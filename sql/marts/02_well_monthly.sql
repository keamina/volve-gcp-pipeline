-- Mart: one row per well per month. Feeds the dashboard and the BigQuery ML forecast.
CREATE OR REPLACE TABLE {{marts.well_monthly}} AS
SELECT
  well,
  DATE_TRUNC(production_date, MONTH)                           AS month_start,
  ROUND(SUM(oil_sm3), 2)                                       AS oil_sm3,
  ROUND(SUM(gas_sm3), 2)                                       AS gas_sm3,
  ROUND(SUM(water_sm3), 2)                                     AS water_sm3,
  ROUND(SUM(water_injected_sm3), 2)                            AS water_injected_sm3,
  COUNTIF(oil_sm3 > 0)                                         AS producing_days,
  ROUND(SAFE_DIVIDE(SUM(oil_sm3), COUNTIF(oil_sm3 > 0)), 2)    AS avg_oil_rate_sm3d,
  ROUND(SAFE_DIVIDE(SUM(water_sm3), SUM(oil_sm3) + SUM(water_sm3)) * 100, 2) AS water_cut_pct,
  ROUND(AVG(uptime_pct), 2)                                    AS avg_uptime_pct
FROM {{staging.daily_production}}
WHERE flow_kind = 'production'
GROUP BY well, month_start;
