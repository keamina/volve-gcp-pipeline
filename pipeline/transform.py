"""Transform: run the SQL models layer by layer (staging -> marts -> ML)."""
import time

from .config import SQL_DIR


def run_folder(engine, folder: str) -> None:
    for path in sorted((SQL_DIR / folder).glob("*.sql")):
        start = time.time()
        engine.execute(path.read_text())
        print(f"transform {folder}/{path.name:<32} ok  ({time.time() - start:.1f}s)")


def run(engine, with_ml: bool) -> None:
    run_folder(engine, "staging")
    run_folder(engine, "marts")
    if with_ml:
        run_folder(engine, "ml")
    else:
        print("transform ml/ skipped (BigQuery ML runs only on BigQuery)")
