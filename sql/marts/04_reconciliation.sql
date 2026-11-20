-- Mart: daily data summed per month vs the official monthly report, per wellbore.
-- status = match when the oil difference is within 0.5 % (or 1 Sm3).
CREATE OR REPLACE TABLE {{marts.daily_vs_monthly_reconciliation}} AS
WITH daily AS (
  SELECT
    npd_wellbore_code,
    MIN(well)                              AS well,
    DATE_TRUNC(production_date, MONTH)     AS month_start,
    SUM(oil_sm3)                           AS daily_oil_sm3,
    SUM(gas_sm3)                           AS daily_gas_sm3,
    SUM(water_sm3)                         AS daily_water_sm3
  FROM {{staging.daily_production}}
  GROUP BY npd_wellbore_code, month_start
),
joined AS (
  SELECT
    COALESCE(d.month_start, m.month_start)             AS month_start,
    COALESCE(d.npd_wellbore_code, m.npd_wellbore_code) AS npd_wellbore_code,
    COALESCE(d.well, m.wellbore_name)                  AS well,
    m.oil_sm3                                          AS reported_oil_sm3,
    d.daily_oil_sm3,
    d.daily_oil_sm3 - m.oil_sm3                        AS oil_diff_sm3,
    m.water_sm3                                        AS reported_water_sm3,
    d.daily_water_sm3,
    d.npd_wellbore_code IS NULL                        AS missing_daily,
    m.npd_wellbore_code IS NULL                        AS missing_monthly
  FROM daily AS d
  FULL OUTER JOIN {{staging.monthly_production}} AS m
    ON d.npd_wellbore_code = m.npd_wellbore_code AND d.month_start = m.month_start
)
SELECT
  *,
  ROUND(SAFE_DIVIDE(ABS(oil_diff_sm3), reported_oil_sm3) * 100, 3) AS oil_diff_pct,
  CASE
    WHEN missing_daily THEN 'missing_daily'
    WHEN missing_monthly THEN 'missing_monthly'
    WHEN ABS(oil_diff_sm3) <= GREATEST(1, 0.005 * ABS(reported_oil_sm3)) THEN 'match'
    ELSE 'mismatch'
  END AS status
FROM joined;
