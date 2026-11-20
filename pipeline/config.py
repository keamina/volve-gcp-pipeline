"""Pipeline settings, read from environment variables (or a local .env file)."""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

RAW_XLSX = ROOT / "data" / "raw" / "volve_production_data.xlsx"
LANDING_DIR = ROOT / "data" / "landing"
SQL_DIR = ROOT / "sql"

# Logical dataset names used in the SQL files as {{raw.table}}, {{staging.table}}, ...
LAYERS = ("raw", "staging", "marts")


@dataclass(frozen=True)
class Settings:
    project: str | None
    location: str
    bucket: str | None
    dataset_prefix: str
    partition_tables: bool

    def dataset(self, layer: str) -> str:
        return f"{self.dataset_prefix}_{layer}"


def get_settings() -> Settings:
    return Settings(
        project=os.getenv("GCP_PROJECT") or None,
        location=os.getenv("BQ_LOCATION", "EU"),
        bucket=os.getenv("GCS_BUCKET") or None,
        dataset_prefix=os.getenv("DATASET_PREFIX", "volve"),
        # The free BigQuery sandbox expires partitions older than 60 days, which would empty
        # a table of 2008-2016 data. Set PARTITION_TABLES=false there (clustering still applies).
        partition_tables=os.getenv("PARTITION_TABLES", "true").lower() != "false",
    )
