

# 🧩 VoteOddsBR — Release v0.9.0

**Version:** v0.9.0  
**Release Date:** 2026-01-19  
**Maintainer:** Igor Lôbo Vieira da Cunha (Shark)  
**Repository:** https://github.com/igorlobovc/voteoddsbr  
**License:** Internal SHRK Analytics — Research & Development Only

---

## 🎯 Project Objective
VoteOddsBR is a **data analytics pipeline** for Brazilian elections. It centralizes data from multiple public sources — including the **TSE Open Data Portal** and future polling datasets — to produce consistent, queryable DuckDB databases and dashboards for electoral intelligence.

It is designed to:
1. Aggregate multi-year official election data (votes, candidates, reelections).
2. Produce summary tables for dashboards and political analytics.
3. Integrate poll averages, social metrics, and official results in one schema.
4. Enable fast, reproducible CSV and SQL exports.

---

## 📁 Directory Overview
```
~/SHRKVSCODE/voteoddsbr/
├── data/                     # Core DuckDB database (elections_mvp.duckdb)
├── exports/                  # CSV outputs (dashboard_summary.csv, grouped analyses)
├── logs/                     # Execution logs from all pipeline scripts
├── meta_api/                 # Social media and Meta API integration scripts
├── mvp/
│   ├── scripts/              # Core processing scripts (08–09b)
│   ├── sql/                  # SQL views (v_dashboard_summary.sql)
│   ├── exports/              # Exported analytical tables (dashboard_by_office...)
│   └── logs/                 # Step-by-step execution history
├── check_integrity.sh        # Automated environment & data validator
├── analyze_dashboard.py      # CSV summarizer and analyzer
├── requirements.txt          # Python dependencies for v0.9.0
└── CHANGELOG.md              # Version history and roadmap alignment
```

---

## ⚙️ Pipeline Flow Summary

| Step | Script | Description |
|------|---------|-------------|
| 1️⃣ | `08_import_tse_multi_year.py` | Downloads and imports multi-year TSE election data into DuckDB. |
| 2️⃣ | `09_build_reelection_summary.py` | Builds `v_reelection_summary` with candidate and total vote aggregates. |
| 3️⃣ | `09b_build_dashboard_summary.py` | Creates unified dashboard view `v_dashboard_summary` and exports CSVs. |
| 4️⃣ | `analyze_dashboard.py` | Performs grouping, comparison, and validation of exported data. |
| 5️⃣ | `check_integrity.sh` | Runs environment, dependency, and schema checks. |

---

## 📊 Key Outputs (v0.9.0)
| File | Description |
|-------|-------------|
| `mvp/exports/dashboard_summary.csv` | Master summary of votes per race and office. |
| `mvp/exports/dashboard_by_office_state_round.csv` | Aggregated results by office, state, and round. |
| `mvp/exports/dashboard_by_office_state_round_with_share.csv` | Adds total and vote share columns. |
| `logs/*.log` | Execution logs for each script run. |

---

## 🧠 AI Context Block
This file provides a high-level map for any AI system (e.g. Codex, GPT, LM Studio) to understand and extend the VoteOddsBR project.

### Context Structure:
- **Environment Path:** `/Users/igorcunha/SHRKVSCODE/voteoddsbr/`
- **Core DB File:** `data/elections_mvp.duckdb`
- **Exports Folder:** `mvp/exports/`
- **Logs Folder:** `mvp/logs/`
- **Python Environment:** `.venv` activated via `source .venv/bin/activate`

### AI Usage Guidelines:
1. Always check `CHANGELOG.md` before generating code.
2. Read SQL files under `mvp/sql/` for schema references.
3. Use DuckDB queries via Python (not direct shell) for consistency.
4. Avoid overwriting files under `data/` — use new exports.
5. Use this structure for automated analysis, plotting, or meta-integration.

---

## 🪜 Milestones
### ✅ Completed (v0.9.0)
- Functional multi-step pipeline from ingestion to export.
- Clean environment with verified dependencies.
- Unified CSV and SQL outputs for dashboards.
- Version control integrated with GitHub.

### 🚧 Next (v1.0.0)
- Add poll ingestion and normalization scripts.
- Connect Meta API for social data correlation.
- Automate DuckDB refresh for future election years.

### 🔜 Future (v1.1.0)
- Build Streamlit/Flourish visualization layer.
- Publish web dashboard for interactive analysis.

---

## 📦 Release Summary for GitHub
**Tag:** `v0.9.0`  
**Type:** Stable release  
**Highlights:** Core ingestion and dashboard pipeline finalized.  
**Breaking Changes:** None.  
**Next Tag:** `v1.0.0` — Poll + Meta API integration.

---

_© 2026 SHRK Analytics — Recife, Pernambuco, Brazil_