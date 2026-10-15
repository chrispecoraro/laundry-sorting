"""Clean rows -> SQLite. The SQL used is returned so the dashboard can show it."""
from .runlog import conn
from .config import MAX_ROWS

INSERT_SQL = ("INSERT INTO records (ts, machine, load_id, socks_in, pairs_out, unmatched_socks, "
              "notes, defect, severity, source_file, run_id) VALUES (?,?,?,?,?,?,?,?,?,?,?)")
TRIM_SQL = (f"DELETE FROM records WHERE rowid NOT IN "
            f"(SELECT rowid FROM records ORDER BY rowid DESC LIMIT {MAX_ROWS})")


def load(df):
    if df.empty:
        return INSERT_SQL
    df = df.assign(ts=df["ts"].astype(str))
    with conn() as c:
        c.executemany(INSERT_SQL, df.itertuples(index=False, name=None))
        c.execute(TRIM_SQL)
    return INSERT_SQL      # logged in pipeline_runs.sql -> shown on the dashboard
