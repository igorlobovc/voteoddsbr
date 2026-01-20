#!/usr/bin/env python3
"""
01_ingest_polls.py
Ingest polling data (e.g., Datafolha, IPEC) from CSV/JSON into DuckDB for analysis.
Part of the 'polls' module in voteoddsbr.
"""

import duckdb
import pandas as pd
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "polls" / "data"
EXPORTS_DIR = BASE_DIR / "polls" / "exports"
DB_PATH = BASE_DIR / "data" / "elections_mvp.duckdb"

DATA_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

print(f"{datetime.now().isoformat()} 🚀 Starting Polls Ingestion")

# Load any CSV or JSON polls in polls/data
poll_files = list(DATA_DIR.glob("*.csv")) + list(DATA_DIR.glob("*.json"))
if not poll_files:
    print("⚠️ No polls found in polls/data/. Please drop files before running.")
    exit()

frames = []
for f in poll_files:
    print(f"📥 Reading {f.name}")
    if f.suffix == ".csv":
        df = pd.read_csv(f)
    elif f.suffix == ".json":
        df = pd.read_json(f)
    else:
        continue
    df["source_file"] = f.name
    frames.append(df)

polls_df = pd.concat(frames, ignore_index=True)
print(f"✅ Loaded {len(polls_df)} total rows from {len(poll_files)} files.")

# Connect to DuckDB
con = duckdb.connect(str(DB_PATH))
table_name = "polls_raw"

# Create or append data
con.execute(f"""
CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM polls_df LIMIT 0;
""")

con.register("polls_df", polls_df)
con.execute(f"INSERT INTO {table_name} SELECT * FROM polls_df;")
con.unregister("polls_df")

con.close()

# Export snapshot
snapshot_path = EXPORTS_DIR / f"polls_raw_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
polls_df.to_csv(snapshot_path, index=False)

print(f"💾 Saved snapshot → {snapshot_path}")
print(f"🏁 Done ingesting polls at {datetime.now().isoformat()}")
