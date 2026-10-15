"""Turn a statistical result into a visible action.

|z| > Z_THRESHOLD on the unmatched-sock mean -> a row in the actions table,
which the dashboard shows as a red banner. Nothing is sent anywhere.
"""
from .config import Z_THRESHOLD
from .runlog import conn, now
from .moe_router import ask


def act(run_id, stats):
    z = stats.get("z_latest", 0.0)
    if abs(z) <= Z_THRESHOLD:
        return None

    action = "FLAG_BATCH_FOR_RESORT" if z > 0 else "LOG_GOOD_BATCH"
    msg = ask("decide", run_id,
              f"Unmatched socks per load just hit z={z:.2f} "
              f"(threshold {Z_THRESHOLD}). Action: {action}. "
              "Write a 2-line note to whoever runs the next load.")
    with conn() as c:
        c.execute("INSERT INTO actions VALUES (?,?,?,?,?,?)",
                  (now(), run_id, "mean_unmatched", z, action, msg))
    return action
