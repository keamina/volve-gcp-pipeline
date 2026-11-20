-- Mart: field totals per month (whole Volve field).
CREATE OR REPLACE TABLE {{marts.field_monthly}} AS
SELECT
  DATE_TRUNC(production_date, MONTH)                           AS month_start,
  ROUND(SUM(oil_sm3), 2)                                       AS oil_sm3,
  ROUND(SUM(gas_sm3), 2)                                       AS gas_sm3,
  ROUND(SUM(water_sm3), 2)                                     AS water_sm3,
  ROUND(SUM(water_injected_sm3), 2)                            AS water_injected_sm3,
  ROUND(SAFE_DIVIDE(SUM(water_sm3), SUM(oil_sm3) + SUM(water_sm3)) * 100, 2) AS water_cut_pct,
  COUNT(DISTINCT IF(oil_sm3 > 0, well, NULL))                  AS producing_wells,
  ROUND(SUM(oil_sm3) / COUNT(DISTINCT production_date), 2)     AS avg_daily_oil_sm3d
FROM {{staging.daily_production}}
GROUP BY month_start;
