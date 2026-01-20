


# 🧭 VoteOddsBR Roadmap — v0.9.0 → v1.1

This roadmap outlines the key development phases, milestones, and future improvements for the VoteOddsBR project.

---

## 🚀 Phase 1 — Core Data Backbone (Completed ✅)
**Objective:** Establish the canonical election data pipeline from TSE sources.

**Deliverables:**
- [x] DuckDB-based database `elections_mvp.duckdb`
- [x] `08_import_tse_multi_year.py` for automated ingestion
- [x] `09_build_reelection_summary.py` for reelection insights
- [x] `09b_build_dashboard_summary.py` for aggregated dashboards
- [x] Verified exports (`dashboard_summary.csv`, `dashboard_by_office_state_round.csv`)

**Next Actions:**
- Automate integrity checks (`check_integrity.sh`)
- Integrate version control commits on successful builds

---

## 📊 Phase 2 — Polls Integration (In Progress 🧩)
**Objective:** Merge historical polling data with TSE official results for enriched insights.

**Tasks:**
- [ ] Reactivate `polls_pipeline` ingestion modules (under `mvp/polls/`)
- [ ] Normalize poll structure (institutes, dates, sample size)
- [ ] Combine poll averages with electoral outcomes
- [ ] Export unified dataset: `polls_vs_results.csv`

**Dependencies:** Requires TSE canonical tables to be complete and consistent.

---

## 🌐 Phase 3 — Meta API & Social Data (Planned 🧭)
**Objective:** Integrate Meta Ads / Pages / Engagement metrics for campaign-level analysis.

**Tasks:**
- [ ] Connect to `meta_api/SAIDA` outputs
- [ ] Build correlation model: social reach × votes × regions
- [ ] Generate dashboards in `mvp/exports/social_influence.csv`

---

## 🧮 Phase 4 — Advanced Analytics & Visualization (Planned)
**Objective:** Create comparative analytics for re-election trends, turnout, and demographic clusters.

**Tasks:**
- [ ] Expand DuckDB views with multi-year dimensions
- [ ] Create Flourish / Streamlit dashboard with dynamic filters
- [ ] Integrate `v_dashboard_summary` with visualization API endpoints

---

## 🧠 Phase 5 — Automation & DevOps (Planned)
**Objective:** Streamline CI/CD and reproducibility.

**Tasks:**
- [ ] Implement GitHub Actions for build + export verification
- [ ] Add `version.txt` auto-updater
- [ ] Schedule periodic updates (e.g., monthly TSE sync)

---

## 🧩 Versioning
| Version | Description | Status |
|----------|--------------|---------|
| v0.9.0 | Core TSE ingestion + dashboard | ✅ Completed |
| v1.0.0 | Polls integration + Meta API prep | 🚧 In progress |
| v1.1.0 | Visualization and automation layer | 🔜 Planned |

---

## 🧾 Contributors & Credits
**Lead Developer:** Igor Lôbo Vieira da Cunha (Shark)  
**Frameworks:** Python, DuckDB, Pandas, Bash  
**License:** Internal Analytics Use — 2026

---

**Next milestone:** Integrate `polls_pipeline` with `voteoddsbr` and export first full combined dataset.