

import duckdb
import pandas as pd
from pathlib import Path

# === Paths ===
BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "elections_mvp.duckdb"
EXPORT_DIR = BASE_DIR / "polls" / "exports"
EXPORT_FILE = EXPORT_DIR / "polls_trends.csv"

print(f"📈 Connecting to database: {DB_PATH}")
con = duckdb.connect(str(DB_PATH))

# Check if table exists
tables = [t[0] for t in con.execute("SHOW TABLES").fetchall()]
if "polls_timeseries" not in tables:
    raise SystemExit("❌ polls_timeseries table not found. Run 06_create_polls_timeseries.py first.")

print("🔁 Generating rolling averages (7d, 14d, 30d)...")

query = """
CREATE OR REPLACE TABLE polls_trends AS
SELECT
    institute_norm,
    state_norm,
    candidate_mention,
    week_start,
    polls_count,
    avg_file_size_mb,
    AVG(polls_count) OVER (
        PARTITION BY candidate_mention
        ORDER BY week_start
        ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING
    ) AS avg_3w_count,
    AVG(polls_count) OVER (
        PARTITION BY candidate_mention
        ORDER BY week_start
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS avg_4w_count
FROM polls_timeseries
ORDER BY candidate_mention, week_start;
"""

con.execute(query)

# Export to CSV
df = con.execute("SELECT * FROM polls_trends").fetchdf()
df.to_csv(EXPORT_FILE, index=False)
print(f"✅ Poll trends exported → {EXPORT_FILE}")
print(df.head())

con.close()