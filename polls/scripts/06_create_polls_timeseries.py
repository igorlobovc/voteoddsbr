import duckdb
import pandas as pd
from pathlib import Path

# === Paths ===
BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "elections_mvp.duckdb"
EXPORT_DIR = BASE_DIR / "polls" / "exports"
EXPORT_FILE = EXPORT_DIR / "polls_timeseries.csv"

print(f"📊 Connecting to database: {DB_PATH}")
con = duckdb.connect(str(DB_PATH))

# Check if table exists
tables = [t[0] for t in con.execute("SHOW TABLES").fetchall()]
if "polls_normalized" not in tables:
    raise SystemExit("❌ polls_normalized table not found in database.")

print("📅 Creating weekly poll time series...")
query = """
CREATE OR REPLACE TABLE polls_timeseries AS
SELECT
    institute_norm,
    state_norm,
    candidate_mention,
    date_trunc('week', poll_date_norm) AS week_start,
    COUNT(*) AS polls_count,
    AVG(file_size_mb) AS avg_file_size_mb
FROM polls_normalized
WHERE poll_date_norm IS NOT NULL
GROUP BY 1, 2, 3, 4
ORDER BY week_start;
"""

con.execute(query)

# Export to CSV
df = con.execute("SELECT * FROM polls_timeseries").fetchdf()
df.to_csv(EXPORT_FILE, index=False)
print(f"✅ Poll time series exported → {EXPORT_FILE}")
print(df.head())

con.close()
