#!/usr/bin/env python3
"""
Monthly census of math.stackexchange.com via the Stack Exchange API v2.3.

Counts, per calendar month (UTC), 2010-07 .. 2026-11:
  - questions posted that month   (/questions?filter=total)
  - answers posted that month     (/answers?filter=total)
  - new user accounts that month  (/users?filter=total)

Usage:
  python3 census.py              # fetch all missing months (resumes from progress.json)
  python3 census.py --limit 3    # fetch at most 3 missing months (test/quick run)

Requires an API key in ~/.hermes/.env as:  SE_API_KEY=xxxx
(stackapps.com app registration; raises the daily quota to 10,000 requests).

Output: mse_monthly_census_full.csv  (month, questions, answers, users)
State:  progress.json (resume-safe; one entry per month)
"""
import json, os, subprocess, sys, time
import datetime, csv, argparse

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
PROGRESS = os.path.join(OUT_DIR, "progress.json")
CSV_OUT = os.path.join(OUT_DIR, "mse_monthly_census_full.csv")

SITE = "math"
FILTER = "total"

def load_key():
    env = os.path.expanduser("~/.hermes/.env")
    with open(env) as f:
        for line in f:
            if line.startswith("SE_API_KEY="):
                return line.split("=", 1)[1].strip()
    raise SystemExit("SE_API_KEY not found in ~/.hermes/.env")

def ts(y, m, d=1):
    return int(datetime.datetime(y, m, d, tzinfo=datetime.timezone.utc).timestamp())

def months_span():
    out = []
    for y in range(2010, 2027):
        for m in range(1, 13):
            if y == 2010 and m < 7:      # site launched 2010-07-28
                continue
            if y == 2026 and m > 11:     # data through 2026-11-07
                continue
            label = f"{y}-{m:02d}"
            fd = ts(y, m)
            td = (ts(y + 1, 1) - 1) if m == 12 else (ts(y, m + 1) - 1)
            out.append((label, fd, td))
    return out

def total(endpoint, fd, td, key, tries=3):
    url = (f"https://api.stackexchange.com/2.3/{endpoint}?site={SITE}"
           f"&filter={FILTER}&fromdate={fd}&todate={td}&key={key}")
    for i in range(tries):
        r = subprocess.run(["curl", "-s", "-m", "40", "--compressed",
                            "-A", "Mozilla/5.0 (research)", url],
                           capture_output=True, text=True).stdout
        try:
            d = json.loads(r)
            if "total" in d:
                return d["total"]
        except Exception:
            pass
        time.sleep(2 + 3 * i)
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="max months to fetch this run")
    args = ap.parse_args()

    key = load_key()
    months = months_span()
    prog = json.load(open(PROGRESS)) if os.path.exists(PROGRESS) else {}

    missing = []
    for label, fd, td in months:
        e = prog.setdefault(label, {})
        if not all(e.get(v) is not None for v in ("questions", "answers", "users")):
            missing.append((label, fd, td))

    print(f"months total {len(months)} | complete {len(months) - len(missing)} | missing {len(missing)}")
    for label, fd, td in missing[:args.limit] if args.limit else missing:
        e = prog.setdefault(label, {})
        for var, endpoint in (("questions", "questions"), ("answers", "answers"), ("users", "users")):
            if e.get(var) is not None:
                continue
            e[var] = total(endpoint, fd, td, key)
            if e[var] is None:
                print(f"{label}: {var} FAILED (throttle/quota?) — stopping; rerun to resume")
                json.dump(prog, open(PROGRESS, "w"))
                return 1
            time.sleep(0.35)
        json.dump(prog, open(PROGRESS, "w"))
        print(f"{label}: Q={e['questions']} A={e['answers']} U={e['users']}")

    done = [m for m, _, _ in months
            if all(prog[m].get(v) is not None for v in ("questions", "answers", "users"))]
    print(f"complete {len(done)}/{len(months)}")
    if len(done) == len(months):
        with open(CSV_OUT, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["month", "questions", "answers", "users"])
            for label, _, _ in months:
                w.writerow([label, prog[label]["questions"], prog[label]["answers"], prog[label]["users"]])
        print(f"wrote {CSV_OUT}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
