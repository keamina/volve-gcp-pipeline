# Looker Studio dashboard

Free, at lookerstudio.google.com. Add data source → BigQuery → your project →
`volve_marts`, and add each table below as a source.

**Page 1 · Field overview**
- Scorecards from `well_summary`: total oil (SUM total_oil_sm3), producing wells (COUNT where role = producer), average water cut, average uptime.
- Time series from `field_monthly`: oil_sm3 and water_sm3 by month_start, with water_cut_pct on a second axis.

**Page 2 · Wells**
- Table from `well_summary`, sorted by total oil, with conditional colours on water cut and downtime days.
- Time series from `well_monthly`: avg_oil_rate_sm3d by month_start, broken down by well, with a well filter control.

**Page 3 · Forecast (BigQuery ML)**
- Time series from `oil_rate_actual_vs_forecast`: oil_rate_sm3d by month_start, broken down by series (actual / forecast), plus lower_bound and upper_bound, with a well filter.

**Page 4 · Data quality**
- Table from `data_quality_log`: latest run_id, check_name, severity, failing_rows, passed.
- Table from `daily_vs_monthly_reconciliation`: status counts, and the rows where status is not match.
