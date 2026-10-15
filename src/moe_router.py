"""App-level Mixture of Experts: each task goes to the cheapest model that does it well.

This is a router over models, NOT the MoE inside a single model. Every call is
logged to model_calls so the dashboard can show who did what, when, for how much.
"""
import os
import time

from .runlog import conn, now

EXPERTS = {
    "clean":   "claude-haiku-5-5",    # fast + cheap: tag a batch of operator notes
    "analyze": "claude-sonnet-5-5",   # explain the stats in plain English
    "decide":  "claude-opus-5-5",     # high-stakes: word the alert to the household
}


def ask(task, run_id, prompt, max_tokens=1024):
    model = EXPERTS[task]
    t0 = time.time()
    dry = not os.getenv("ANTHROPIC_API_KEY")
    if dry:
        text, tin, tout = f"[dry-run: {model} would answer here]", 0, 0
    else:
        import anthropic
        msg = anthropic.Anthropic().messages.create(
            model=model, max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}])
        text = "".join(b.text for b in msg.content if b.type == "text")
        tin, tout = msg.usage.input_tokens, msg.usage.output_tokens
    with conn() as c:
        c.execute("INSERT INTO model_calls VALUES (?,?,?,?,?,?,?,?)",
                  (now(), run_id, task, model, tin, tout, round(time.time() - t0, 2), int(dry)))
    return text
