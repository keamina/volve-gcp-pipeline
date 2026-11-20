"""Quality: run the data checks, log every result to marts.data_quality_log,
and stop the pipeline if any 'error' check fails."""
from datetime import datetime, timezone

from .config import SQL_DIR


class QualityError(RuntimeError):
    pass


def run(engine, run_id: str) -> None:
    df = engine.query_df((SQL_DIR / "quality" / "checks.sql").read_text())
    df["failing_rows"] = df["failing_rows"].astype("int64")
    df["passed"] = df["failing_rows"] == 0
    df["run_id"] = run_id
    df["checked_at"] = datetime.now(timezone.utc)
    engine.write_df(df, "marts", "data_quality_log", append=True)

    for r in df.itertuples():
        mark = "PASS" if r.passed else ("FAIL" if r.severity == "error" else "WARN")
        print(f"quality   {mark}  {r.check_name:<34} {r.failing_rows:>5} rows  [{r.severity}]")

    failed = df[(~df["passed"]) & (df["severity"] == "error")]
    if len(failed):
        raise QualityError(f"{len(failed)} blocking check(s) failed: {', '.join(failed.check_name)}")
