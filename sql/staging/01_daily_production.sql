-- Staging: one clean, typed row per wellbore per day.
-- Business rules live here (not in the extract step), so they are versioned and reviewable:
--   * missing volumes and hours count as 0 (no meter reading = no flow that day)
--   * a pressure of exactly 0 means "no reading", so it becomes NULL
--   * KPIs: water cut, GOR, uptime, downtime flag, cumulative volumes per well
--   * negative volumes are kept as reported but flagged for the quality checks
CREATE OR REPLACE TABLE {{staging.daily_production}}
PARTITION BY DATE_TRUNC(production_date, MONTH)
CLUSTER BY well
AS
WITH typed AS (
  SELECT
    CAST(dateprd AS DATE)                                AS production_date,
    TRIM(REPLACE(well_bore_code, 'NO 15/9-', ''))        AS well,
    npd_well_bore_code                                   AS npd_wellbore_code,
    npd_field_name                                       AS field,
    LOWER(flow_kind)                                     AS flow_kind,
    well_type,
    COALESCE(CAST(on_stream_hrs AS FLOAT64), 0)          AS on_stream_hrs,
    NULLIF(CAST(avg_downhole_pressure AS FLOAT64), 0)    AS downhole_pressure_bar,
    NULLIF(CAST(avg_whp_p AS FLOAT64), 0)                AS wellhead_pressure_bar,
    CAST(avg_choke_size_p AS FLOAT64)                    AS choke_size_pct,
    COALESCE(CAST(bore_oil_vol AS FLOAT64), 0)           AS oil_sm3,
    COALESCE(CAST(bore_gas_vol AS FLOAT64), 0)           AS gas_sm3,
    COALESCE(CAST(bore_wat_vol AS FLOAT64), 0)           AS water_sm3,
    COALESCE(CAST(bore_wi_vol AS FLOAT64), 0)            AS water_injected_sm3
  FROM {{raw.daily_production}}
)
SELECT
  *,
  well_type = 'OP'                                                     AS is_producer,
  ROUND(LEAST(on_stream_hrs / 24, 1) * 100, 2)                         AS uptime_pct,
  (well_type = 'OP' AND flow_kind = 'production' AND on_stream_hrs < 24) AS is_downtime_day,
  (oil_sm3 < 0 OR gas_sm3 < 0 OR water_sm3 < 0)                        AS has_negative_volume,
  SAFE_DIVIDE(water_sm3, oil_sm3 + water_sm3) * 100                    AS water_cut_pct,
  SAFE_DIVIDE(gas_sm3, oil_sm3)                                        AS gor_sm3_sm3,
  SUM(oil_sm3)   OVER w                                                AS cum_oil_sm3,
  SUM(gas_sm3)   OVER w                                                AS cum_gas_sm3,
  SUM(water_sm3) OVER w                                                AS cum_water_sm3
FROM typed
WINDOW w AS (PARTITION BY well ORDER BY production_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW);
