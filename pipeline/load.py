"""Load: put the landed Parquet files into the BigQuery raw layer.

With GCS_BUCKET set, files are first uploaded to Cloud Storage
(gs://<bucket>/landing/volve/ingest_date=YYYY-MM-DD/) and BigQuery loads them
from there, which is the usual production pattern. Without a bucket (for
example in the free BigQuery sandbox), BigQuery loads the local files directly.
"""
from datetime import date

from google.cloud import bigquery

from .config import LANDING_DIR, Settings

TABLES = ("daily_production", "monthly_production")


def ensure_datasets(client: bigquery.Client, s: Settings) -> None:
    for layer in ("raw", "staging", "marts"):
        ds = bigquery.Dataset(f"{s.project}.{s.dataset(layer)}")
        ds.location = s.location
        ds.description = f"Volve production pipeline, {layer} layer"
        client.create_dataset(ds, exists_ok=True)


def _upload_to_gcs(s: Settings, name: str) -> str:
    from google.cloud import storage

    blob_path = f"landing/volve/ingest_date={date.today().isoformat()}/{name}.parquet"
    storage.Client(project=s.project).bucket(s.bucket).blob(blob_path).upload_from_filename(
        LANDING_DIR / f"{name}.parquet"
    )
    return f"gs://{s.bucket}/{blob_path}"


def run(s: Settings) -> None:
    client = bigquery.Client(project=s.project, location=s.location)
    ensure_datasets(client, s)
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    for name in TABLES:
        table_id = f"{s.project}.{s.dataset('raw')}.{name}"
        if s.bucket:
            uri = _upload_to_gcs(s, name)
            job = client.load_table_from_uri(uri, table_id, job_config=job_config)
            source = uri
        else:
            with open(LANDING_DIR / f"{name}.parquet", "rb") as fh:
                job = client.load_table_from_file(fh, table_id, job_config=job_config)
            source = "local file"
        job.result()
        rows = client.get_table(table_id).num_rows
        print(f"load      {name:<20} {rows:>6} rows -> {table_id}  (from {source})")
