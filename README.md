# VoteOddsBR — Brazilian Election Data Analytics

**Version:** v0.9.0  
**Status:** Stable — Dashboard export and analytics pipeline validated  
**Maintainer:** Igor Lôbo Vieira da Cunha (Shark)

## 🧭 Overview
VoteOddsBR is a DuckDB‑powered analytics pipeline for Brazilian election data (TSE). It ingests, normalizes, and aggregates multi‑year electoral and poll datasets to produce dashboards and structured exports for political and social analysis.

## 📂 Project Structure
```
~/SHRKVSCODE/voteoddsbr/
├── data/               # DuckDB databases and cached JSONs
├── mvp/                # Scripts and SQL views
│   ├── scripts/        # Pipeline scripts (08_import_tse_multi_year, 09_build_reelection_summary…)
│   ├── sql/            # SQL views and transforms
│   └── exports/        # Generated CSV exports
├── meta_api/           # Meta API (social data) integration
├── logs/               # Pipeline logs
├── exports/            # Root‑level consolidated outputs
└── README.md           # Project documentation
```

## ⚙️ Environment Setup
```bash
cd ~/SHRKVSCODE/voteoddsbr
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```
Dependencies include: `duckdb`, `pandas`, `tqdm`, and `requests`.

## 🚀 Pipeline Execution
Typical flow:
```bash
# 1️⃣ Import historical TSE data
python mvp/scripts/08_import_tse_multi_year.py

# 2️⃣ Build reelection summary
python mvp/scripts/09_build_reelection_summary.py

# 3️⃣ Generate dashboard summary
python mvp/scripts/09b_build_dashboard_summary.py

# 4️⃣ Analyze results interactively
python analyze_dashboard.py
```
Results are exported under `mvp/exports/`, e.g.:
- `dashboard_summary.csv`
- `dashboard_by_office_state_round.csv`

## 🧪 Data Sources
- **TSE open data:** Official Brazilian electoral datasets (2022+)
- **Site Cache JSONs:** Processed intermediate election files (`/data/site_cache/...`)

## 📊 Outputs
Each run exports clean CSVs and DuckDB views:
- `v_reelection_summary` — Candidates and reelection potential
- `v_dashboard_summary` — Dashboard aggregation

## 🔍 Validation
Integrity check via:
```bash
bash check_integrity.sh
```
This verifies: database access, Python environment, and Git status.

## 🧭 Roadmap (Summary)
See `ROADMAP.md` for detailed milestones.
- [x] Core DuckDB ingestion
- [x] Dashboard exports
- [ ] Poll integration
- [ ] Meta API social metrics merge
- [ ] Visualization dashboard (Flourish / Streamlit)

## 🧾 License
Internal analytical use. Contact maintainer for publication rights.

---
_© 2026 Shark Analytics — Recife, PE, Brazil_
