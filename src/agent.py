"""The agent loop: generate -> extract -> clean -> load -> analyze -> act."""
import argparse
import time
import uuid

from . import generate_fake_data, extract, transform, load, analytics, actions
from .runlog import log_step, now
from .moe_router import ask


def run_once():
    run_id = uuid.uuid4().hex[:8]
    t = now(); f = generate_fake_data.generate()
    log_step(run_id, "generate", "ok", f.name, started_at=t)
    t = now(); files = extract.extract(run_id)
    log_step(run_id, "extract", "ok", ",".join(files), started_at=t)
    t = now(); df = transform.transform(run_id)
    log_step(run_id, "clean", "ok", detail=f"{len(df)} rows", started_at=t)
    t = now(); sql = load.load(df)
    log_step(run_id, "load", "ok", sql=sql, started_at=t)
    t = now(); stats = analytics.analyze(run_id)
    log_step(run_id, "analyze", "ok", sql=analytics.BATCH_SQL, detail=str(stats), started_at=t)
    ask("analyze", run_id,
        f"Summarize these laundry sorting stats in 3 sentences: {stats}")
    t = now(); a = actions.act(run_id, stats)
    log_step(run_id, "act", "triggered" if a else "none", detail=a, started_at=t)
    print(f"[agent] run {run_id} done; {len(df)} clean rows; action={a}")


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
