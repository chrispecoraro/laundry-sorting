"""File -> TinyDB. Raw rows land as typed by the operator; the filename is logged."""
import csv
import shutil

from tinydb import TinyDB

from .config import INCOMING, PROCESSED, TINYDB_PATH, MAX_PROCESSED_FILES


def extract(run_id):
    db = TinyDB(TINYDB_PATH)
    files_t, raw_t = db.table("files"), db.table("raw")

    seen = {r["filename"] for r in files_t.all()}          # already-processed files are skipped
    new_files = sorted(p for p in INCOMING.glob("*.csv") if p.name not in seen)

    for p in new_files:
        with p.open() as f:
            rows = list(csv.DictReader(f))                  # no schema forced, free text kept as-is
        raw_t.insert_multiple({**r, "_file": p.name, "_run": run_id, "_cleaned": False} for r in rows)
        files_t.insert({"filename": p.name, "rows": len(rows), "run_id": run_id})
        print(f"[extract] {p.name}: {len(rows)} rows")       # filename logged
        shutil.move(p, PROCESSED / p.name)

    for old in sorted(PROCESSED.glob("*.csv"))[:-MAX_PROCESSED_FILES]:
        old.unlink()
    return [p.name for p in new_files]
