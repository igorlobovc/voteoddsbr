CREATE OR REPLACE VIEW v_dashboard_summary AS
SELECT
    vrs.race_id,
    SPLIT_PART(vrs.race_id, '-', 1) AS year,
    SPLIT_PART(vrs.race_id, '-', 2) AS office,
    SPLIT_PART(vrs.race_id, '-', 3) AS state,
    SPLIT_PART(vrs.race_id, '-', 4) AS round,
    vrs.total_votes,
    vrs.num_candidates,
    vrs.num_candidates > 1 AS possible_reelection
FROM v_reelection_summary AS vrs
ORDER BY vrs.total_votes DESC;
