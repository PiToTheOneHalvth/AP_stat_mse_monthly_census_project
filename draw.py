#!/usr/bin/env python3
"""
Draw the monthly-census graphs from mse_monthly_census_full.csv.

Outputs (in this folder):
  - mse_answers_vs_questions.html   flagship scatter: answers vs questions, fitted line,
                                    RGB time coloring (R 2010 -> G 2017 -> B 2026), legend
  - mse_2x2_grid.html               2x2 grid: questions (linear) vs time (nonlinear),
                                    new users (no correlation), calendar month (seasonal)

Usage:  python3 draw.py
Requires: mse_monthly_census_full.csv (from census.py) — no other dependencies.
r and its 95% CI are printed/annotated as fit-checks only.
"""
import csv, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, "mse_monthly_census_full.csv")

def load():
    rows = list(csv.DictReader(open(CSV)))
    months = [r["month"] for r in rows]
    Q = [int(r["questions"]) for r in rows]
    A = [int(r["answers"]) for r in rows]
    U = [int(r["users"]) for r in rows]
    return months, Q, A, U

def tcolor(label):
    y = int(label[:4]); t = y + (int(label[5:7]) - 1) / 12
    R, G, B = (255, 69, 58), (52, 199, 89), (10, 132, 255)
    if t <= 2017:
        f = max(0, min(1, (t - 2010) / 7)); c = tuple(int(R[i] + (G[i] - R[i]) * f) for i in range(3))
    else:
        f = max(0, min(1, (t - 2017) / 9)); c = tuple(int(G[i] + (B[i] - G[i]) * f) for i in range(3))
    return f"rgb({c[0]},{c[1]},{c[2]})"

def fit(xs, ys):
    n = len(xs); mx = sum(xs) / n; my = sum(ys) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys)); sxx = sum((a - mx) ** 2 for a in xs)
    r = sxy / math.sqrt(sxx * sum((b - my) ** 2 for b in ys))
    z = math.atanh(max(-.99999, min(.99999, r))); se = 1 / math.sqrt(n - 3)
    rlo, rhi = math.tanh(z - 1.96 * se), math.tanh(z + 1.96 * se)
    b = sxy / sxx; a0 = my - b * mx
    s = math.sqrt(sum((y - (a0 + b * x)) ** 2 for x, y in zip(xs, ys)) / (n - 2))
    return r, rlo, rhi, b, a0, s

def panel(xs, ys, labels, xlabel, ticks=None,
          xfmt=lambda v: f"{v/1000:.0f}k", tfmt=lambda l, x, y: f"{l} — {x:,} vs {y:,}"):
    r, rlo, rhi, b, a0, s = fit(xs, ys)
    W, H = 430, 310; L, R, T, B = 62, 14, 12, 38
    xmin, xmax = min(xs), max(xs); pad = (xmax - xmin) * 0.04 or 1
    ymin, ymax = 0, max(ys) * 1.08
    def X(v): return L + (W - L - R) * (v - xmin) / (xmax - xmin + 2 * pad)
    def Y(v): return H - B - (H - T - B) * (v - ymin) / (ymax - ymin)
    p = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" style="width:{W}px;height:auto;display:block">']
    if ticks:
        for xv, lbl in ticks:
            gx = X(xv)
            p.append(f'<line x1="{gx}" y1="{H-B}" x2="{gx}" y2="{H-B+4}" stroke="var(--foreground)"/>')
            p.append(f'<text x="{gx}" y="{H-B+15}" text-anchor="middle" font-size="10" fill="var(--muted-foreground)">{lbl}</text>')
    else:
        for i in range(5):
            gx = X(xmin + (xmax - xmin) * i / 4)
            p.append(f'<line x1="{gx}" y1="{H-B}" x2="{gx}" y2="{H-B+4}" stroke="var(--foreground)"/>')
            p.append(f'<text x="{gx}" y="{H-B+15}" text-anchor="middle" font-size="10" fill="var(--muted-foreground)">{xfmt(xmin + (xmax - xmin) * i / 4)}</text>')
    for i in range(5):
        gy = Y(ymax * i / 4)
        p.append(f'<line x1="{L}" y1="{gy}" x2="{W-R}" y2="{gy}" stroke="var(--border)"/>')
        p.append(f'<text x="{L-8}" y="{gy+3.5}" text-anchor="end" font-size="10.5" fill="var(--muted-foreground)">{ymax*i/4/1000:.0f}k</text>')
    p.append(f'<line x1="{L}" y1="{H-B}" x2="{W-R}" y2="{H-B}" stroke="var(--foreground)" stroke-width="1.1"/>')
    p.append(f'<line x1="{L}" y1="{T}" x2="{L}" y2="{H-B}" stroke="var(--foreground)" stroke-width="1.1"/>')
    p.append(f'<text x="{(L+W-R)/2}" y="{H-8}" text-anchor="middle" font-size="11" fill="var(--foreground)">{xlabel}</text>')
    p.append(f'<text x="14" y="{(T+H-B)/2}" text-anchor="middle" font-size="11" fill="var(--foreground)" transform="rotate(-90 14 {(T+H-B)/2})">Answers that month</text>')
    p.append(f'<line x1="{X(xmin)}" y1="{Y(a0+b*xmin)}" x2="{X(xmax)}" y2="{Y(a0+b*xmax)}" stroke="#c00000" stroke-width="1.8"/>')
    for x, y, l in zip(xs, ys, labels):
        p.append(f'<circle cx="{X(x)}" cy="{Y(y)}" r="2.8" fill="{tcolor(l)}" opacity="0.95"><title>{tfmt(l, x, y)}</title></circle>')
    p.append(f'<text x="{W-R-8}" y="{T+13}" text-anchor="end" font-size="11.5" fill="#c00000" font-weight="600">r = {r:+.3f} · s = {s:.0f}</text>')
    p.append('</svg>')
    return "\n".join(p)

