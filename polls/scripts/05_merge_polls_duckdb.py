

import duckdb
from pathlib import Path
import pandas as pd

# === Paths ===
BASE_DIR = Path(__file__).resolve().parents[2]
EXPORT_DIR = BASE_DIR / "polls" / "exports"
DB_PATH = BASE_DIR / "data" / "elections_mvp.duckdb"
NORMALIZED_CSV = EXPORT_DIR / "polls_normalized.csv"

# === Load normalized polls ===
print(f"📘 Loading normalized polls from {NORMALIZED_CSV}")
df = pd.read_csv(NORMALIZED_CSV)
print(f"✅ Loaded {len(df)} records")

# === Connect to DuckDB ===
print(f"🦆 Connecting to database → {DB_PATH}")
con = duckdb.connect(str(DB_PATH))

# === Create table if not exists ===
con.execute("""
CREATE TABLE IF NOT EXISTS polls_normalized (
    file_name VARCHAR,
    institute_norm VARCHAR,
    poll_date_norm DATE,
    state_norm VARCHAR,
    round VARCHAR,
    candidate_mention VARCHAR,
    file_size_mb DOUBLE
)
""")

# === Insert data ===
con.execute("DELETE FROM polls_normalized")
con.register("df_view", df)
con.execute("""
INSERT INTO polls_normalized
SELECT
    file_name,
    institute_norm,
    TRY_CAST(poll_date_norm AS DATE),
    state_norm,
    round,
    candidate_mention,
    file_size_mb
FROM df_view
""")
print(f"✅ Inserted {len(df)} normalized polls into DuckDB")

# === Preview ===
preview = con.execute("SELECT * FROM polls_normalized LIMIT 10").fetchdf()
print(preview)

con.close()
print(f"💾 polls_normalized table updated in {DB_PATH}")