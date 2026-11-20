-- Mart: lifetime KPIs per well (one row per well).
CREATE OR REPLACE TABLE {{marts.well_summary}} AS
SELECT
  well,
  IF(LOGICAL_OR(is_producer AND oil_sm3 > 0), 'producer', 'injector') AS role,
  MIN(production_date)                                   AS first_date,
  MAX(production_date)                                   AS last_date,
  COUNTIF(on_stream_hrs > 0)                             AS days_on_stream,
  ROUND(SUM(oil_sm3), 2)                                 AS total_oil_sm3,
  ROUND(SUM(gas_sm3), 2)                                 AS total_gas_sm3,
  ROUND(SUM(water_sm3), 2)                               AS total_water_sm3,
  ROUND(SUM(water_injected_sm3), 2)                      AS total_water_injected_sm3,
  ROUND(AVG(IF(oil_sm3 > 0, water_cut_pct, NULL)), 2)    AS avg_water_cut_pct,
  ROUND(AVG(IF(oil_sm3 > 0, gor_sm3_sm3, NULL)), 2)      AS avg_gor_sm3_sm3,
  ROUND(AVG(uptime_pct), 2)                              AS avg_uptime_pct,
  COUNTIF(is_downtime_day)                               AS downtime_days,
  ROUND(MAX(oil_sm3), 2)                                 AS peak_oil_rate_sm3d
FROM {{staging.daily_production}}
GROUP BY well;
