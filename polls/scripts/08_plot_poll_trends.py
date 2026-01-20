

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# === Paths ===
BASE_DIR = Path(__file__).resolve().parents[2]
EXPORT_DIR = BASE_DIR / "polls" / "exports"
INPUT_FILE = EXPORT_DIR / "polls_trends.csv"
PLOTS_DIR = EXPORT_DIR / "plots"
PLOTS_DIR.mkdir(exist_ok=True)

print(f"📊 Reading: {INPUT_FILE}")
df = pd.read_csv(INPUT_FILE)

if df.empty:
    raise SystemExit("❌ polls_trends.csv is empty. Run 07_generate_poll_trends.py first.")

# Normalize date column
df["week_start"] = pd.to_datetime(df["week_start"], errors="coerce")

# Summary info
print("✅ Loaded records:", len(df))
print("🧾 Candidates:", df["candidate_mention"].dropna().unique())

# === Plot per candidate ===
for candidate, g in df.groupby("candidate_mention"):
    if candidate is None or pd.isna(candidate):
        continue
    plt.figure(figsize=(10, 6))
    plt.plot(g["week_start"], g["polls_count"], label="Poll Count", marker="o")
    plt.plot(g["week_start"], g["avg_3w_count"], label="3-Week Avg", linestyle="--")
    plt.plot(g["week_start"], g["avg_4w_count"], label="4-Week Avg", linestyle=":")
    plt.title(f"Poll Trend for {candidate}")
    plt.xlabel("Week Start")
    plt.ylabel("Poll Count")
    plt.legend()
    plt.grid(True, alpha=0.3)
    out_path = PLOTS_DIR / f"{candidate}_trend.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"📈 Saved {out_path}")

# === Combined plot ===
plt.figure(figsize=(10, 6))
for candidate, g in df.groupby("candidate_mention"):
    if candidate is None or pd.isna(candidate):
        continue
    plt.plot(g["week_start"], g["polls_count"], label=candidate)
plt.title("Poll Count Trends (All Candidates)")
plt.xlabel("Week Start")
plt.ylabel("Poll Count")
plt.legend()
plt.grid(True, alpha=0.3)
combined_path = PLOTS_DIR / "all_candidates_trend.png"
plt.tight_layout()
plt.savefig(combined_path, dpi=150)
plt.close()
print(f"✅ Combined plot saved → {combined_path}")