"""SQL engines: BigQuery (the real target) and DuckDB (a free local dry run).

The SQL files are written in BigQuery SQL and use placeholders such as
{{staging.daily_production}}. Each engine replaces them with its own table
names. The local engine translates BigQuery SQL to DuckDB with sqlglot, so the
same files can be tested on a laptop before spending anything on the cloud.
"""
import re
from pathlib import Path

import pandas as pd

from .config import LANDING_DIR, LAYERS, Settings

PLACEHOLDER = re.compile(r"\{\{\s*(\w+)\.(\w+)\s*\}\}")


class BigQueryEngine:
    name = "bigquery"

    def __init__(self, s: Settings):
        from google.cloud import bigquery

        if not s.project:
            raise SystemExit("Set GCP_PROJECT in .env (see .env.example) to run on BigQuery.")
        self.s = s
        self.client = bigquery.Client(project=s.project, location=s.location)

    def render(self, sql: str) -> str:
        def table(m):
            layer, tbl = m.group(1), m.group(2)
            return f"`{self.s.project}.{self.s.dataset(layer)}.{tbl}`"

        sql = PLACEHOLDER.sub(table, sql)
        if not self.s.partition_tables:
            sql = re.sub(r"\n\s*PARTITION BY [^\n]+", "", sql)
        return sql

    def execute(self, sql: str) -> None:
        self.client.query(self.render(sql)).result()

    def query_df(self, sql: str) -> pd.DataFrame:
        return self.client.query(self.render(sql)).to_dataframe()

    def write_df(self, df: pd.DataFrame, layer: str, table: str, append: bool = True) -> None:
        from google.cloud import bigquery

        cfg = bigquery.LoadJobConfig(
            write_disposition="WRITE_APPEND" if append else "WRITE_TRUNCATE"
        )
        table_id = f"{self.s.project}.{self.s.dataset(layer)}.{table}"
        self.client.load_table_from_dataframe(df, table_id, job_config=cfg).result()


class DuckDBEngine:
    name = "duckdb"

    def __init__(self, s: Settings, db_path: Path):
        import duckdb

        self.s = s
        self.con = duckdb.connect(str(db_path))
        for layer in LAYERS:
            self.con.execute(f"CREATE SCHEMA IF NOT EXISTS {s.dataset(layer)}")

    def load_landing(self) -> None:
        for f in sorted(LANDING_DIR.glob("*.parquet")):
            tbl = f"{self.s.dataset('raw')}.{f.stem}"
            self.con.execute(f"CREATE OR REPLACE TABLE {tbl} AS SELECT * FROM read_parquet('{f}')")
            n = self.con.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
            print(f"load      {f.stem:<20} {n:>6} rows -> duckdb {tbl}")

    def render(self, sql: str) -> str:
        import sqlglot

        sql = PLACEHOLDER.sub(lambda m: f"{self.s.dataset(m.group(1))}.{m.group(2)}", sql)
        # PARTITION BY / CLUSTER BY are BigQuery storage options with no DuckDB equivalent.
        sql = re.sub(r"\n\s*PARTITION BY [^\n]+", "", sql)
        sql = re.sub(r"\n\s*CLUSTER BY [^\n]+", "", sql)
        return ";\n".join(sqlglot.transpile(sql, read="bigquery", write="duckdb"))

    def execute(self, sql: str) -> None:
        self.con.execute(self.render(sql))

    def query_df(self, sql: str) -> pd.DataFrame:
        return self.con.execute(self.render(sql)).df()

    def write_df(self, df: pd.DataFrame, layer: str, table: str, append: bool = True) -> None:
        tbl = f"{self.s.dataset(layer)}.{table}"
        self.con.register("_df", df)
        exists = self.con.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = ? AND table_name = ?",
            [self.s.dataset(layer), table],
        ).fetchone()[0]
        if append and exists:
            self.con.execute(f"INSERT INTO {tbl} SELECT * FROM _df")
        else:
            self.con.execute(f"CREATE OR REPLACE TABLE {tbl} AS SELECT * FROM _df")
        self.con.unregister("_df")
