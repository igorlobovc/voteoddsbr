#!/usr/bin/env python3
"""
07_import_from_sitecache_json.py
Bridges legacy site_cache JSON files from polls_pipeline_OLD into DuckDB.
"""

import json
import duckdb
import pathlib
import pandas as pd
from tqdm import tqdm

# --- Paths ---
ROOT = pathlib.Path(__file__).resolve().parents[2]

# Automatically detect legacy folder one level ABOVE the project
ARCHIVE_PARENT = ROOT.parent / "_archive"
LEGACY_DIR = None

for p in ARCHIVE_PARENT.glob("polls_pipeline_OLD_*"):
    if (p / "data" / "site_cache").exists():
        LEGACY_DIR = p / "data" / "site_cache"
        break

if LEGACY_DIR is None:
    raise FileNotFoundError("❌ No valid legacy site_cache found in _archive directory.")

print(f"Using detected LEGACY_DIR: {LEGACY_DIR}")
DB_PATH = ROOT / "data" / "elections_mvp.duckdb"

# --- Connect ---
con = duckdb.connect(str(DB_PATH))
print(f"Connected to {DB_PATH}")

# --- Collect JSON files ---
json_files = sorted(LEGACY_DIR.rglob("*.json"))
print(f"Found {len(json_files)} JSON files under {LEGACY_DIR}")
if not json_files:
    print("⚠️ No JSON files found under legacy site_cache — verify correct path.")

rows = []
for fp in tqdm(json_files, desc="Parsing site_cache"):
    try:
        data = json.loads(fp.read_text(encoding="utf-8"))
        race = data.get("race_id")
        geo = data.get("geo_id")
        total = data.get("total_votes", 0)
        results = data.get("results", [])
        for r in results:
            rows.append({
                "race_id": race,
                "geo_id": geo,
                "candidate": r.get("candidate_name"),
                "party": r.get("party", ""),
                "votes": r.get("votes", 0),
                "pct": r.get("pct", 0.0),
                "path": str(fp.relative_to(LEGACY_DIR))
            })
    except Exception as e:
        print(f"⚠️ Failed to parse {fp}: {e}")

# --- Create DataFrame ---
df = pd.DataFrame(rows)
print(f"Parsed {len(df):,} result rows")

if not df.empty:
    con.execute("""
        CREATE TABLE IF NOT EXISTS staging_sitecache AS SELECT * FROM df LIMIT 0
    """)
    con.register("df", df)
    con.execute("""
        INSERT INTO staging_sitecache
        SELECT * FROM df
    """)
    print("✅ Inserted into DuckDB: staging_sitecache")

# --- Build views ---
con.execute("""
CREATE OR REPLACE VIEW v_dashboard_summary AS
SELECT race_id, geo_id, candidate, party,
       SUM(votes) AS total_votes,
       AVG(pct) AS avg_pct
FROM staging_sitecache
GROUP BY ALL;
""")

con.execute("""
CREATE OR REPLACE VIEW v_reelection_summary AS
SELECT race_id, COUNT(DISTINCT candidate) AS num_candidates,
       SUM(votes) AS total_votes
FROM staging_sitecache
GROUP BY ALL;
""")

con.close()
print("✅ Import completed and views rebuilt.")