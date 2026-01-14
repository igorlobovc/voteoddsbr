from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from datetime import datetime
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Iterator
from urllib.parse import urlencode
from urllib.request import Request, urlopen

CKAN_BASE = "https://dadosabertos.tse.jus.br"
CKAN_API = f"{CKAN_BASE}/api/3/action/package_search"
CKAN_SHOW_API = f"{CKAN_BASE}/api/3/action/package_show"

RESULTADOS_TITLE_RE = re.compile(r"^Resultados\s*-\s*(20\d{2})\b", re.IGNORECASE)
RESULTADOS_NAME_RE = re.compile(r"^resultados[-_ ]*(20\d{2})\b", re.IGNORECASE)

DEFAULT_RESOURCE_KEYWORDS = [
    "votacao_candidato_munzona",
    "votacao candidato munzona",
    "votacao nominal por municipio e zona",
]


class CKANError(RuntimeError):
    pass


@dataclass(frozen=True)
class FailureEntry:
    stage: str
    message: str
    dataset_name: str | None = None
    url: str | None = None


class FailureLog:
    def __init__(self) -> None:
        self.entries: list[FailureEntry] = []

    def add(self, stage: str, message: str, dataset_name: str | None = None, url: str | None = None) -> None:
        self.entries.append(
            FailureEntry(stage=stage, message=message, dataset_name=dataset_name, url=url)
        )

    def summary_by_stage(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for entry in self.entries:
            counts[entry.stage] = counts.get(entry.stage, 0) + 1
        return counts

    def write_json(self, path: Path) -> None:
        payload = {
            "generated_at": datetime.now().isoformat(),
            "entries": [asdict(entry) for entry in self.entries],
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


@dataclass
class Stats:
    packages_seen: int = 0
    resultados_datasets: int = 0
    resources_seen: int = 0
    resources_matched: int = 0


@dataclass(frozen=True)
class ResultadosDataset:
    year: int
    title: str
    name: str
    url: str
    metadata_modified: str | None


@dataclass(frozen=True)
class ResourceMatch:
    year: int
    dataset_title: str
    dataset_name: str
    dataset_url: str
    resource_id: str
    resource_name: str
    resource_url: str
    resource_format: str | None
    resource_description: str | None
    resource_last_modified: str | None
    resource_size: int | None


def _request_json(url: str, timeout: float = 30.0) -> dict:
    req = Request(url, headers={"User-Agent": "polls-pipeline/ckan-search"})
    try:
        with urlopen(req, timeout=timeout) as resp:
            payload = resp.read().decode("utf-8")
    except Exception as exc:
        raise CKANError(f"Failed to request CKAN API: {exc}") from exc

    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        raise CKANError("Invalid JSON response from CKAN API") from exc


def package_search(query: str, rows: int = 100, start: int = 0, fq: str | None = None) -> dict:
    params = {"q": query, "rows": rows, "start": start}
    if fq:
        params["fq"] = fq
    url = f"{CKAN_API}?{urlencode(params)}"
    payload = _request_json(url)
    if not payload.get("success"):
        raise CKANError(f"CKAN API reported failure: {payload}")
    return payload["result"]


def package_show(name: str) -> dict:
    url = f"{CKAN_SHOW_API}?{urlencode({'id': name})}"
    payload = _request_json(url)
    if not payload.get("success"):
        raise CKANError(f"CKAN API reported failure: {payload}")
    return payload["result"]


def iter_packages(
    query: str,
    rows: int = 100,
    fq: str | None = None,
    max_pages: int | None = None,
    failure_log: FailureLog | None = None,
) -> Iterator[dict]:
    start = 0
    page = 0
    while True:
        try:
            result = package_search(query=query, rows=rows, start=start, fq=fq)
        except CKANError as exc:
            if failure_log:
                failure_log.add(stage="package_search", message=str(exc), url=CKAN_API)
            raise
        packages = result.get("results", [])
        for pkg in packages:
            yield pkg
        start += len(packages)
        page += 1
        if start >= result.get("count", 0) or not packages:
            break
        if max_pages is not None and page >= max_pages:
            break


def extract_resultados_year(pkg: dict) -> int | None:
    title = (pkg.get("title") or "").strip()
    name = (pkg.get("name") or "").strip()
    for regex, value in ((RESULTADOS_TITLE_RE, title), (RESULTADOS_NAME_RE, name)):
        match = regex.search(value)
        if match:
            return int(match.group(1))
    return None


def find_resultados_datasets(
    years: Iterable[int] | None = None,
    query: str = "Resultados",
    rows: int = 100,
    max_pages: int | None = None,
    stats: Stats | None = None,
    failure_log: FailureLog | None = None,
) -> list[ResultadosDataset]:
    years_set = set(years) if years else None
    matches: list[ResultadosDataset] = []
    for pkg in iter_packages(query=query, rows=rows, max_pages=max_pages, failure_log=failure_log):
        if stats:
            stats.packages_seen += 1
        year = extract_resultados_year(pkg)
        if year is None:
            continue
        if years_set and year not in years_set:
            continue
        if stats:
            stats.resultados_datasets += 1
        title = (pkg.get("title") or "").strip()
        name = (pkg.get("name") or "").strip()
        url = f"{CKAN_BASE}/dataset/{name}" if name else CKAN_BASE
        matches.append(
            ResultadosDataset(
                year=year,
                title=title or name,
                name=name,
                url=url,
                metadata_modified=pkg.get("metadata_modified"),
            )
        )
    return matches


def _normalize_text(value: str) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKD", value)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = normalized.lower()
    cleaned = []
    for ch in normalized:
        if ch.isalnum() or ch == "_":
            cleaned.append(ch)
        else:
            cleaned.append(" ")
    return " ".join("".join(cleaned).split())


def _resource_haystack(resource: dict) -> str:
    parts = [
        resource.get("name"),
        resource.get("description"),
        resource.get("format"),
        resource.get("url"),
    ]
    return _normalize_text(" ".join([p for p in parts if p]))


def _matches_keywords(haystack: str, keywords: Iterable[str]) -> bool:
    for keyword in keywords:
        if keyword and keyword in haystack:
            return True
    return False


def _get_resources(
    pkg: dict,
    fetch_full: bool = True,
    failure_log: FailureLog | None = None,
) -> list[dict]:
    resources = pkg.get("resources") or []
    if not fetch_full:
        return resources
    name = (pkg.get("name") or "").strip()
    if not name:
        return resources
    needs_full = not resources or any("size" not in r for r in resources)
    if not needs_full:
        return resources
    try:
        full_pkg = package_show(name)
    except CKANError as exc:
        if failure_log:
            failure_log.add(stage="package_show", message=str(exc), dataset_name=name, url=CKAN_SHOW_API)
        return resources
    return full_pkg.get("resources") or []


def find_resultados_resources(
    years: Iterable[int] | None = None,
    query: str = "Resultados",
    rows: int = 100,
    max_pages: int | None = None,
    resource_keywords: Iterable[str] | None = None,
    stats: Stats | None = None,
    failure_log: FailureLog | None = None,
) -> list[ResourceMatch]:
    years_set = set(years) if years else None
    keywords = resource_keywords or DEFAULT_RESOURCE_KEYWORDS
    normalized_keywords = [_normalize_text(k) for k in keywords if k]
    matches: list[ResourceMatch] = []

    for pkg in iter_packages(query=query, rows=rows, max_pages=max_pages, failure_log=failure_log):
        if stats:
            stats.packages_seen += 1
        year = extract_resultados_year(pkg)
        if year is None:
            continue
        if years_set and year not in years_set:
            continue
        if stats:
            stats.resultados_datasets += 1
        title = (pkg.get("title") or "").strip()
        name = (pkg.get("name") or "").strip()
        dataset_url = f"{CKAN_BASE}/dataset/{name}" if name else CKAN_BASE
        resources = _get_resources(pkg, failure_log=failure_log)
        for resource in resources:
            if stats:
                stats.resources_seen += 1
            haystack = _resource_haystack(resource)
            if not _matches_keywords(haystack, normalized_keywords):
                continue
            if stats:
                stats.resources_matched += 1
            matches.append(
                ResourceMatch(
                    year=year,
                    dataset_title=title or name,
                    dataset_name=name,
                    dataset_url=dataset_url,
                    resource_id=str(resource.get("id") or ""),
                    resource_name=str(resource.get("name") or resource.get("title") or ""),
                    resource_url=str(resource.get("url") or ""),
                    resource_format=resource.get("format"),
                    resource_description=resource.get("description"),
                    resource_last_modified=resource.get("last_modified"),
                    resource_size=resource.get("size"),
                )
            )

    return matches


def _parse_years(value: str) -> set[int] | None:
    if not value:
        return None
    years: set[int] = set()
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        years.add(int(part))
    return years or None


def _parse_keywords(value: str) -> list[str]:
    if not value:
        return DEFAULT_RESOURCE_KEYWORDS
    items: list[str] = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        items.append(part)
    return items or DEFAULT_RESOURCE_KEYWORDS


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Search CKAN datasets for titles like 'Resultados - 2022'."
    )
    parser.add_argument("--years", default="", help="Comma-separated years, e.g. 2018,2022")
    parser.add_argument("--query", default="Resultados", help="CKAN search query")
    parser.add_argument("--rows", type=int, default=100, help="Rows per CKAN page")
    parser.add_argument("--max-pages", type=int, default=10, help="Max pages to fetch (0=all)")
    parser.add_argument("--resources", action="store_true", help="Output matching resources")
    parser.add_argument(
        "--resource-keywords",
        default="",
        help="Comma-separated resource match strings (defaults to known votacao keys)",
    )
    parser.add_argument(
        "--failures-log",
        default="mvp/manifests/ckan_failures.json",
        help="Path to write failure log (empty to disable)",
    )
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args(argv)

    years = _parse_years(args.years)
    max_pages = None if args.max_pages <= 0 else args.max_pages
    resource_keywords = _parse_keywords(args.resource_keywords)
    failure_log = FailureLog()
    stats = Stats()
    exit_code = 0

    try:
        if args.resources:
            results = find_resultados_resources(
                years=years,
                query=args.query,
                rows=args.rows,
                max_pages=max_pages,
                resource_keywords=resource_keywords,
                stats=stats,
                failure_log=failure_log,
            )
        else:
            results = find_resultados_datasets(
                years=years,
                query=args.query,
                rows=args.rows,
                max_pages=max_pages,
                stats=stats,
                failure_log=failure_log,
            )
    except CKANError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        results = []
        exit_code = 1

    if args.resources:
        results.sort(key=lambda item: (item.year, item.dataset_title or ""), reverse=True)
    else:
        results.sort(key=lambda item: (item.year, item.title or ""), reverse=True)

    if args.json:
        print(
            json.dumps(
                [r.__dict__ for r in results],
                indent=2,
                ensure_ascii=False,
            )
        )
    else:
        if not results:
            print("No matching datasets found.")
        else:
            for item in results:
                if args.resources:
                    fmt = f" ({item.resource_format})" if item.resource_format else ""
                    print(
                        f"{item.year} | {item.dataset_title} | {item.resource_name} | {item.resource_url}{fmt}"
                    )
                else:
                    modified = (
                        f" (modified {item.metadata_modified})" if item.metadata_modified else ""
                    )
                    print(f"{item.year} | {item.title} | {item.url}{modified}")

    if args.failures_log and failure_log.entries:
        failure_log.write_json(Path(args.failures_log))

    summary_stream = sys.stderr if args.json else sys.stdout
    _print_summary(stats, failure_log, stream=summary_stream)

    return exit_code


def _print_summary(stats: Stats, failure_log: FailureLog, stream: object = sys.stdout) -> None:
    rows = [
        ("packages_seen", stats.packages_seen),
        ("resultados_datasets", stats.resultados_datasets),
        ("resources_seen", stats.resources_seen),
        ("resources_matched", stats.resources_matched),
        ("failures", len(failure_log.entries)),
    ]
    width = max(len(label) for label, _ in rows)
    print("\nSummary", file=stream)
    for label, value in rows:
        print(f"{label.ljust(width)} : {value}", file=stream)

    failures_by_stage = failure_log.summary_by_stage()
    if failures_by_stage:
        stage_summary = ", ".join(
            f"{stage}={count}" for stage, count in sorted(failures_by_stage.items())
        )
        print(f"{'failures_by_stage'.ljust(width)} : {stage_summary}", file=stream)


if __name__ == "__main__":
    raise SystemExit(main())
