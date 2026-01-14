"""
08_import_tse_multi_year.py

This script imports and harmonizes TSE CSV datasets for multiple election years (2006–2018).
It processes voting and candidate data, normalizes columns, and loads them into DuckDB tables,
updating shared dimension tables for parties and candidates.
"""

import duckdb
import pandas as pd
from pathlib import Path
from datetime import datetime
import os
import logging
import zipfile
from unidecode import unidecode
import gc
# For automatic data acquisition from TSE CKAN
import requests

def safe_read_csv(path):
    """
    Helper to read CSVs with robust error handling for malformed files.
    Returns empty DataFrame on failure and prints a warning.
    """
    try:
        df = pd.read_csv(
            path,
            encoding="latin1",
            sep=";",
            on_bad_lines="skip",
            skip_blank_lines=True,
            engine="python"
        )
        if df.empty:
            print(f"⚠️ File {path.name} loaded but is empty.")
        return df
    except Exception as e:
        print(f"⚠️ Warning: Failed to read CSV {path}: {e}. Retrying with fallback...")
        try:
            df = pd.read_csv(path, encoding="latin1", sep=";", error_bad_lines=False, engine="python")
            return df
        except Exception as e2:
            print(f"❌ Second failure reading {path}: {e2}")
            return pd.DataFrame()

# Constants
CHUNK_SIZE = 1_000_000
YEARS = [2002, 2006, 2010, 2014, 2018, 2022, 2026]
DATA_DIR = Path.home() / "SHRKVSCODE" / "polls_pipeline" / "data" / "tse"
if not DATA_DIR.exists():
    print(f"⚠️ Warning: DATA_DIR path not found: {DATA_DIR}")
else:
    print(f"✅ Using absolute DATA_DIR path: {DATA_DIR}")
print(f"🧠 Importer initialized for years: {YEARS}")
if not any(DATA_DIR.rglob('*.csv')):
    print(f"⚠️ No CSV files found recursively in {DATA_DIR}. Please verify extracted data folders exist.")
DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "elections_mvp.duckdb"
print(f"🔍 DATA_DIR in use: {DATA_DIR}")

