"""Paths and tunable constants for the Sock & Garment Sorting Pulse pipeline."""
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
INCOMING = ROOT / "data" / "incoming"
PROCESSED = ROOT / "data" / "processed"
TINYDB_PATH = ROOT / "db" / "raw_tinydb.json"
SQLITE_PATH = ROOT / "db" / "clean.sqlite"

# A batch whose mean unmatched-sock count is this many standard deviations
# away from history is abnormal.
Z_THRESHOLD = 2.0

# Keep the repo small: the GitHub Action commits the DB every 5 minutes.
MAX_ROWS = 2000
MAX_PROCESSED_FILES = 50

for p in (INCOMING, PROCESSED, SQLITE_PATH.parent):
    p.mkdir(parents=True, exist_ok=True)
