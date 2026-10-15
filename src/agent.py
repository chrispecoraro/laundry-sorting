"""The agent loop: generate -> extract (more steps land in later milestones)."""
import argparse
import time
import uuid

from . import generate_fake_data, extract
from .runlog import log_step, now


def run_once():
    run_id = uuid.uuid4().hex[:8]
    t = now(); f = generate_fake_data.generate()
    log_step(run_id, "generate", "ok", f.name, started_at=t)
    t = now(); files = extract.extract(run_id)
    log_step(run_id, "extract", "ok", ",".join(files), started_at=t)
    print(f"[agent] run {run_id} done")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=60)
    ap.add_argument("--iterations", type=int, default=0, help="0 = forever")
    args = ap.parse_args()
    i = 0
    while True:
        run_once()
        i += 1
        if args.iterations and i >= args.iterations:
            break
        time.sleep(args.interval)
