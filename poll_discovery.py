"""
Discover new poll files from public sources and queue them for download.

• FiveThirtyEight – JSON feeds (poll‐level URLs)
• Abrapel – HTML page with PDF links
Results are stored/merged in SQLite: polls.db → table poll_queue
"""

from __future__ import annotations
import json
import sqlite3
import time
from pathlib import Path
from typing import Iterable, List, Tuple

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel

# ---------- constants --------------------------------------------------------

REPO_ROOT = Path("/Users/igorcunha/SHRKVSCODE/polls_pipeline")  # hard path per Shrk
DB_FILE    = REPO_ROOT / "polls.db"

FTE_JSON_FEEDS = [
    "https://projects.fivethirtyeight.com/polls-page/president_primary_polls.json",
    "https://projects.fivethirtyeight.com/polls-page/president_polls.json",
]

ABRAPEL_LIST_URL = "https://www.abrapel.org.br/pesquisas-eleitorais-2025"

POLL_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS poll_queue (
    url         TEXT PRIMARY KEY,
    source      TEXT NOT NULL,
    added_ts    INTEGER NOT NULL,
    downloaded  INTEGER DEFAULT 0   -- 0 = pending, 1 = downloaded
);
"""

# ---------- data model -------------------------------------------------------


class PollLink(BaseModel):
    url: str
    source: str  # "538" or "abrapel"


# ---------- helpers ----------------------------------------------------------


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute(POLL_TABLE_DDL)
    return conn


def _insert_new(conn: sqlite3.Connection, rows: Iterable[PollLink]) -> int:
    cur = conn.cursor()
    added = 0
    for row in rows:
        try:
            cur.execute(
                "INSERT OR IGNORE INTO poll_queue (url, source, added_ts) "
                "VALUES (?, ?, ?)",
                (row.url, row.source, int(time.time())),
            )
            if cur.rowcount:
                added += 1
        except sqlite3.Error as e:
            print(f"[WARN] DB error on {row.url}: {e}")
    conn.commit()
    return added


# ---------- scrapers ---------------------------------------------------------


def scrape_fte() -> List[PollLink]:
    links: list[PollLink] = []
    for feed_url in FTE_JSON_FEEDS:
        print(f"[FTE] Fetching {feed_url}")
        try:
            data = requests.get(feed_url, timeout=30).json()
        except Exception as exc:  # JSONDecodeError or network issues
            print(f"[FTE] failed: {exc}")
            continue

        # each entry is a poll dict with a 'url' key
        for entry in data:
            if (u := entry.get("url")):
                links.append(PollLink(url=u, source="538"))
    print(f"[FTE] collected {len(links)} links")
    return links


def scrape_abrapel() -> List[PollLink]:
    print(f"[ABRAPEL] Fetching {ABRAPEL_LIST_URL}")
    try:
        html = requests.get(ABRAPEL_LIST_URL, timeout=30).text
    except Exception as exc:
        print(f"[ABRAPEL] failed: {exc}")
        return []

    soup = BeautifulSoup(html, "lxml")
    pdf_links = {
        a["href"]
        for a in soup.select("a[href$='.pdf'], a[href$='.PDF']")
        if a["href"].startswith("http")
    }
    print(f"[ABRAPEL] collected {len(pdf_links)} links")
    return [PollLink(url=u, source="abrapel") for u in pdf_links]


def discover() -> None:
    """Run both scrapers, store unseen rows, print summary."""
    conn = _connect()
    new_total = 0
    for scraper in (scrape_fte, scrape_abrapel):
        new_total += _insert_new(conn, scraper())
    print(f"[DISCOVERY] {new_total} new links queued.")


# ---------- CLI --------------------------------------------------------------


if __name__ == "__main__":
    discover()