#!/usr/bin/env python3
"""Scan a Data Analytics with AI final project and render its requirements bingo card.

Usage: python scripts/bingo_check.py [PROJECT_DIR] [--min 20]
Writes BINGO.md and bingo.html into PROJECT_DIR. Exit 0 = pass, 1 = not yet.
Evidence that can't be detected from code goes in bingo_overrides.json: {"SQUARE_ID": "link or note"}.
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path

SKIP = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build"}
CORE = {"AGENT_LOOP", "FILE_INGEST", "TINYDB", "SQLITE", "STREAMLIT", "STAT_ACTION", "FREE_GIT"}

# (id, label, checks). A square passes if ANY alternative passes; an alternative passes if ALL its
# (glob, regex) pairs match some file. regex None = the file only has to exist.
PY, MD = "**/*.py", "**/*.md"
SQUARES = [
    ("AGENT_LOOP", "Agent runs in a loop", [[(PY, r"while\s+True|--iterations|schedule\.every")]]),
    ("FILE_INGEST", "Reads data from a file", [[(PY, r"\.glob\(|open\(|read_csv|read_json|DictReader")]]),
    ("TINYDB", "TinyDB for messy / free text", [[(PY, r"from tinydb import|import tinydb")]]),
    ("FILENAME_LOG", "File name logged", [[(PY, r"filename")]]),
    ("INTERVAL_ETL", "New data read at intervals", [[(PY, r"time\.sleep|--interval|run_every")]]),

    ("FAKE_DATA", "Fake data import each minute", [[("**/*fake*.py", None)], [(PY, r"(?i)faker|random\.(gauss|choice|randint)")]]),
    ("CLEANING", "Data cleaned", [[(PY, r"to_datetime|dropna|drop_duplicates|fillna|strip\(\)")]]),
    ("SQLITE", "Clean data in SQLite", [[(PY, r"sqlite3\.connect|sqlalchemy.*sqlite")]]),
    ("STREAMLIT", "Streamlit visualization", [[(PY, r"import streamlit")]]),
    ("FLOWCHART", "Live flow chart of steps", [[(PY, r"graphviz_chart|st_mermaid|streamlit_flow|mermaid")]]),

    ("SQL_SHOWN", "SQL queries displayed", [[(PY, r"""st\.code\([^)]*(language\s*=\s*["']sql|sql)""")]]),
    ("FORMULA_SHOWN", "Stat formula shown", [[(PY, r"st\.latex|\.latex\(")]]),
    ("FREE_GIT", "FREE: project in Git", "GIT"),
    ("METHOD_DESC", "Method 1: descriptive", [[(PY, r"np\.mean|\.mean\(|np\.std|\.std\(|median|rolling\(")]]),
    ("METHOD_TREND", "Method 2: trend / regression", [[(PY, r"polyfit|linregress|LinearRegression|\.corr\(|pearsonr|slope")]]),

    ("METHOD_ANOMALY", "Method 3: anomaly / test", [[(PY, r"(?i)z_?score|z_latest|zscore|ttest|chi2|iqr|quantile\(")]]),
    ("STAT_ACTION", "Stat result triggers action", [[(PY, r"(?i)threshold"), (PY, r"(?i)actions?\b")]]),
    ("JEV_DECIDE", "Jev System 1 decisions", [[(PY, r"(?i)\bjev"), (PY, r"p_yes|confidence")]]),
    ("MOE_PANEL", "MoE: models used, when, for what", [[(PY, r"model_calls|model_usage"), (PY, r"claude-haiku"), (PY, r"claude-sonnet|claude-opus")]]),
    ("CLAUDE_API_ENV", "Claude API key via .env", [[(".env.example", r"ANTHROPIC_API_KEY"), (PY, r"load_dotenv")]]),

    ("ROUTINE", "Claude Routine created", [[("docs/ROUTINE.md", r"(?i)routine")]]),
    ("GH_ACTIONS", "Runs on GitHub Actions", [[(".github/workflows/*.y*ml", r"schedule|cron")]]),
    ("STREAMLIT_CLOUD", "Hosted on Streamlit Cloud", [[("README.md", r"https://[\w.-]+\.streamlit\.app")]]),
    ("VIDEO_30S", "30-second Claude Motion video", [[("video/*.mp4", None)], [("**/*.mp4", None)]]),
    ("DOCS", "Each step documented visually", [[("README.md", r"```mermaid")]]),
]
BONUS = [("SNOWFLAKE", "Bonus: Snowflake", [[(PY, r"snowflake\.connector|write_pandas")]])]


def files(root, pattern, cache={}):
    key = (root, pattern)
    if key not in cache:
        cache[key] = [p for p in root.glob(pattern)
                      if p.is_file() and not SKIP.intersection(p.relative_to(root).parts)
                      and "bingo_check" not in p.name]
    return cache[key]


def text(path, cache={}):
    if path not in cache:
        try:
            cache[path] = path.read_text(errors="ignore")
        except OSError:
            cache[path] = ""
    return cache[path]


def check(root, checks):
    """Return evidence string if passed, else None."""
    if checks == "GIT":
        return ".git/" if (root / ".git").exists() else None
    for alternative in checks:
        hits = []
        for pattern, regex in alternative:
            hit = next((p for p in files(root, pattern)
                        if regex is None or re.search(regex, text(p))), None)
            if not hit:
                break
            hits.append(str(hit.relative_to(root)))
        else:
            return ", ".join(dict.fromkeys(hits))
    return None


