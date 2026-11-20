-- Staging: official monthly volumes per wellbore, as reported to the authorities.
-- Used only to reconcile the daily data (see marts/04_reconciliation.sql).
CREATE OR REPLACE TABLE {{staging.monthly_production}} AS
SELECT
  DATE(year, month, 1)                         AS month_start,
  npdcode                                      AS npd_wellbore_code,
  TRIM(REPLACE(wellbore_name, '15/9-', ''))    AS wellbore_name,
  COALESCE(on_stream, 0)                       AS on_stream_hrs,
  COALESCE(oil, 0)                             AS oil_sm3,
  COALESCE(gas, 0)                             AS gas_sm3,
  COALESCE(water, 0)                           AS water_sm3,
  COALESCE(gi, 0)                              AS gas_injected_sm3,
  COALESCE(wi, 0)                              AS water_injected_sm3
FROM {{raw.monthly_production}}
WHERE year IS NOT NULL AND month IS NOT NULL;
