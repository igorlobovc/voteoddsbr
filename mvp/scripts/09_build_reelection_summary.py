from __future__ import annotations

import logging
import re
from pathlib import Path

import duckdb


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = REPO_ROOT / "data" / "elections_mvp.duckdb"
LOG_DIR = REPO_ROOT / "mvp" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = LOG_DIR / "09_build_reelection_summary.log"
CSV_OUT = LOG_DIR / "09_reelection_summary.csv"

TABLE_RE = re.compile(r"^staging_raw_(\d{4})$")


def _configure_logging() -> None:
    logging.basicConfig(
        filename=LOG_PATH,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )


def _list_staging_tables(con: duckdb.DuckDBPyConnection) -> list[str]:
    tables = [row[0] for row in con.execute("SHOW TABLES").fetchall()]
    return sorted([name for name in tables if TABLE_RE.match(name)])


def _year_from_table(name: str) -> int:
    match = TABLE_RE.match(name)
    if not match:
        return 0
    return int(match.group(1))


def _build_union_query(table_names: list[str]) -> str:
    parts = []
    for table in table_names:
        year = _year_from_table(table)
        parts.append(
            f"""
            SELECT
              TRIM(CAST(nome AS VARCHAR)) AS candidate_label,
              SUM(
                COALESCE(TRY_CAST(votos AS BIGINT), 0)
              ) AS votos,
              COALESCE(TRY_CAST(ano AS INTEGER), {year}) AS year
            FROM {table}
            WHERE nome IS NOT NULL AND TRIM(nome) <> ''
            GROUP BY nome, ano
            """
        )
    return "\nUNION ALL\n".join(part.strip() for part in parts)


def _create_or_replace_view(con: duckdb.DuckDBPyConnection, table_names: list[str]) -> None:
    if not table_names:
        empty_view_sql = """
        CREATE OR REPLACE VIEW v_reelection_summary AS
        SELECT
          CAST(NULL AS VARCHAR) AS candidate_label,
          CAST(0 AS BIGINT) AS total_votes,
          CAST(0 AS BIGINT) AS num_years,
          CAST('' AS VARCHAR) AS years_list,
          CAST(FALSE AS BOOLEAN) AS possible_reelection
        WHERE FALSE
        """
        con.execute(empty_view_sql)
        return

    print(f"✅ Creating or replacing view from {len(table_names)} staging tables.")
    union_sql = _build_union_query(table_names)
    view_sql = f"""
    CREATE OR REPLACE VIEW v_reelection_summary AS
    WITH all_rows AS (
      {union_sql}
    )
    SELECT
      candidate_label,
      SUM(votos) AS total_votes,
      COUNT(DISTINCT year) AS num_years,
      STRING_AGG(DISTINCT CAST(year AS VARCHAR), ',' ) AS years_list,
      COUNT(DISTINCT year) > 1 AS possible_reelection
    FROM all_rows
    GROUP BY candidate_label
    """
    con.execute(view_sql)


def main() -> None:
    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    _configure_logging()
    logging.info("Starting reelection summary build.")
    logging.info("Connecting to DuckDB: %s", DB_PATH)
    print(f"🔍 Using database: {DB_PATH}")

    con = duckdb.connect(str(DB_PATH))
    try:
        table_names = _list_staging_tables(con)
        logging.info("Found staging tables: %s", table_names)
        logging.info("Number of staging tables found: %d", len(table_names))
        if not table_names:
            print("⚠️ No staging_raw_* tables found. Creating empty view.")

        logging.info("Creating or replacing v_reelection_summary view.")
        _create_or_replace_view(con, table_names)

        logging.info("Exporting v_reelection_summary to CSV: %s", CSV_OUT)
        con.execute(
            f"COPY (SELECT * FROM v_reelection_summary ORDER BY num_years DESC, total_votes DESC) "
            f"TO '{CSV_OUT}' (HEADER, DELIMITER ',')"
        )

        print("Top 10 reelection candidates:")
        top_rows = con.execute(
            """
            SELECT candidate_label, total_votes, num_years, years_list
            FROM v_reelection_summary
            ORDER BY num_years DESC, total_votes DESC
            LIMIT 10
            """
        ).fetchall()
        for row in top_rows:
            print(f"- {row[0]} | total_votes={row[1]} | num_years={row[2]} | years={row[3]}")

        logging.info("Summary build completed successfully.")
    finally:
        con.close()
        logging.info("DuckDB connection closed.")


if __name__ == "__main__":
    main()
