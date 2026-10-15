"""SQLite schema + step logging. pipeline_runs drives the live flow chart."""
import sqlite3
import datetime as dt

from .config import SQLITE_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS pipeline_runs(run_id TEXT, step TEXT, status TEXT, filename TEXT,
  sql TEXT, detail TEXT, started_at TEXT, finished_at TEXT);
CREATE TABLE IF NOT EXISTS model_calls(ts TEXT, run_id TEXT, task TEXT, model TEXT,
  input_tokens INT, output_tokens INT, latency_s REAL, dry_run INT);
CREATE TABLE IF NOT EXISTS actions(ts TEXT, run_id TEXT, metric TEXT, z REAL, action TEXT, message TEXT);
CREATE TABLE IF NOT EXISTS stats(ts TEXT, run_id TEXT, method TEXT, value REAL, formula TEXT);
CREATE TABLE IF NOT EXISTS records(ts TEXT, machine TEXT, load_id TEXT, socks_in REAL,
  pairs_out REAL, unmatched_socks REAL, notes TEXT, defect TEXT, severity TEXT,
  source_file TEXT, run_id TEXT);
"""


def conn():
    c = sqlite3.connect(SQLITE_PATH)
    c.executescript(SCHEMA)
    return c


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def log_step(run_id, step, status, filename=None, sql=None, detail=None, started_at=None):
    with conn() as c:
        c.execute("INSERT INTO pipeline_runs VALUES (?,?,?,?,?,?,?,?)",
                  (run_id, step, status, filename, sql, detail, started_at or now(), now()))
