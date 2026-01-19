# 🧾 VoteOddsBR — Changelog

All notable changes to this project will be documented in this file.

---

## [v0.9.0] — 2026-01-19
### Added
- Implemented `08_import_tse_multi_year.py` for TSE multi-year data ingestion.
- Added `09_build_reelection_summary.py` for reelection analytics.
- Added `09b_build_dashboard_summary.py` for dashboard data exports.
- Created SQL view `v_dashboard_summary.sql` to unify aggregated metrics.
- Introduced integrity validation script `check_integrity.sh`.
- Added `analyze_dashboard.py` for high-level summary analysis and CSV comparison.

### Fixed
- Corrected missing columns (`candidate`, `valid_votes_share`) in SQL bindings.
- Resolved file locking issue on `elections_mvp.duckdb` (DuckDB concurrency fix).
- Adjusted Python path activation for virtual environment consistency.

### Improved
- Standardized CSV output schema: `race_id`, `year`, `office`, `state`, `round`, `total_votes`, `num_candidates`, `possible_reelection`.
- Enhanced logging with emojis and timestamps for all pipeline scripts.
- Improved project folder structure (`meta_api`, `mvp/exports`, `logs`).

---

## [v1.0.0] — Planned (Q1 2026)
### To Be Added
- Poll integration module to merge TSE and institute datasets.
- Poll/TSE combined dataset export (`polls_vs_results.csv`).
- Meta API connector for campaign social metrics.
- Documentation automation with GitHub Actions.

### To Be Improved
- Add auto-refresh command for database sync.
- Implement unified error handling across all mvp/scripts.

---

## [v1.1.0] — Planned (Q2 2026)
### To Be Added
- Interactive dashboards (Flourish/Streamlit integration).
- Visualization and report automation layer.
- Continuous Integration with tests + data validation hooks.

### Future Vision
- Full-stack web app for public analytics.
- Multi-year political trend reports with poll, turnout, and engagement comparison.

---

## Version Summary Table
| Version | Date | Type | Summary |
|----------|------|------|----------|
| v0.9.0 | 2026-01-19 | ✅ Stable | Core TSE ingestion and analytics complete |
| v1.0.0 | Q1 2026 | 🚧 In Progress | Poll and Meta API integration |
| v1.1.0 | Q2 2026 | 🔜 Planned | Dashboard and automation rollout |

---

**Maintainer:** Igor Lôbo Vieira da Cunha (Shark)  
**Repository:** `voteoddsbr`  
**License:** Internal Analytics Use Only  
_© 2026 SHRK Analytics, Recife, Brazil_
