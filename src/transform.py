"""TinyDB raw rows -> clean, typed rows.

Fixes mixed date formats, five spellings of each machine, blank fields and
typo'd sock counts; then the Haiku expert tags the free-text operator notes.
"""
import re
import json

import pandas as pd
from tinydb import TinyDB, Query

from .config import TINYDB_PATH
from .moe_router import ask
from .jev_client import choose

MAX_PLAUSIBLE_SOCKS = 60      # one household load; 170 means a stray zero
DEFECTS = ["none", "faded", "torn", "missing_sock", "wear", "other"]
MACHINE_MAP = {
    "washer 1": "Washer 1", "washer1": "Washer 1",
    "washer 2": "Washer 2", "washer2": "Washer 2",
    "dryer a": "Dryer A", "dryera": "Dryer A",
}


def _num(v):
    m = re.search(r"[\d.]+", v or "")
    return float(m.group()) if m else None


def transform(run_id):
    db = TinyDB(TINYDB_PATH)
    raw = db.table("raw")
    Q = Query()
    rows = raw.search(Q._cleaned == False)   # noqa: E712 -- TinyDB needs ==
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["ts"] = pd.to_datetime(df["ts"], format="mixed", errors="coerce")
    df["machine"] = df["machine"].str.strip().str.lower().map(MACHINE_MAP).fillna("Unknown")
    df["socks_in"] = df["socks_in"].map(_num)
    df["pairs_out"] = df["pairs_out"].map(_num)

    # Clean the outliers BEFORE averaging: one stray zero would swamp the batch mean.
    df.loc[df["socks_in"] > MAX_PLAUSIBLE_SOCKS, "socks_in"] = None
    df["socks_in"] = df["socks_in"].fillna(df["socks_in"].median())
    df["pairs_out"] = df["pairs_out"].fillna(df["pairs_out"].median())

    # The metric: socks that went in without a partner coming out.
    df["unmatched_socks"] = (df["socks_in"] - 2 * df["pairs_out"]).clip(lower=0)

    df = df.dropna(subset=["ts"]).drop_duplicates(subset=["ts", "machine", "load"])

    # System 1 (Jev) routes the note-tagging job to an expert before System 2 does it.
    sample = " | ".join(n for n in df["notes"].fillna("") if n)[:400]
    route = choose(run_id, "Which expert should tag these laundry notes?", sample,
                   ["clean", "analyze", "decide"])
    expert = route["choice"] if route.get("confidence", 0) >= 0.5 else "clean"

    # Haiku expert reads every operator note in ONE batched call.
    notes = df["notes"].fillna("").tolist()
    reply = ask(expert, run_id,
                'For each laundry note return a JSON list of {"defect": '
                + "|".join(DEFECTS) + ', "severity": low|medium|high}. '
                "Same length as the input, same order. Only JSON.\n" + json.dumps(notes))
    try:
        tags = json.loads(reply)
        assert len(tags) == len(notes)
    except (json.JSONDecodeError, AssertionError):
        tags = [{"defect": "none", "severity": "low"}] * len(notes)   # dry-run / bad JSON
    df["defect"] = [t.get("defect", "none") for t in tags]
    df["severity"] = [t.get("severity", "low") for t in tags]

    raw.update({"_cleaned": True}, Q._cleaned == False)   # noqa: E712
    df["source_file"] = df["_file"]
    df["load_id"] = df["load"]
    df["run_id"] = run_id
    return df[["ts", "machine", "load_id", "socks_in", "pairs_out", "unmatched_socks",
               "notes", "defect", "severity", "source_file", "run_id"]]
