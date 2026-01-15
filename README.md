The repository voteoddsbr contains a minimalist pipeline for ingesting and analysing Brazilian election data published by the Tribunal Superior Eleitoral (TSE).  Its core lies under mvp/scripts, which houses Python scripts to fetch and normalize multiple years of CSV data, store the results in a DuckDB database and build a cross‑year re‑election summary.  Below is a technical README draft explaining the project structure, how to set it up on macOS and how to run the ingestion and analysis scripts.  Citations refer to the extracted code for accuracy.

VoteOddsBR
Overview
VoteOddsBR is a prototype data‑engineering pipeline for Brazilian election data.  It automates ingestion of raw CSV/ZIP files published by TSE, harmonizes column names and data types, loads the cleaned data into a DuckDB database and generates multi‑year analytics.  The primary goal is to enable cross‑year re‑election analysis and provide a foundation for building dashboards or further analytics.  The project uses Python (Pandas and DuckDB) and offers scripts to fetch missing data from the TSE CKAN API, normalize votes/candidate data and compute re‑election summaries.
Legacy context
This repository builds upon logic from a previous polls_pipeline project.  Evidence of this includes:


Data directory – the ingestion script still points to ~/SHRKVSCODE/polls_pipeline/data/tse when searching for CSV files.


User‑agent strings – ckan_search.py identifies itself as "polls-pipeline/ckan-search", and constants such as RESULTADOS_TITLE_RE reference datasets discovered in the older pipeline.


Common functions – helpers like safe_read_csv, CKAN search logic and normalization routines appear to have been ported directly from the polls_pipeline codebase.


These legacy artifacts should be refactored in future releases to align file paths and naming with the new project.
Folder structure
voteoddsbr/
├── .env                 # optional environment variables
├── main.py              # entry point used in the legacy polls pipeline (not used by MVP)
├── poll_discovery.py    # legacy discovery script
├── data/
│   └── elections_mvp.duckdb    # DuckDB database created by the ingestion script
├── mvp/
│   ├── logs/            # logs and CSV outputs from scripts
│   └── scripts/
│       ├── 08_import_tse_multi_year.py    # multi‑year TSE ingestion and normalization
│       ├── 09_build_reelection_summary.py # builds cross‑year re‑election summary
│       └── ckan_search.py                 # helper to query TSE CKAN API
└── README.md            # (this draft)



mvp/scripts/08_import_tse_multi_year.py – imports TSE voting and candidate datasets for multiple years.  It reads CSV/ZIP files from ~/SHRKVSCODE/polls_pipeline/data/tse, automatically downloads missing files from TSE’s CKAN API and normalizes fields such as UF, cargo (office), turno (round), candidate names, party abbreviations and vote counts.  The script writes a staging table staging_raw_{year} for each year into a DuckDB database, while also upserting unique party and candidate labels into dimension tables.  Years processed by default include 2002, 2006, 2010, 2014, 2018, 2022 and 2026.


mvp/scripts/09_build_reelection_summary.py – reads all staging_raw_* tables from the DuckDB database and builds a view v_reelection_summary.  The view aggregates votes per candidate across all available years, counts how many distinct years each candidate ran and flags those with more than one year as possible re‑election cases.  It exports the view to a CSV file (mvp/logs/09_reelection_summary.csv) and prints the top 10 candidates by number of years contested and total votes.


mvp/scripts/ckan_search.py – a CLI module to search the TSE CKAN API for dataset packages.  It defines dataclasses for result structures and functions to iterate through packages, extract yearly metadata from dataset names and match resources by keywords like votacao_candidato_munzona.  This script is helpful if you want to discover new datasets but is not required for the basic ingestion pipeline.


Dependencies and environment setup (macOS)
The project targets Python 3.11 (any recent 3.x should work) and uses DuckDB for analytics.  A virtual environment is recommended to avoid conflicts.


Install prerequisites – ensure you have python3, pip, git and wget available on your Mac.  Homebrew users can run:
brew install python git



Clone the repository:
git clone https://github.com/igorlobovc/voteoddsbr.git
cd voteoddsbr



Create and activate a virtual environment (.venv):
python3 -m venv .venv
source .venv/bin/activate



Install dependencies.  There is no requirements.txt, so install manually:
pip install duckdb pandas requests unidecode

Optional packages for CKAN search and development (e.g., rich, typer) can be added as needed.


Prepare the data directory – the ingestion script expects raw TSE files in ~/SHRKVSCODE/polls_pipeline/data/tse.  If this directory does not exist, create it or set a different DATA_DIR via environment variables before running the script.  Ensure you have enough disk space for multiple election-year datasets.


Usage guide
1. Ingest multi‑year TSE data
Run the ingestion script from the project root:
python mvp/scripts/08_import_tse_multi_year.py

What it does:


Downloads missing datasets – for years 2014–2022, the script queries the TSE CKAN API and downloads ZIP/CSV resources matching the patterns votacao_candidato_munzona_{year} and consulta_cand_{year}.