# Setup logger
LOG_DIR = Path("mvp/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=LOG_DIR / "08_import_tse_multi_year.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

# ---------------------------------------------------------------------------
# Helper: Fetch TSE CSV/ZIP from CKAN if missing (2014–2022, reproducible)
def fetch_tse_from_ckan(year, dataset_type):
    """
    Download TSE dataset ZIP/CSV for a given year/type from CKAN if not present in DATA_DIR.
    Example dataset_type: 'votacao_candidato_munzona', 'consulta_cand'
    """
    # Only attempt for years 2014–2022 (CKAN API covers these best)
    if year not in range(2014, 2023):
        return
    api_url = f"https://dadosabertos.tse.jus.br/api/3/action/package_search?q={dataset_type}+{year}"
    try:
        resp = requests.get(api_url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("result", {}).get("results", [])
        if not results:
            print(f"🌐 No CKAN package found for {dataset_type} {year}")
            return
        # Find all .zip or .csv resources
        found = False
        for pkg in results:
            for r in pkg.get("resources", []):
                url = r.get("url")
                if not url:
                    continue
                if url.endswith(".zip") or url.endswith(".csv"):
                    fname = url.split("/")[-1]
                    dest = DATA_DIR / fname
                    if dest.exists():
                        print(f"🌐 {fname} already exists, skipping download.")
                        continue
                    # Download file
                    print(f"🌐 Downloading {fname} from TSE CKAN...")
                    with requests.get(url, stream=True, timeout=60) as rfile:
                        rfile.raise_for_status()
                        with open(dest, "wb") as f:
                            for chunk in rfile.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                    print(f"✅ Downloaded {fname} to {dest}")
                    found = True
        if not found:
            print(f"🌐 No downloadable .zip or .csv found for {dataset_type} {year}")
    except Exception as e:
        print(f"❌ CKAN fetch failed for {dataset_type} {year}: {e}")

def extract_zip_files():
    """
    Extract all .zip files in DATA_DIR if not already extracted.
    Skips extraction if files with same names exist.
    Logs actions accordingly.
    """
    for zip_path in DATA_DIR.glob("*.zip"):
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Check if all files already exist
                all_exist = True
                for member in zip_ref.namelist():
                    member_path = DATA_DIR / member
                    if not member_path.exists():
                        all_exist = False
                        break
                if all_exist:
                    logging.info(f"Skipped extraction of {zip_path.name}: files already exist.")
                    continue
                zip_ref.extractall(DATA_DIR)
                logging.info(f"Extracted {zip_path.name} into {DATA_DIR}")
        except Exception as e:
            logging.error(f"Failed to extract {zip_path.name}: {e}")


def load_tse_csv(year, kind):
    """
    Enhanced loader: handles both 'votacao' and 'candidatos' datasets.
    Now supports nested folders like consulta_cand_2022/.
    """
    print(f"🔍 Searching {kind} files for {year} recursively...")
    if kind == "votacao":
        pattern = f"votacao_candidato_munzona_{year}_"
        file_paths = [p for p in DATA_DIR.rglob("*") if p.is_file() and pattern in p.name]
        if not file_paths:
            logging.error(f"No voting files found for year {year} with pattern {pattern}")
            print(f"⚠️ No CSVs found for year {year} (votacao) with pattern {pattern}")
            return pd.DataFrame()
        for file_path in file_paths:
            df = safe_read_csv(file_path)
            df.columns = df.columns.str.strip()
            if df.empty:
                continue
            yield df
        return

    elif kind == "candidatos":
        pattern_flat = f"candidatos-{year}.csv"
        pattern_nested = f"consulta_cand_{year}_"
        candidates_files = [p for p in DATA_DIR.rglob("*") if p.is_file() and (pattern_flat.replace("*", "") in p.name or pattern_nested in p.name)]
        if not candidates_files:
            logging.error(f"No candidate files found for year {year} in {DATA_DIR}")
            print(f"⚠️ No CSVs found for year {year} (candidatos) in {DATA_DIR}")
            return pd.DataFrame()

        for file_path in candidates_files:
            logging.info(f"Loading candidate file {file_path}")
            df = safe_read_csv(file_path)
            df.columns = df.columns.str.strip()
            if df.empty:
                continue
            yield df
        return
    else:
        logging.error(f"Unknown kind '{kind}'")
        return pd.DataFrame()
def normalize_votacao_df(df, year):
    df.columns = [unidecode(col).strip().upper() for col in df.columns]
    votacao_cols = {
        "uf": "SG_UF",
        "cargo": "DS_CARGO",
        "turno": "NR_TURNO",
        "nome": None,
        "partido": "SG_PARTIDO",
        "votos": None,
        "tipo_resultado": None,
    }
    if "NM_CANDIDATO" in df.columns:
        votacao_cols["nome"] = "NM_CANDIDATO"
    elif "NM_URNA_CANDIDATO" in df.columns:
        votacao_cols["nome"] = "NM_URNA_CANDIDATO"
    else:
        votacao_cols["nome"] = None

    # Vote column detection (with fallback)
    if "QT_VOTOS" in df.columns:
        votacao_cols["votos"] = "QT_VOTOS"
    elif "QT_VOTOS_NOMINAIS" in df.columns:
        votacao_cols["votos"] = "QT_VOTOS_NOMINAIS"
    elif "QT_VOTOS_NOMINAIS_VALIDOS" in df.columns:
        votacao_cols["votos"] = "QT_VOTOS_NOMINAIS_VALIDOS"
    # Add fallback detection for QT_VOTOS_NOMINAIS_VALIDOS if not already present
    elif "QT_VOTOS_NOMINAIS_VALIDOS" in df.columns:
        votacao_cols["votos"] = "QT_VOTOS_NOMINAIS_VALIDOS"
    else:
        votacao_cols["votos"] = None

    print(f"✅ Using vote column for {year}: {votacao_cols['votos']}")

    if "DS_SIT_TOT_TURNO" in df.columns:
        votacao_cols["tipo_resultado"] = "DS_SIT_TOT_TURNO"
    elif "DS_SITUACAO_CANDIDATO_TOT" in df.columns:
        votacao_cols["tipo_resultado"] = "DS_SITUACAO_CANDIDATO_TOT"
    else:
        votacao_cols["tipo_resultado"] = None

    votacao_norm = pd.DataFrame()
    votacao_norm["ano"] = year
    votacao_norm["uf"] = df[votacao_cols["uf"]] if votacao_cols["uf"] and votacao_cols["uf"] in df.columns else pd.Series(dtype=str)
    votacao_norm["cargo"] = df[votacao_cols["cargo"]] if votacao_cols["cargo"] and votacao_cols["cargo"] in df.columns else pd.Series(dtype=str)
    votacao_norm["turno"] = df[votacao_cols["turno"]] if votacao_cols["turno"] and votacao_cols["turno"] in df.columns else pd.Series(dtype=int)
    votacao_norm["nome"] = df[votacao_cols["nome"]] if votacao_cols["nome"] and votacao_cols["nome"] in df.columns else pd.Series(dtype=str)
    votacao_norm["partido"] = df[votacao_cols["partido"]] if votacao_cols["partido"] and votacao_cols["partido"] in df.columns else pd.Series(dtype=str)
    if votacao_cols["votos"] and votacao_cols["votos"] in df.columns:
        # Clean and coerce votes to numeric (handles '.', ',', spaces, and text)
        df[votacao_cols["votos"]] = (
            df[votacao_cols["votos"]]
            .astype(str)
            .str.replace(r"[^0-9]", "", regex=True)
            .replace("", "0")
        )
        votacao_norm["votos"] = (
            pd.to_numeric(df[votacao_cols["votos"]], errors="coerce")
            .fillna(0)
            .astype(int)
        )
        print(f"✅ Parsed non-zero votes for {year}: {int((votacao_norm['votos'] > 0).sum())}")
    else:
        votacao_norm["votos"] = pd.Series(dtype=int)
    if votacao_cols["tipo_resultado"] and votacao_cols["tipo_resultado"] in df.columns:
        votacao_norm["tipo_resultado"] = df[votacao_cols["tipo_resultado"]]
    else:
        votacao_norm["tipo_resultado"] = ""

    # Normalize cargo text before filtering to ensure match regardless of case or accent
    votacao_norm["cargo"] = votacao_norm["cargo"].astype(str).str.upper().str.strip()
    votacao_norm = votacao_norm[votacao_norm["cargo"].isin(["GOVERNADOR", "SENADOR", "PRESIDENTE"])]
    return votacao_norm

def normalize_candidatos_df(df, year):
    df.columns = [unidecode(col).strip().upper() for col in df.columns]
    candidatos_cols = {
        "uf": "SG_UF",
        "cargo": "DS_CARGO",
        "turno": "NR_TURNO",
        "nome": None,
        "partido": "SG_PARTIDO",
    }
    if "NM_CANDIDATO" in df.columns:
        candidatos_cols["nome"] = "NM_CANDIDATO"
    elif "NM_URNA_CANDIDATO" in df.columns:
        candidatos_cols["nome"] = "NM_URNA_CANDIDATO"
    else:
        candidatos_cols["nome"] = None

    candidatos_norm = pd.DataFrame()
    candidatos_norm["ano"] = year
    candidatos_norm["uf"] = df[candidatos_cols["uf"]] if candidatos_cols["uf"] and candidatos_cols["uf"] in df.columns else pd.Series(dtype=str)
    candidatos_norm["cargo"] = df[candidatos_cols["cargo"]] if candidatos_cols["cargo"] and candidatos_cols["cargo"] in df.columns else pd.Series(dtype=str)
    candidatos_norm["turno"] = df[candidatos_cols["turno"]] if candidatos_cols["turno"] and candidatos_cols["turno"] in df.columns else pd.Series(dtype=int)
    candidatos_norm["nome"] = df[candidatos_cols["nome"]] if candidatos_cols["nome"] and candidatos_cols["nome"] in df.columns else pd.Series(dtype=str)
    candidatos_norm["partido"] = df[candidatos_cols["partido"]] if candidatos_cols["partido"] and candidatos_cols["partido"] in df.columns else pd.Series(dtype=str)
    candidatos_norm["votos"] = 0  # Use integer zero for candidates
    candidatos_norm["tipo_resultado"] = ""

    candidatos_norm = candidatos_norm[candidatos_norm["cargo"].isin(["GOVERNADOR", "SENADOR", "PRESIDENTE"])]

    return candidatos_norm


def import_year_data(con, year):
    """
    Improved: process voting and candidate data independently
    and merge them before writing to staging.
    """
    logging.info(f"Importing data for year {year}")

    # --- Automatic TSE data acquisition patch ---
    fetch_tse_from_ckan(year, "votacao_candidato_munzona")
    fetch_tse_from_ckan(year, "consulta_cand")
    # -------------------------------------------

    votacao_data = load_tse_csv(year, "votacao")
    candidatos_data = load_tse_csv(year, "candidatos")

    def collect_frames(gen_or_df):
        dfs = []
        if gen_or_df is None:
            return dfs
        if isinstance(gen_or_df, pd.DataFrame):
            dfs.append(gen_or_df)
        else:
            for g in gen_or_df:
                if g is not None and not g.empty:
                    dfs.append(g)
        return dfs

    votacao_frames = collect_frames(votacao_data)
    candidatos_frames = collect_frames(candidatos_data)

    if not votacao_frames and not candidatos_frames:
        print(f"⚠️ No input frames collected for {year}. Skipping early.")
        return

    # Normalize and combine data safely
    all_votacao = pd.concat(
        [normalize_votacao_df(df, year) for df in votacao_frames if not df.empty],
        ignore_index=True
    ) if votacao_frames else pd.DataFrame()

    all_candidatos = pd.concat(
        [normalize_candidatos_df(df, year) for df in candidatos_frames if not df.empty],
        ignore_index=True
    ) if candidatos_frames else pd.DataFrame()

    # Force schema alignment if one is empty
    if all_votacao.empty and not all_candidatos.empty:
        all_votacao = all_candidatos.copy()
        all_votacao["votos"] = pd.NA
        all_votacao["tipo_resultado"] = ""
    elif all_candidatos.empty and not all_votacao.empty:
        all_candidatos = all_votacao.copy()

    combined_df = pd.concat([all_votacao, all_candidatos], ignore_index=True, sort=False).fillna("")

    # Ensure the 'votos' column is numeric; convert non-numeric values to 0
    if "votos" in combined_df.columns:
        combined_df["votos"] = (
            pd.to_numeric(combined_df["votos"], errors="coerce")
            .fillna(0)
            .astype(int)
        )

    # Always print diagnostics even if partial data
    print(f"📊 Year {year}: votacao_rows={len(all_votacao):,}, candidatos_rows={len(all_candidatos):,}, combined={len(combined_df):,}")

    if combined_df.empty:
        print(f"⚠️ Combined dataset for year {year} is empty after alignment. Skipping.")
        return

    staging_table = f"staging_raw_{year}"
    try:
        # ✅ Force numeric type for votes before writing to DuckDB
        if "votos" in combined_df.columns:
            combined_df["votos"] = (
                pd.to_numeric(combined_df["votos"], errors="coerce")
                .fillna(0)
                .astype(int)
            )
        con.execute(f"DROP TABLE IF EXISTS {staging_table}")
        con.register("combined_df", combined_df)
        con.execute(f"CREATE OR REPLACE TABLE {staging_table} AS SELECT * FROM combined_df")
        con.unregister("combined_df")
        print(f"✅ Created {staging_table} with {len(combined_df):,} records")
        con.commit()
    except Exception as e:
        logging.error(f"Error writing {staging_table}: {e}")
        print(f"❌ Error writing {staging_table}: {e}")
        return

    # Upsert parties and candidates (robust schema handling)
    try:
        # Ensure table exists and add missing columns dynamically
        con.execute("CREATE TABLE IF NOT EXISTS party_labels (party_label VARCHAR)")
        existing_cols = [c[1] for c in con.execute("PRAGMA table_info('party_labels')").fetchall()]
        if "party_label" not in existing_cols:
            con.execute("ALTER TABLE party_labels ADD COLUMN party_label VARCHAR")

        parties = con.execute(f"SELECT DISTINCT partido FROM {staging_table} WHERE partido IS NOT NULL").fetchall()
        for (p,) in parties:
            con.execute("""
                INSERT INTO party_labels (party_label)
                SELECT ? WHERE NOT EXISTS (SELECT 1 FROM party_labels WHERE party_label = ?)
            """, [p, p])
        print(f"✅ Upserted {len(parties)} parties for year {year}")
    except Exception as e:
        print(f"❌ Failed to upsert party labels for {year}: {e}")

    try:
        con.execute("CREATE TABLE IF NOT EXISTS candidate_labels (candidate_label VARCHAR)")
        existing_cols = [c[1] for c in con.execute("PRAGMA table_info('candidate_labels')").fetchall()]
        if "candidate_label" not in existing_cols:
            con.execute("ALTER TABLE candidate_labels ADD COLUMN candidate_label VARCHAR")

        candidates = con.execute(f"SELECT DISTINCT nome FROM {staging_table} WHERE nome IS NOT NULL").fetchall()
        for (c,) in candidates:
            con.execute("""
                INSERT INTO candidate_labels (candidate_label)
                SELECT ? WHERE NOT EXISTS (SELECT 1 FROM candidate_labels WHERE candidate_label = ?)
            """, [c, c])
        print(f"✅ Upserted {len(candidates)} candidates for year {year}")
    except Exception as e:
        print(f"❌ Failed to upsert candidate labels for {year}: {e}")

    del votacao_frames, candidatos_frames, combined_df, all_votacao, all_candidatos
    gc.collect()
    # Print summary for historical check
    print(f"🌐 Historical TSE data check complete for {year}.")

def main(
):
    """
    Main function to process all years and load data into DuckDB.
    """
    extract_zip_files()
    con = None
    try:
        con = duckdb.connect(str(DB_PATH))
        try:
            tables = [t[0] for t in con.execute("SHOW TABLES").fetchall()]
            print(f"🗂️ Existing DuckDB tables: {tables}")
        except Exception as e:
            print(f"⚠️ Could not list tables: {e}")

        header_msg = f"Starting multi-year import for TSE data ({min(YEARS)}–{max(YEARS)})..."
        logging.info(header_msg)
        print(header_msg)

        for year in YEARS:
            print(f"\n🚀 Processing election year {year}...\n")
            try:
                logging.info(f"Starting import for year {year}")
                import_year_data(con, year)
                logging.info(f"Successfully imported data for year {year}")
            except Exception as e:
                error_msg = f"Failed to import data for year {year}: {e}"
                logging.error(error_msg)
                print(error_msg)

        con.commit()
        con.close()
        print("🧩 All commits completed and connection closed.")

        success_msg = f"All years processed. Total years: {len(YEARS)}"
        print(success_msg)
        logging.info(success_msg)

    except Exception as e:
        error_msg = f"Error during import: {e}"
        logging.error(error_msg)
        print(error_msg)
    finally:
        if con is not None:
            con.close()
            logging.info("DuckDB connection closed successfully.")
        print("✅ Multi-year import routine finished. Check mvp/logs/08_import_tse_multi_year.log for detailed results.")

if __name__ == "__main__":
    main()
