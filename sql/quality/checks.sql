-- Data quality checks. Each SELECT returns one row: check name, severity, failing rows.
-- severity 'error' stops the pipeline; 'warn' is reported and logged only.
SELECT 'unique_well_day' AS check_name, 'error' AS severity, COUNT(*) AS failing_rows
FROM (SELECT well, production_date FROM {{staging.daily_production}} GROUP BY 1, 2 HAVING COUNT(*) > 1)
UNION ALL
SELECT 'no_null_keys', 'error', COUNTIF(well IS NULL OR production_date IS NULL)
FROM {{staging.daily_production}}
UNION ALL
SELECT 'raw_vs_staging_row_count', 'error',
  ABS((SELECT COUNT(*) FROM {{raw.daily_production}}) - (SELECT COUNT(*) FROM {{staging.daily_production}}))
UNION ALL
SELECT 'on_stream_hours_0_to_25', 'error', COUNTIF(on_stream_hrs < 0 OR on_stream_hrs > 25)
FROM {{staging.daily_production}}
UNION ALL
SELECT 'water_cut_0_to_100', 'error', COUNTIF(NOT has_negative_volume AND (water_cut_pct < 0 OR water_cut_pct > 100))
FROM {{staging.daily_production}}
UNION ALL
SELECT 'negative_volumes', 'warn', COUNTIF(has_negative_volume)
FROM {{staging.daily_production}}
UNION ALL
SELECT 'oil_without_on_stream_hours', 'warn', COUNTIF(oil_sm3 > 0 AND on_stream_hrs = 0)
FROM {{staging.daily_production}}
UNION ALL
SELECT 'monthly_reconciliation_mismatch', 'warn', COUNTIF(status != 'match')
FROM {{marts.daily_vs_monthly_reconciliation}}
