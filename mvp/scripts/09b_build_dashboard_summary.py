from __future__ import annotations
import duckdb
from pathlib import Path
from datetime import datetime

# Adjusted root resolution for voteoddsbr repository layout
REPO_ROOT = Path(__file__).resolve().parents[2]  # polls_pipeline/mvp/scripts → go up two
DB_PATH = REPO_ROOT / "data" / "elections_mvp.duckdb"
SQL_PATH = REPO_ROOT / "mvp" / "sql" / "v_dashboard_summary.sql"
EXPORT_PATH = REPO_ROOT / "mvp" / "exports" / "dashboard_summary.csv"

def main() -> int:
    timestamp = datetime.now().isoformat(timespec="seconds")
    print(f"{timestamp} 🚀 Building v_dashboard_summary from {DB_PATH}")

    if not DB_PATH.exists():
        raise FileNotFoundError(f"❌ DuckDB file not found: {DB_PATH}")
    if not SQL_PATH.exists():
        raise FileNotFoundError(f"❌ SQL definition file not found: {SQL_PATH}")

    con = duckdb.connect(str(DB_PATH))
    try:
        # DuckDB 1.1+ no longer accepts "PRAGMA threads=ALL"; replaced by SET threads TO n
        con.execute("SET threads TO 4;")  # DuckDB 1.1+ syntax
        sql = SQL_PATH.read_text(encoding="utf-8")
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