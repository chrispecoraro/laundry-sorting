"""Turn a statistical result into a visible action.

Two decisions, two systems:
  System 1 (Jev)    -- fast + typed: is this batch worth flagging at all?
  System 2 (Claude) -- slow + wordy: write the note a human will read.

|z| > Z_THRESHOLD writes a row to the actions table, which the dashboard shows
as a red banner. Nothing is sent anywhere.
"""
from .config import Z_THRESHOLD
from .runlog import conn, now
from .moe_router import ask
from .jev_client import yes_no

ACT_AT = 0.90    # confidence needed to act without a human in the loop


def act(run_id, stats):
    z = stats.get("z_latest", 0.0)
    if abs(z) <= Z_THRESHOLD:
        return None

    action = "FLAG_BATCH_FOR_RESORT" if z > 0 else "LOG_GOOD_BATCH"
    d = yes_no(run_id, f"Should the household {action}?",
               f"Unmatched socks per load, z-score = {z:.2f}; threshold {Z_THRESHOLD}")
    if d["p_yes"] < ACT_AT:
        action = "ESCALATE_TO_HUMAN"          # not confident enough -> a person decides

    msg = ask("decide", run_id,
              f"Unmatched socks per load just hit z={z:.2f} (threshold {Z_THRESHOLD}). "
              f"Action: {action} (Jev p_yes={d['p_yes']:.2f}). "
              "Write a 2-line note to whoever runs the next load.")
    with conn() as c:
        c.execute("INSERT INTO actions VALUES (?,?,?,?,?,?)",
                  (now(), run_id, "mean_unmatched", z, action, msg))
    return action
