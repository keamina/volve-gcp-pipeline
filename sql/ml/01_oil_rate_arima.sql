-- BigQuery ML: one ARIMA_PLUS time-series model per producing well (monthly average oil rate).
-- BigQuery only (skipped in --local mode).
CREATE OR REPLACE MODEL {{marts.oil_rate_arima}}
OPTIONS (
  model_type = 'ARIMA_PLUS',
  time_series_timestamp_col = 'month_start',
  time_series_data_col = 'avg_oil_rate_sm3d',
  time_series_id_col = 'well',
  data_frequency = 'MONTHLY',
  horizon = 12,
  auto_arima = TRUE
) AS
SELECT well, month_start, avg_oil_rate_sm3d
FROM {{marts.well_monthly}}
WHERE avg_oil_rate_sm3d IS NOT NULL
  AND well IN (SELECT well FROM {{marts.well_summary}} WHERE role = 'producer');
