"""Volve production pipeline: Excel -> (Cloud Storage) -> BigQuery -> SQL marts -> quality -> BigQuery ML.

    python run_pipeline.py            # full run on Google Cloud (needs .env, see README)
    python run_pipeline.py --local    # free dry run on this laptop with DuckDB
"""
import argparse
import sys
import time
import uuid

from pipeline import extract, load, quality, transform
from pipeline.config import ROOT, get_settings
from pipeline.engine import BigQueryEngine, DuckDBEngine


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--local", action="store_true", help="run on DuckDB instead of BigQuery")
    ap.add_argument("--skip-ml", action="store_true", help="skip the BigQuery ML forecast")
    args = ap.parse_args()

    s = get_settings()
    run_id = time.strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:6]
    print(f"run {run_id}  target={'duckdb (local)' if args.local else f'bigquery:{s.project} ({s.location})'}")

    extract.run()
    if args.local:
        engine = DuckDBEngine(s, ROOT / "data" / "volve_local.duckdb")
        engine.load_landing()
    else:
        load.run(s)
        engine = BigQueryEngine(s)

    transform.run(engine, with_ml=not args.local and not args.skip_ml)
    try:
        quality.run(engine, run_id)
    except quality.QualityError as e:
        print(f"STOPPED: {e}")
        return 1
    print(f"run {run_id} finished")
    return 0


if __name__ == "__main__":
    sys.exit(main())
