"""Extract: read the Equinor Volve export (Excel) and land it as Parquet files.

The landing step keeps the data as close to the source as possible: same
columns, same values. The only changes are technical: column names are made
BigQuery-safe, the units row of the monthly sheet is dropped, and two audit
columns are added (source file and extraction time). Every business rule
(renaming, null handling, KPIs) lives in SQL, in the staging layer.
"""
import re
from datetime import datetime, timezone

import pandas as pd

from .config import LANDING_DIR, RAW_XLSX


def _safe_name(col: str) -> str:
    return re.sub(r"[^0-9a-zA-Z]+", "_", str(col)).strip("_").lower()


def _add_audit(df: pd.DataFrame) -> pd.DataFrame:
    df["_source_file"] = RAW_XLSX.name
    df["_extracted_at"] = datetime.now(timezone.utc)
    return df


def extract_daily() -> pd.DataFrame:
    df = pd.read_excel(RAW_XLSX, sheet_name="Daily Production Data")
    df.columns = [_safe_name(c) for c in df.columns]
    df["dateprd"] = pd.to_datetime(df["dateprd"]).dt.date
    return _add_audit(df)


def extract_monthly() -> pd.DataFrame:
    """Official monthly volumes reported per wellbore (used to reconcile the daily data)."""
    df = pd.read_excel(RAW_XLSX, sheet_name="Monthly Production Data")
    df = df[df["Wellbore name"].notna()].copy()  # first row only holds the units (hrs, Sm3)
    df.columns = [_safe_name(c) for c in df.columns]
    for col in ["npdcode", "year", "month", "on_stream", "oil", "gas", "water", "gi", "wi"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ["npdcode", "year", "month"]:
        df[col] = df[col].astype("Int64")
    return _add_audit(df)


def run() -> dict[str, "pd.DataFrame"]:
    LANDING_DIR.mkdir(parents=True, exist_ok=True)
    tables = {"daily_production": extract_daily(), "monthly_production": extract_monthly()}
    for name, df in tables.items():
        path = LANDING_DIR / f"{name}.parquet"
        df.to_parquet(path, index=False)
        print(f"extract   {name:<20} {len(df):>6} rows -> {path.relative_to(LANDING_DIR.parent.parent)}")
    return tables