LEGEND = """
<div style="display:inline-block;margin-top:10px;">
  <div style="display:flex;align-items:center;gap:8px;">
    <span style="font-size:11px;color:var(--foreground);font-weight:600;">2010</span>
    <svg width="300" height="10" viewBox="0 0 300 10" style="display:block;border:1px solid var(--border);border-radius:3px;">
      <defs><linearGradient id="tg" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0" stop-color="rgb(255,69,58)"/><stop offset="0.5" stop-color="rgb(52,199,89)"/><stop offset="1" stop-color="rgb(10,132,255)"/>
      </linearGradient></defs>
      <rect x="0" y="0" width="300" height="10" fill="url(#tg)"/>
    </svg>
    <span style="font-size:11px;color:var(--foreground);font-weight:600;">2026</span>
  </div>
</div>"""

def page(inner, note):
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
body{{margin:0;font-family:var(--font,-apple-system,sans-serif);}}
.wrap{{display:inline-block;}}
p.note{{color:var(--muted-foreground);font-size:12px;margin:8px 0 0 0;max-width:900px;}}
</style></head>
<body><div class="wrap">
{inner}
{LEGEND}
</div></body></html>"""

def flagship(months, Q, A):
    W, H = 920, 560; L, R, T, B = 84, 30, 20, 54
    r, rlo, rhi, b, a0, s = fit(Q, A)
    xmax, ymax = max(Q) * 1.08, max(A) * 1.08
    def X(v): return L + (W - L - R) * v / xmax
    def Y(v): return H - B - (H - T - B) * v / ymax
    p = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" style="width:{W}px;height:auto;display:block">']
    for i in range(7):
        xv, yv = xmax * i / 6, ymax * i / 6
        gx, gy = X(xv), Y(yv)
        p.append(f'<line x1="{gx}" y1="{T}" x2="{gx}" y2="{H-B}" stroke="var(--border)"/>')
        p.append(f'<line x1="{L}" y1="{gy}" x2="{W-R}" y2="{gy}" stroke="var(--border)"/>')
        p.append(f'<text x="{gx}" y="{H-B+18}" text-anchor="middle" font-size="12" fill="var(--muted-foreground)">{xv/1000:.0f}k</text>')
        p.append(f'<text x="{L-10}" y="{gy+4}" text-anchor="end" font-size="12" fill="var(--muted-foreground)">{yv/1000:.0f}k</text>')
    p.append(f'<line x1="{L}" y1="{H-B}" x2="{W-R}" y2="{H-B}" stroke="var(--foreground)" stroke-width="1.2"/>')
    p.append(f'<line x1="{L}" y1="{T}" x2="{L}" y2="{H-B}" stroke="var(--foreground)" stroke-width="1.2"/>')
    p.append(f'<text x="{(L+W-R)/2}" y="{H-16}" text-anchor="middle" font-size="13" fill="var(--foreground)">Questions posted that month</text>')
    p.append(f'<text x="18" y="{(T+H-B)/2}" text-anchor="middle" font-size="13" fill="var(--foreground)" transform="rotate(-90 18 {(T+H-B)/2})">Answers posted that month</text>')
    p.append(f'<line x1="{X(0)}" y1="{Y(a0)}" x2="{X(xmax)}" y2="{Y(a0+b*xmax)}" stroke="#c00000" stroke-width="2.2"/>')
    p.append(f'<text x="{X(xmax)-165}" y="{Y(a0+b*xmax)-10}" font-size="13" fill="#c00000" font-weight="600">r = {r:.3f} · s = {s:.0f}</text>')
    for q, a, m in zip(Q, A, months):
        p.append(f'<circle cx="{X(q)}" cy="{Y(a)}" r="3.4" fill="{tcolor(m)}" opacity="0.95"><title>{m} — {q:,} questions, {a:,} answers (ratio {a/q:.2f})</title></circle>')
    p.append('</svg>')
    note = "" 
    return page("\n".join(p), note)

def grid2x2(months, Q, A, U):
    t = [int(m[:4]) + (int(m[5:7]) - 1) / 12 for m in months]
    moy = [int(m[5:7]) for m in months]
    p1 = panel(Q, A, months, "Questions that month",
               tfmt=lambda l, x, y: f"{l} — Q {x:,}, A {y:,} (ratio {y/x:.2f})")
    p2 = panel(t, A, months, "Year",
               ticks=[(y + 0.5, str(y)) for y in range(2010, 2027, 2)], xfmt=lambda v: f"{v:.0f}",
               tfmt=lambda l, x, y: f"{l} — {x:.2f} vs {y:,}")
    p3 = panel(U, A, months, "New user registrations that month")
    p4 = panel(moy, A, months, "Calendar month (1=Jan .. 12=Dec)",
               ticks=[(m, str(m)) for m in (1, 4, 7, 10)], xfmt=lambda v: f"{v:.0f}")
    inner = f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;">{p1}{p2}{p3}{p4}</div>'
    note = "" 
    return page(inner, note)

def main():
    months, Q, A, U = load()
    print(f"loaded {len(months)} months")
    with open(os.path.join(HERE, "mse_answers_vs_questions.html"), "w") as f:
        f.write(flagship(months, Q, A))
    with open(os.path.join(HERE, "mse_2x2_grid.html"), "w") as f:
        f.write(grid2x2(months, Q, A, U))
    print("wrote mse_answers_vs_questions.html, mse_2x2_grid.html")

if __name__ == "__main__":
    main()
