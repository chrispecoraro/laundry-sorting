"""Write one messy laundry-sorting file per cycle.

Messy on purpose: mixed date formats, machine names typed five different ways,
blank fields, free-text operator notes, and typo'd sock counts (a stray zero).
"""
import csv
import random
import uuid
import datetime as dt

from .config import INCOMING

MACHINES = ["Washer 1", "washer1", "WASHER 1", "Dryer A", "dryer a", "Washer 2", "washer 2"]
DATE_FMTS = ["%Y-%m-%d %H:%M", "%m/%d/%Y %I:%M %p", "%Y-%m-%dT%H:%M:%S"]
NOTES = [
    "left sock gone again??",
    "red tee faded bad",
    "small tear on the sleeve",
    "all good",
    "",
    "two blacks came out grey",
    "kid's sock stuck in the drum",
    "towel snagged, loose thread",
    "smells fine, nothing weird",
    "collar looks worn out",
    "one of the striped pair missing!!",
]


def generate(n=None, spike=None):
    """One file = one sorted batch of loads. ~15% of batches go bad."""
    n = n or random.randint(8, 20)
    spike = random.random() < 0.12 if spike is None else spike
    stamp = dt.datetime.now()
    path = INCOMING / f"loads_{stamp:%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:4]}.csv"

    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ts", "machine", "load", "socks_in", "pairs_out", "notes"])
        for i in range(n):
            pairs = random.randint(3, 12)
            unmatched = max(0, round(random.gauss(8.0 if spike else 0.8, 1.2)))
            socks = 2 * pairs + unmatched

            # data entry is human: stray zero, unit tacked on, or just blank
            roll = random.random()
            if roll < 0.08:
                socks_s = str(socks * 10)        # typo: 14 -> 140
            elif roll < 0.25:
                socks_s = f"{socks} socks"
            elif roll < 0.30:
                socks_s = ""
            else:
                socks_s = str(socks)

            w.writerow([
                stamp.strftime(random.choice(DATE_FMTS)),
                random.choice(MACHINES),
                f"L{stamp:%H%M}{i:02d}",
                socks_s,
                random.choice([str(pairs), str(pairs), ""]),
                random.choice(NOTES),
            ])
    return path
