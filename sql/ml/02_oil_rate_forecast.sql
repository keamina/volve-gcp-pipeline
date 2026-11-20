-- Actuals + 12-month forecast with a 90 % interval, in one table for the dashboard.
CREATE OR REPLACE TABLE {{marts.oil_rate_actual_vs_forecast}} AS
SELECT well, month_start, 'actual' AS series, avg_oil_rate_sm3d AS oil_rate_sm3d,
       CAST(NULL AS FLOAT64) AS lower_bound, CAST(NULL AS FLOAT64) AS upper_bound
FROM {{marts.well_monthly}}
WHERE avg_oil_rate_sm3d IS NOT NULL
  AND well IN (SELECT well FROM {{marts.well_summary}} WHERE role = 'producer')
UNION ALL
SELECT well, DATE(forecast_timestamp), 'forecast', GREATEST(forecast_value, 0),
       GREATEST(prediction_interval_lower_bound, 0), prediction_interval_upper_bound
FROM ML.FORECAST(MODEL {{marts.oil_rate_arima}}, STRUCT(12 AS horizon, 0.9 AS confidence_level));
