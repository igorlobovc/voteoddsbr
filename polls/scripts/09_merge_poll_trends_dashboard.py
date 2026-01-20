import duckdb
from pathlib import Path
import pandas as pd

# === Paths ===
BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "elections_mvp.duckdb"
POLL_TRENDS = BASE_DIR / "polls" / "exports" / "polls_trends.csv"

print(f"📊 Connecting to database: {DB_PATH}")
print(f"📈 Loading poll trends from: {POLL_TRENDS}")

# === Load poll trends CSV ===
df = pd.read_csv(POLL_TRENDS)
print(f"✅ Loaded {len(df)} poll trend records")

# === Connect to DuckDB ===
con = duckdb.connect(DB_PATH)

# === Create table for poll trends (if not exists) ===
con.execute("""
CREATE TABLE IF NOT EXISTS poll_trends (
    institute_norm VARCHAR,
    state_norm VARCHAR,
    candidate_mention VARCHAR,
    week_start DATE,
    polls_count INTEGER,
    avg_file_size_mb DOUBLE,
    avg_3w_count DOUBLE,
    avg_4w_count DOUBLE
);
""")

# === Clear existing data and insert new ===
con.execute("DELETE FROM poll_trends;")
con.register("poll_trends_df", df)
con.execute("INSERT INTO poll_trends SELECT * FROM poll_trends_df;")

print("✅ Inserted poll_trends into DuckDB")

# === Create or replace dashboard view ===
con.execute("""
CREATE OR REPLACE VIEW v_poll_dashboard AS
SELECT 
    t.candidate_mention,
    t.state_norm,
    t.week_start,
    t.polls_count,
    t.avg_3w_count,
    t.avg_4w_count,
    r.total_votes
FROM poll_trends t
LEFT JOIN v_dashboard_summary r
    ON r.state = COALESCE(t.state_norm, 'BR')
ORDER BY t.week_start DESC;
""")

print("✅ View 'v_poll_dashboard' created successfully")

# === Export merged dashboard to CSV ===
EXPORT_PATH = BASE_DIR / "polls" / "exports" / "polls_dashboard.csv"
merged_df = con.execute("SELECT * FROM v_poll_dashboard").fetchdf()
merged_df.to_csv(EXPORT_PATH, index=False)
print(f"📤 Exported → {EXPORT_PATH}")

con.close()
print("🏁 Done — poll trends merged into main dashboard.")