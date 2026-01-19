from __future__ import annotations
import duckdb
from pathlib import Path
from datetime import datetime

# Adjusted root resolution for voteoddsbr repository layout
REPO_ROOT = Path(__file__).resolve().parents[2]  # polls_pipeline/mvp/scripts → go up two
DB_PATH = REPO_ROOT / "data" / "elections_mvp.duckdb"
SQL_PATH = REPO_ROOT / "mvp" / "sql" / "v_dashboard_summary.sql"
ARCHIVE_SQL_PATH = REPO_ROOT / "_archive" / "sql" / "v_dashboard_summary.sql"
EXPORT_PATH = REPO_ROOT / "mvp" / "exports" / "dashboard_summary.csv"

def main() -> int:
    timestamp = datetime.now().isoformat(timespec="seconds")
    print(f"{timestamp} 🚀 Building v_dashboard_summary from {DB_PATH}")

    if not DB_PATH.exists():
        raise FileNotFoundError(f"❌ DuckDB file not found: {DB_PATH}")

    if SQL_PATH.exists():
        sql_file_path = SQL_PATH
    elif ARCHIVE_SQL_PATH.exists():
        sql_file_path = ARCHIVE_SQL_PATH
    else:
        raise FileNotFoundError(f"❌ SQL definition file not found in either {SQL_PATH} or {ARCHIVE_SQL_PATH}")

    con = duckdb.connect(str(DB_PATH))
    try:
        # DuckDB 1.1+ no longer accepts "PRAGMA threads=ALL"; replaced by SET threads TO n
        con.execute("SET threads TO 4;")  # DuckDB 1.1+ syntax
        sql = sql_file_path.read_text(encoding="utf-8")
        sql = sql.replace("candidate_label", "candidate")
        con.execute(sql)
        con.execute(
            f"COPY (SELECT * FROM v_dashboard_summary) "
            f"TO '{EXPORT_PATH}' (HEADER, DELIMITER ',');"
        )
        print(f"{datetime.now().isoformat(timespec='seconds')} ✅ Exported dashboard_summary.csv → {EXPORT_PATH}")
        return 0
    finally:
        con.close()

if __name__ == "__main__":
    raise SystemExit(main())