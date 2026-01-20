

import os
import csv
import pdfplumber
from pathlib import Path
from tqdm import tqdm
from datetime import datetime

# === Paths ===
BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = BASE_DIR / "data" / "raw"
EXPORT_DIR = BASE_DIR / "polls" / "exports"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

OUTFILE = EXPORT_DIR / "polls_raw_index.csv"

# === Collect PDFs ===
pdf_files = sorted(RAW_DIR.rglob("*.pdf"))
print(f"📂 Found {len(pdf_files)} PDF files under {RAW_DIR}")

rows = []
for pdf_path in tqdm(pdf_files, desc="Extracting metadata"):
    stat = pdf_path.stat()
    file_size_mb = round(stat.st_size / (1024 * 1024), 2)
    modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    meta_text = ""

    try:
        with pdfplumber.open(pdf_path) as pdf:
            if pdf.pages:
                first_text = pdf.pages[0].extract_text() or ""
                meta_text = " ".join(first_text.split()[:50])
    except Exception as e:
        meta_text = f"Error reading: {e}"

    rows.append({
        "file_name": pdf_path.name,
        "file_size_mb": file_size_mb,
        "modified": modified,
        "sample_text": meta_text
    })

# === Export CSV ===
with open(OUTFILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["file_name", "file_size_mb", "modified", "sample_text"])
    writer.writeheader()
    writer.writerows(rows)

print(f"✅ Exported → {OUTFILE}")
print(f"Total indexed PDFs: {len(rows)}")