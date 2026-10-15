"""Sock & Garment Sorting Pulse -- live dashboard.

Reads the SQLite file the GitHub Action commits (Streamlit Cloud disk is
ephemeral, so nothing is ever written from here).
"""
import os
import sqlite3
import tempfile

import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Sock & Garment Sorting Pulse", layout="wide")

def _secret(name, default=""):
    """st.secrets raises if no secrets.toml exists -- normal when running locally."""
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


# Set DB_URL in Streamlit Cloud secrets; empty locally = read the file next door.
DB_URL = _secret("DB_URL", os.getenv("DB_URL", ""))
STEPS = ["generate", "extract", "clean", "load", "analyze", "act"]
SYSTEM_1 = "#8e44ad"   # Jev: fast typed decisions
SYSTEM_2 = "#2980b9"   # Claude: slow reasoning


def db():
    if DB_URL:
        path = os.path.join(tempfile.gettempdir(), "clean.sqlite")
        with open(path, "wb") as f:
            f.write(requests.get(DB_URL, timeout=20).content)
        return sqlite3.connect(path)
    return sqlite3.connect("db/clean.sqlite")


def q(sql):
    with db() as c:
        return pd.read_sql(sql, c)


def show(title, sql):
    """Every chart shows the SQL that fed it."""
    st.caption(title)
    st.code(sql, language="sql")
    return q(sql)


@st.fragment(run_every=60)
def live():
    runs = q("SELECT * FROM pipeline_runs ORDER BY rowid DESC LIMIT 6")
    last = runs.iloc[0] if len(runs) else None
    st.subheader(f"Live pipeline — run {last['run_id'] if last is not None else '—'}")

    done = set(runs["step"]) if len(runs) else set()
    acted = len(runs) and (runs["status"] == "triggered").any()
    dot = "digraph{rankdir=LR;node[shape=box,style=filled,fontname=Helvetica];"
    for s in STEPS:
        color = "#e74c3c" if s == "act" and acted else ("#2ecc71" if s in done else "#dddddd")
        dot += f'{s}[fillcolor="{color}"];'
    dot += "->".join(STEPS) + "}"
    st.graphviz_chart(dot)

    gen = runs.loc[runs.step == "generate", "filename"]
    st.write("**Latest file ingested:**", gen.iloc[0] if len(gen) else "—")

    t1, t2, t3, t4 = st.tabs(["Unmatched socks", "Actions", "Models (MoE)", "Files & SQL"])

    with t1:
        b = show("Mean unmatched socks per batch",
                 "SELECT run_id, AVG(unmatched_socks) AS mean_unmatched, MAX(ts) AS ts "
                 "FROM records GROUP BY run_id ORDER BY MIN(rowid)")
        b["batch"] = range(1, len(b) + 1)
        st.line_chart(b, x="batch", y="mean_unmatched")

        s = q("SELECT method, value, formula FROM stats "
              "WHERE run_id=(SELECT run_id FROM stats ORDER BY rowid DESC LIMIT 1)")
        for _, r in s.iterrows():
            c1, c2 = st.columns([1, 2])
            c1.metric(r.method, f"{r.value:.2f}")
            c2.latex(r.formula)                    # the formula behind the number

        d = show("Garment defects found in the notes",
                 "SELECT defect, COUNT(*) AS n FROM records GROUP BY defect ORDER BY n DESC")
        st.bar_chart(d, x="defect", y="n")

    with t2:
        a = show("Stat-triggered actions",
                 "SELECT ts, z, action, message FROM actions ORDER BY rowid DESC LIMIT 20")
        if len(a) and len(runs) and a.iloc[0].ts >= runs.iloc[-1].started_at:
            st.error(f"ACTION: {a.iloc[0].action}  (z = {a.iloc[0].z:.2f})")
            st.info(a.iloc[0].message)
        st.dataframe(a, width="stretch")

    with t3:
        st.markdown(
            f"<span style='color:{SYSTEM_1}'>**System 1 — Jev**</span>: fast typed decisions "
            "(which expert? act or not?). "
            f"<span style='color:{SYSTEM_2}'>**System 2 — Claude**</span>: slow reasoning "
            "(tag free text, explain stats, word the action).",
            unsafe_allow_html=True)
        st.caption("Expert map — clean: Haiku · analyze: Sonnet · decide: Opus. "
                   "This is an app-level router over models, not the MoE inside one model.")
        m = show("Model calls",
                 "SELECT ts, task, model, input_tokens, output_tokens, latency_s, dry_run "
                 "FROM model_calls ORDER BY rowid DESC LIMIT 200")
        if len(m):
            st.bar_chart(m.groupby("model").size())
        st.dataframe(m, width="stretch")

    with t4:
        st.dataframe(show("Run log (filenames + the SQL each step ran)",
                          "SELECT run_id, step, status, filename, sql, finished_at "
                          "FROM pipeline_runs ORDER BY rowid DESC LIMIT 60"),
                     width="stretch")


st.title("Sock & Garment Sorting Pulse")
st.caption("Unmatched socks, faded colors and tears — tracked load by load.")
live()
