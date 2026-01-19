CREATE OR REPLACE VIEW v_dashboard_summary AS
SELECT
    candidate_label,
    total_votes,
    num_years,
    years_list,
    possible_reelection
FROM v_reelection_summary
WHERE total_votes > 0;