"""Render the README charts straight from the BigQuery marts (or the local DuckDB run).

    python make_charts.py           # from BigQuery
    python make_charts.py --local   # from data/volve_local.duckdb
"""
import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from pipeline.config import ROOT, get_settings
from pipeline.engine import BigQueryEngine, DuckDBEngine

OUT = ROOT / "docs" / "img"
OIL, WATER, FORECAST, BAND, INK, MUTED = "#1f6f8b", "#e07a2f", "#c2185b", "#f3c1d6", "#222222", "#777777"

plt.rcParams.update({
    "font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": "#bbbbbb", "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.grid": True, "grid.color": "#eeeeee", "grid.linewidth": 0.8, "figure.dpi": 150,
})


def field_chart(engine) -> Path:
    df = engine.query_df("SELECT * FROM {{marts.field_monthly}} ORDER BY month_start")
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(df.month_start, df.oil_sm3 / 1000, color=OIL, lw=1.8, label="Oil")
    ax.plot(df.month_start, df.water_sm3 / 1000, color=WATER, lw=1.8, label="Water")
    ax.set_ylabel("Thousand Sm³ per month")
    ax.set_title("Volve field: monthly oil and water production, 2008–2016", loc="left", color=INK, fontsize=12)
    ax.legend(frameon=False, loc="upper right")
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    fig.text(0.01, 0.01, "Source: Equinor Volve Data Village (Equinor Open Data Licence). Mart: volve_marts.field_monthly",
             fontsize=7, color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    path = OUT / "field_monthly.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def forecast_chart(engine) -> Path:
    df = engine.query_df(
        "SELECT * FROM {{marts.oil_rate_actual_vs_forecast}} "
        "WHERE well IN ('F-11 H', 'F-12 H', 'F-15 D') ORDER BY well, month_start"
    )
    wells = ["F-12 H", "F-11 H", "F-15 D"]
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.6), sharey=False)
    for ax, well in zip(axes, wells):
        d = df[df.well == well]
        a, f = d[d.series == "actual"], d[d.series == "forecast"]
        ax.plot(a.month_start, a.oil_rate_sm3d, color=OIL, lw=1.5, label="Actual")
        ax.fill_between(f.month_start, f.lower_bound, f.upper_bound, color=BAND, alpha=0.7, lw=0, label="90 % interval")
        ax.plot(f.month_start, f.oil_rate_sm3d, color=FORECAST, lw=1.8, label="Forecast")
        ax.set_title(well, loc="left", color=INK, fontsize=11)
        ax.xaxis.set_major_locator(mdates.YearLocator(base=2))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    axes[0].set_ylabel("Average oil rate, Sm³/day")
    axes[0].legend(frameon=False, fontsize=8, loc="upper right")
    fig.suptitle("BigQuery ML (ARIMA_PLUS): 12-month oil rate forecast per well", x=0.01, ha="left", color=INK, fontsize=12)
    fig.text(0.01, 0.01, "Model: volve_marts.oil_rate_arima. Table: volve_marts.oil_rate_actual_vs_forecast",
             fontsize=7, color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    path = OUT / "oil_rate_forecast.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--local", action="store_true")
    args = ap.parse_args()
    s = get_settings()
    engine = DuckDBEngine(s, ROOT / "data" / "volve_local.duckdb") if args.local else BigQueryEngine(s)
    OUT.mkdir(parents=True, exist_ok=True)
    print(field_chart(engine))
    if not args.local:
        print(forecast_chart(engine))


if __name__ == "__main__":
    main()
