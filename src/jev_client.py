"""System 1 decisions: fast, typed, with a confidence number attached.

Jev (TypeSafe AI) is a native System 1 decision model -- waitlist only, so this
client uses it when JEV_API_KEY is set and otherwise falls back to Claude Haiku
with the same JSON contract.

The fallback's confidence is a GUESS, not a calibrated probability. Jev's RLCD
training is what makes 0.90 actually mean "right 9 times out of 10".
"""
import os
import json

import requests

from .moe_router import ask


def _jev(payload):
    r = requests.post(os.environ["JEV_API_URL"], json=payload, timeout=10,
                      headers={"Authorization": f"Bearer {os.environ['JEV_API_KEY']}"})
    r.raise_for_status()
    return r.json()


def choose(run_id, question, text, options):
    """Jev Choice -> {"choice": str, "confidence": float}"""
    if os.getenv("JEV_API_KEY"):
        return _jev({"state": {"text": text},
                     "questions": [{"type": "choice", "question": question, "options": options}]})
    reply = ask("clean", run_id,
                f"{question}\nInput: {text}\nPick ONE of {options}. "
                'Reply only JSON: {"choice": ..., "confidence": 0-1}')
    try:
        out = json.loads(reply)
        if out.get("choice") in options:
            return out
    except json.JSONDecodeError:
        pass
    return {"choice": options[0], "confidence": 0.0}      # dry-run / bad reply


def yes_no(run_id, question, text):
    """Jev Noul -> {"p_yes": float}"""
    if os.getenv("JEV_API_KEY"):
        return _jev({"state": {"text": text},
                     "questions": [{"type": "yes_no", "question": question}]})
    out = choose(run_id, question, text, ["yes", "no"])
    c = out.get("confidence", 0.0)
    return {"p_yes": c if out["choice"] == "yes" else 1 - c}
