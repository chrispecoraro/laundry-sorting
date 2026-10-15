# Claude Routine — laundry-sorting-daily-report

Created with `/schedule` in Claude Code (or claude.ai/code → Routines).

| Field | Value |
|---|---|
| Name | `laundry-sorting-daily-report` |
| Schedule | Daily, 07:00 local |
| Link | _paste the routine URL here, then copy it into `bingo_overrides.json`_ |

## Prompt

> In repo `<your repo URL>`: read `db/clean.sqlite`. Summarize the last 24 hours —
> batches processed, mean unmatched socks per batch and how it moved, every row in
> `actions` (with its z-score), model usage by expert from `model_calls`, and any
> data-quality issues (blank sock counts, typo'd counts caught by the 60-sock cap,
> notes that failed to tag). Write `docs/reports/<date>.md` and open a pull request.

## Why a routine and not another cron job

The GitHub Action keeps the data flowing every five minutes. The routine is the
part that reads the data like a person would — once a day, in prose, with a PR
you can actually review. Two different jobs.
