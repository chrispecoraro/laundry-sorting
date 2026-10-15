"""Three analytics methods over the unmatched-sock metric.

Each returns (name, value, LaTeX formula, SQL) so the dashboard can show the
number, the formula behind it, and the query that fed it.
"""
import numpy as np
import pandas as pd

from .runlog import conn, now

# Order by load order, NOT by ts: the fake timestamps are minute-truncated, so
# sorting by time scrambles batches and the z-score compares the wrong "latest".
BATCH_SQL = ("SELECT run_id, AVG(unmatched_socks) AS mean_unmatched, MAX(ts) AS ts "
             "FROM records GROUP BY run_id ORDER BY MIN(rowid)")


def analyze(run_id):
    with conn() as c:
        batches = pd.read_sql(BATCH_SQL, c)
    y = batches["mean_unmatched"].to_numpy()
    out = []

    # Method 1 -- descriptive
    mu = float(np.mean(y)) if len(y) else 0.0
    sd = float(np.std(y, ddof=1)) if len(y) > 1 else 0.0
    out.append(("mean_unmatched", mu, r"\bar{x}=\frac{1}{n}\sum_{i=1}^{n}x_i", BATCH_SQL))
    out.append(("std_dev", sd, r"s=\sqrt{\frac{1}{n-1}\sum(x_i-\bar{x})^2}", BATCH_SQL))

    # Method 2 -- trend: least-squares slope across batches
    if len(y) > 2:
        x = np.arange(len(y))
        slope = float(np.polyfit(x, y, 1)[0])
        out.append(("trend_slope", slope,
                    r"\beta_1=\frac{\sum(x_i-\bar{x})(y_i-\bar{y})}{\sum(x_i-\bar{x})^2}", BATCH_SQL))

    # Method 3 -- anomaly: z-score of the latest batch against its own history
    z = 0.0
    if len(y) > 3:
        hist = y[:-1]
        z = float((y[-1] - hist.mean()) / (hist.std(ddof=1) or 1))
    out.append(("z_latest", z, r"z=\frac{x_{latest}-\bar{x}_{hist}}{s_{hist}}", BATCH_SQL))

    with conn() as c:
        c.executemany("INSERT INTO stats VALUES (?,?,?,?,?)",
                      [(now(), run_id, n, v, f) for n, v, f, _ in out])
    return {n: v for n, v, _, _ in out}