Extracts archives – any .zip files in the data directory are extracted to ~/SHRKVSCODE/polls_pipeline/data/tse.


Loads and normalizes – all CSV files are read with robust error handling (safe_read_csv), columns are stripped of accents and renamed to a unified schema (e.g., SG_UF, DS_CARGO, NR_TURNO, NM_CANDIDATO) and vote counts are parsed into integers.


Creates staging tables – for each year, a table staging_raw_{year} is created in data/elections_mvp.duckdb containing normalized rows.  If a year has both candidate and voting files, they are concatenated; missing votes default to zero.


Upserts labels – unique parties and candidate names are inserted into party_labels and candidate_labels dimension tables, avoiding duplicates.


Logging – all messages, warnings and errors are logged to mvp/logs/08_import_tse_multi_year.log.


The script will iterate through the predefined years list (currently [2002, 2006, 2010, 2014, 2018, 2022, 2026]) and print progress information.  Successful completion leaves a DuckDB database at data/elections_mvp.duckdb with multiple staging tables.
2. Build the re‑election summary
Once the multi‑year data is loaded, generate a cross‑year summary:
python mvp/scripts/09_build_reelection_summary.py

This script performs the following tasks:


Connects to the DuckDB database – by default at data/elections_mvp.duckdb.


Discovers staging tables – it lists all tables whose names match staging_raw_(\d{4}).


Creates a view – uses a union query to aggregate votes per candidate and year, sums total votes, counts distinct election years and flags candidates appearing in more than one year as possible_reelection.  It creates or replaces a view v_reelection_summary in DuckDB.


Exports CSV – writes the full view to mvp/logs/09_reelection_summary.csv ordered by num_years and total_votes, and prints the top ten candidates to stdout.


Logging – writes a log file mvp/logs/09_build_reelection_summary.log.


Ensure the ingestion script has been run first; otherwise, the summary script will create an empty view and issue a warning.
Expected outputs
After running both scripts:
ArtifactLocationDescriptionDuckDB databasedata/elections_mvp.duckdbContains staging_raw_{year} tables, party_labels, candidate_labels and the v_reelection_summary view.Import logmvp/logs/08_import_tse_multi_year.logDetailed logs from the ingestion process, including download status and normalization diagnostics.Re‑election summary viewin DuckDBThe v_reelection_summary view summarises total votes, number of election years and a comma‑separated list of years per candidate.CSV summarymvp/logs/09_reelection_summary.csvA CSV export of the view, ordered by number of years and total votes.Summary logmvp/logs/09_build_reelection_summary.logLogs for the re‑election summary generation.
Scaling and performance notes


DuckDB is used as the analytical engine.  DuckDB performs queries in‑process and benefits from columnar storage; it can efficiently scan multi‑million‑row tables and supports parallel execution.


Incremental ingestion – each election year is processed independently.  If new years are added to the YEARS list, they will be downloaded (if necessary) and appended to the database.  Running the script multiple times will upsert party and candidate labels without duplication.


Data acquisition – fetch_tse_from_ckan downloads datasets only when missing, avoiding redundant network requests.  CKAN search can be extended to detect additional resource types via ckan_search.py.


Normalization – columns are normalized using unidecode and uppercase conversions to ensure comparability across years and dataset formats.


Parallelism – the current scripts process each year sequentially.  For improved throughput, the YEARS loop could be parallelized (e.g., using multiprocessing) and DuckDB can ingest multiple staging tables concurrently.  However, concurrency should be carefully tuned to avoid memory exhaustion, especially when processing large CSV files on limited hardware.


Planned roadmap (v1.0)


Refactor legacy paths – migrate the data directory from the old polls_pipeline structure to a project‑local path (data/tse) and expose it via a configuration setting.


Add configuration file – introduce a settings.yaml or .env file to define parameters such as YEARS, DATA_DIR, database path and CKAN API options.


Enhance CKAN integration – integrate ckan_search.py into the ingestion process to automatically discover and download future datasets (e.g., 2024 municipal elections).


Cross‑year re‑election analysis (v1.0) – expand the summary view to include metrics like vote share, positions (Governor, Senator, President) and success of re‑election bids.  Add simple visualizations (e.g., bar charts) exported to PNG/HTML.


Visualization exports – provide scripts to export charts or interactive dashboards (Matplotlib/Altair/Streamlit) summarizing the data, ready for publication.


Documentation improvements – write user‑friendly guides, API documentation for the CKAN search helper and examples of SQL queries on the DuckDB database.



About
VoteOddsBR: a Python‑powered data ingestion and analytics engine for Brazilian election data, built on DuckDB for fast multi‑year analysis of TSE datasets.Relevant tabsvoteoddsbr/mvp/scripts/09_build_reelection_summary.py at master · igorlobovc/voteoddsbrGitHub