def score(root, overrides):
    out = []
    for sid, label, checks in SQUARES + BONUS:
        ev = overrides.get(sid) or check(root, checks)
        out.append({"id": sid, "label": label, "done": bool(ev), "evidence": ev or "",
                    "core": sid in CORE, "bonus": (sid, label, checks) in BONUS})
    return out


def lines_complete(grid):
    rows = [grid[i * 5:(i + 1) * 5] for i in range(5)]
    cols = [grid[i::5] for i in range(5)]
    diags = [[grid[i * 6] for i in range(5)], [grid[(i + 1) * 4] for i in range(5)]]
    return sum(all(s["done"] for s in line) for line in rows + cols + diags)


def render_md(project, results, done, need, core_missing, bingos, passed):
    grid = [r for r in results if not r["bonus"]]
    cell = lambda r: f"{'✅' if r['done'] else '⬜'} {'★ ' if r['core'] else ''}{r['label']}"
    md = [f"# Bingo Card — {project}", "",
          f"**{done}/25 squares** · need {need} + all ★ core · **{bingos} bingo line(s)** · "
          f"**{'PASS' if passed else 'NOT YET'}**", ""]
    if core_missing:
        md += [f"Missing core: {', '.join(core_missing)}", ""]
    md += ["| B | I | N | G | O |", "|---|---|---|---|---|"]
    for i in range(5):
        md.append("| " + " | ".join(cell(r) for r in grid[i * 5:(i + 1) * 5]) + " |")
    md += ["", "## Evidence", "", "| Square | Status | Evidence |", "|---|---|---|"]
    for r in results:
        md.append(f"| {r['id']} | {'✅' if r['done'] else '⬜'} | {r['evidence'] or '—'} |")
    md += ["", "_Generated by scripts/bingo_check.py. Undetectable squares: add proof to bingo_overrides.json._", ""]
    return "\n".join(md)


def render_html(project, results, done, need, bingos, passed):
    grid = [r for r in results if not r["bonus"]]
    cells = "".join(
        f'<div class="c {"on" if r["done"] else ""} {"core" if r["core"] else ""}" title="{html.escape(r["evidence"])}">'
        f'<b>{html.escape(r["label"])}</b><small>{"★ core" if r["core"] else r["id"]}</small></div>'
        for r in grid)
    return f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Project Bingo</title><style>
:root{{--bg:#fafaf7;--fg:#1d1d1b;--cell:#fff;--line:#d9d8d2;--on:#1f8a4c;--onbg:#e3f4ea;--mut:#6b6a64}}
@media (prefers-color-scheme:dark){{:root{{--bg:#151514;--fg:#ecebe6;--cell:#1f1f1d;--line:#3a3936;--on:#5fd08f;--onbg:#173323;--mut:#9a9890}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.4 system-ui,sans-serif;padding:24px 16px}}
main{{max-width:760px;margin:auto}} h1{{margin:0 0 4px}} p{{color:var(--mut);margin:0 0 16px}}
.hd,.g{{display:grid;grid-template-columns:repeat(5,1fr);gap:6px}}
.hd div{{text-align:center;font-weight:800;font-size:28px}}
.c{{background:var(--cell);border:1px solid var(--line);border-radius:8px;aspect-ratio:1;padding:8px;display:flex;flex-direction:column;justify-content:space-between;font-size:13px}}
.c small{{color:var(--mut);font-size:10px}} .c.core{{border-width:2px}}
.c.on{{background:var(--onbg);border-color:var(--on)}} .c.on b::before{{content:"✓ ";color:var(--on)}}
@media (max-width:520px){{.c{{font-size:10px;padding:4px}} .c small{{display:none}}}}
</style></head><body><main><h1>{html.escape(project)}</h1>
<p>{done}/25 squares · need {need} + all core · {bingos} bingo line(s) · <strong>{"PASS" if passed else "NOT YET"}</strong></p>
<div class="hd"><div>B</div><div>I</div><div>N</div><div>G</div><div>O</div></div>
<div class="g">{cells}</div></main></body></html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project", nargs="?", default=".")
    ap.add_argument("--min", type=int, default=20, help="squares required to pass (default 20)")
    args = ap.parse_args()
    root = Path(args.project).resolve()
    ov_path = root / "bingo_overrides.json"
    overrides = json.loads(ov_path.read_text()) if ov_path.exists() else {}

    results = score(root, overrides)
    grid = [r for r in results if not r["bonus"]]
    done = sum(r["done"] for r in grid)
    core_missing = [r["id"] for r in grid if r["core"] and not r["done"]]
    bingos = lines_complete(grid)
    passed = done >= args.min and not core_missing
    project = root.name

    (root / "BINGO.md").write_text(render_md(project, results, done, args.min, core_missing, bingos, passed))
    (root / "bingo.html").write_text(render_html(project, results, done, args.min, bingos, passed))

    print(f"{project}: {done}/25 squares, {bingos} bingo line(s), core missing: {core_missing or 'none'}")
    for r in grid:
        if not r["done"]:
            print(f"  ⬜ {r['id']}: {r['label']}")
    print("PASS" if passed else f"NOT YET (need {args.min} + all core)")
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
