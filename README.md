# MSE Monthly Census Project

One script, one dataset: monthly counts for math.stackexchange.com, 2010-07 → 2026-11
(197 calendar months, UTC).

## Files

- `census.py` — fetches the three monthly counts (questions, answers, new users) via the
  Stack Exchange API v2.3 (`filter=total` endpoints; census, no sampling).
- `draw.py` — draws both graphs from `mse_monthly_census_full.csv` (pure stdlib, no deps):
  `mse_answers_vs_questions.html` (flagship scatter with fitted line, RGB time colors) and
  `mse_2x2_grid.html` (linear vs nonlinear/no-correlation comparison).
- `progress.json` — resume state; one entry per month.
- `mse_monthly_census_full.csv` — the finished dataset: `month, questions, answers, users`.

## Run

```
python3 census.py            # full run / resume
python3 census.py --limit 3  # test: fetch at most 3 missing months
python3 draw.py              # regenerate both graph HTML files
```

Requirements: `curl` on PATH, Python 3, and an API key in `~/.hermes/.env` as
`SE_API_KEY=xxxx`. The key is registered at https://stackapps.com (app registration,
10,000 requests/day vs 300 unkeyed — see https://api.stackexchange.com/docs/throttle).
Requests are paced 0.35 s apart; the script is resume-safe, so a throttle/quota stop
loses nothing — rerun to continue.

## Method (one month = one row)

For each calendar month `[first second, last second]` in UTC:

- `/2.3/questions?site=math&filter=total&fromdate&todate&key` → questions posted
- `/2.3/answers?site=math&filter=total&fromdate&todate&key` → answers posted
- `/2.3/users?site=math&filter=total&fromdate&todate&key` → new user accounts (creation date)

Notes: 2010 starts at July (site launched 2010-07-28); 2026-11 window ends Nov 7.
The `/users` count is accounts created, including sockpuppets/bots and auto-created
accounts from first logins. Deleted content is invisible to all public tools
(quantified: ~0.44% of questions).
