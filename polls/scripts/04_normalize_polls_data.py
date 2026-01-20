import pandas as pd
from pathlib import Path
import re

# === Paths ===
BASE_DIR = Path(__file__).resolve().parents[2]
EXPORT_DIR = BASE_DIR / "polls" / "exports"
STRUCTURED_IN = EXPORT_DIR / "polls_structured.csv"
NORMALIZED_OUT = EXPORT_DIR / "polls_normalized.csv"

print(f"📘 Loading structured polls: {STRUCTURED_IN}")
df = pd.read_csv(STRUCTURED_IN)

# === Helper normalization functions ===

def normalize_date(text: str) -> str:
    """Convert '25 de fevereiro de 2025' -> '2025-02-25'"""
    if pd.isna(text) or not isinstance(text, str):
        return None
    months = {
        "janeiro": "01", "fevereiro": "02", "março": "03", "abril": "04",
        "maio": "05", "junho": "06", "julho": "07", "agosto": "08",
        "setembro": "09", "outubro": "10", "novembro": "11", "dezembro": "12"
    }
    m = re.search(r"(\d{1,2})\s*de\s*([a-zç]+)\s*de\s*(\d{4})", text.lower())
    if m:
        day, month_text, year = m.groups()
        month = months.get(month_text, "01")
        return f"{year}-{month}-{int(day):02d}"
    return None

def normalize_institute(text: str) -> str:
    """Standardize institute names"""
    if pd.isna(text): return None
    text = text.strip().upper()
    aliases = {
        "PARANÁ PESQUISAS": "PARANA PESQUISAS",
        "REAL TIME BIG DATA": "REALTIME BIGDATA",
        "PODERDATA": "PODERDATA",
        "ATLAS": "ATLAS INTEL",
        "DATAFOLHA": "DATAFOLHA",
        "IPEP": "IPEP",
        "IPEC": "IPEC"
    }
    for k, v in aliases.items():
        if k in text:
            return v
    return text

def normalize_state(text: str) -> str:
    """Ensure valid Brazilian state abbreviation"""
    valid_states = {
        "AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG","PA","PB","PR",
        "PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"
    }
    if pd.isna(text): return None
    text = text.strip().upper()
    if text in valid_states:
        return text
    return None

# === Apply normalization ===
print("⚙️ Normalizing columns...")

df["poll_date_norm"] = df["poll_date"].apply(normalize_date)
df["institute_norm"] = df["institute"].apply(normalize_institute)
df["state_norm"] = df["state"].apply(normalize_state)

# === Drop duplicates and reorder ===
df_norm = df.drop_duplicates(subset=["file_name"]).copy()
cols = [
    "file_name","institute_norm","poll_date_norm","state_norm",
    "round","candidate_mention","file_size_mb"
]
df_norm = df_norm[cols]

# === Export normalized data ===
df_norm.to_csv(NORMALIZED_OUT, index=False)
print(f"✅ Normalized poll data exported → {NORMALIZED_OUT}")
print(df_norm.head(10))
