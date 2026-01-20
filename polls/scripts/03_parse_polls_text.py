import csv
import re
from pathlib import Path
import pandas as pd
from tqdm import tqdm

BASE_DIR = Path(__file__).resolve().parents[2]
EXPORT_DIR = BASE_DIR / "polls" / "exports"
RAW_INDEX = EXPORT_DIR / "polls_raw_index.csv"
STRUCTURED_OUT = EXPORT_DIR / "polls_structured.csv"

print(f"📖 Loading: {RAW_INDEX}")
df = pd.read_csv(RAW_INDEX)

patterns = {
    "institute": re.compile(r"(?i)(IPEC|Quaest|Datafolha|Paraná\s+Pesquisas|Atlas|CNT|FSB|Real\s+Time\s+Big\s+Data|PoderData|IPEP|Modalmais|Genial|XP|BTG)"),
    "date": re.compile(r"(\d{1,2}\s*(de)?\s*[A-Za-zçÇãÃéÉíÍóÓôÔúÚ]+\s*(de)?\s*\d{4})"),  # e.g. 'Março de 2025'
    "state": re.compile(r"(?i)\b(AC|AL|AP|AM|BA|CE|DF|ES|GO|MA|MT|MS|MG|PA|PB|PR|PE|PI|RJ|RN|RS|RO|RR|SC|SP|SE|TO)\b"),
    "round": re.compile(r"(?i)\bT([12])\b"),
    "candidate": re.compile(r"(?i)(LULA|BOLSONARO|RAQUEL|MARÍLIA|CIRO|SIMONE|TEBET|ARMANDO|DANIEL|ANDERSON|GILSON)")
}

def extract_metadata(text: str) -> dict:
    result = {}
    for key, pattern in patterns.items():
        match = pattern.search(text)
        result[key] = match.group(0) if match else None
    return result

records = []
print("🔍 Parsing text for structured metadata...")
for _, row in tqdm(df.iterrows(), total=len(df)):
    meta = extract_metadata(str(row.get("sample_text", "")))
    record = {
        "file_name": row["file_name"],
        "file_size_mb": row["file_size_mb"],
        "modified": row["modified"],
        "institute": meta["institute"],
        "poll_date": meta["date"],
        "state": meta["state"],
        "round": meta["round"],
        "candidate_mention": meta["candidate"]
    }
    records.append(record)

structured_df = pd.DataFrame(records)
structured_df.to_csv(STRUCTURED_OUT, index=False)
print(f"✅ Structured metadata saved → {STRUCTURED_OUT}")
print(structured_df.head(10))