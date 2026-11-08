#!/usr/bin/env python3
"""
Draw the monthly-census graphs from mse_monthly_census_full.csv as standalone SVG.

Outputs (in this folder):
  - mse_answers_vs_questions.svg   flagship scatter + residual plot, fitted line,
                                   RGB time coloring (R 2010 -> G 2017 -> B 2026)
  - mse_2x2_grid.svg               four variables (questions / time / new users /
                                   calendar month), each with its residual plot

Usage:  python3 draw.py
Requires: mse_monthly_census_full.csv (from census.py) — stdlib only.
r and s are labeled per scatter as fit-checks only; no other annotations.
"""
import csv, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, "mse_monthly_census_full.csv")

FG, BORDER, MUTED = "#1a1a1a", "#e0e0e0", "#707070"
LINE = "#c00000"
FONT = '<style>text{font-family:system-ui,-apple-system,"Helvetica Neue",sans-serif}</style>'


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
        f = max(0, min(1, (t - 2010) / 7))
        c = tuple(int(R[i] + (G[i] - R[i]) * f) for i in range(3))
    else:
        f = max(0, min(1, (t - 2017) / 9))
        c = tuple(int(G[i] + (B[i] - G[i]) * f) for i in range(3))
    return f"rgb({c[0]},{c[1]},{c[2]})"


def fit(xs, ys):
    n = len(xs); mx = sum(xs) / n; my = sum(ys) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    sxx = sum((a - mx) ** 2 for a in xs)
    r = sxy / math.sqrt(sxx * sum((b - my) ** 2 for b in ys))
    b = sxy / sxx; a0 = my - b * mx
    s = math.sqrt(sum((y - (a0 + b * x)) ** 2 for x, y in zip(xs, ys)) / (n - 2))
    return r, b, a0, s


def scatter_svg(xs, ys, labels, xlabel, W, H, ticks=None,
                xfmt=None,
                tfmt=lambda l, x, y: f"{l} — {x:,} vs {y:,}"):
    xfmt = xfmt or (lambda v: f"{v/1000:.0f}k")
    r, b, a0, s = fit(xs, ys)
    L, R, T, B = 62, 14, 12, 38
    xmin, xmax = min(xs), max(xs)
    pad = (xmax - xmin) * 0.04 or 1
    ymin, ymax = 0, max(ys) * 1.08
    def X(v): return L + (W - L - R) * (v - xmin) / (xmax - xmin + 2 * pad)
    def Y(v): return H - B - (H - T - B) * (v - ymin) / (ymax - ymin)
    p = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">']
    if ticks:
        for xv, lbl in ticks:
            gx = X(xv)
            p.append(f'<line x1="{gx}" y1="{H-B}" x2="{gx}" y2="{H-B+4}" stroke="{FG}"/>')
            p.append(f'<text x="{gx}" y="{H-B+15}" text-anchor="middle" font-size="10" fill="{MUTED}">{lbl}</text>')
    else:
        for i in range(5):
            gx = X(xmin + (xmax - xmin) * i / 4)
            p.append(f'<line x1="{gx}" y1="{H-B}" x2="{gx}" y2="{H-B+4}" stroke="{FG}"/>')
            p.append(f'<text x="{gx}" y="{H-B+15}" text-anchor="middle" font-size="10" fill="{MUTED}">{xfmt(xmin + (xmax - xmin) * i / 4)}</text>')
    for i in range(5):
        gy = Y(ymax * i / 4)
        p.append(f'<line x1="{L}" y1="{gy}" x2="{W-R}" y2="{gy}" stroke="{BORDER}"/>')
        p.append(f'<text x="{L-8}" y="{gy+3.5}" text-anchor="end" font-size="10.5" fill="{MUTED}">{ymax*i/4/1000:.0f}k</text>')
    p.append(f'<line x1="{L}" y1="{H-B}" x2="{W-R}" y2="{H-B}" stroke="{FG}" stroke-width="1.1"/>')
    p.append(f'<line x1="{L}" y1="{T}" x2="{L}" y2="{H-B}" stroke="{FG}" stroke-width="1.1"/>')
    p.append(f'<text x="{(L+W-R)/2}" y="{H-8}" text-anchor="middle" font-size="11" fill="{FG}">{xlabel}</text>')
    p.append(f'<text x="14" y="{(T+H-B)/2}" text-anchor="middle" font-size="11" fill="{FG}" transform="rotate(-90 14 {(T+H-B)/2})">Answers that month</text>')
    p.append(f'<line x1="{X(xmin)}" y1="{Y(a0+b*xmin)}" x2="{X(xmax)}" y2="{Y(a0+b*xmax)}" stroke="{LINE}" stroke-width="1.8"/>')
    for x, y, l in zip(xs, ys, labels):
        p.append(f'<circle cx="{X(x)}" cy="{Y(y)}" r="2.8" fill="{tcolor(l)}" opacity="0.95"><title>{tfmt(l, x, y)}</title></circle>')
    p.append(f'<text x="{W-R-8}" y="{T+13}" text-anchor="end" font-size="11.5" fill="{LINE}" font-weight="600">r = {r:+.3f} · s = {s:.0f}</text>')
    p.append('</svg>')
    return "\n".join(p), b, a0


def residual_svg(xs, ys, labels, xlabel, W, H, b, a0, ticks=None,
                 xfmt=None,
                 tfmt=lambda l, x, y: f"{l} — x {x:,.0f}, resid {y:+,.0f}"):
    xfmt = xfmt or (lambda v: f"{v/1000:.0f}k")
    res = [y - (a0 + b * x) for x, y in zip(xs, ys)]
    L, R, T, B = 62, 14, 10, 30
    xmin, xmax = min(xs), max(xs)
    pad = (xmax - xmin) * 0.04 or 1
    lim = max(abs(v) for v in res) * 1.15 or 1
    def X(v): return L + (W - L - R) * (v - xmin) / (xmax - xmin + 2 * pad)
    def Y(v): return H - B - (H - T - B) * (v + lim) / (2 * lim)
    p = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">']
    if ticks:
        for xv, lbl in ticks:
            gx = X(xv)
            p.append(f'<line x1="{gx}" y1="{H-B}" x2="{gx}" y2="{H-B+4}" stroke="{FG}"/>')
            p.append(f'<text x="{gx}" y="{H-B+14}" text-anchor="middle" font-size="10" fill="{MUTED}">{lbl}</text>')
    else:
        for i in range(5):
            gx = X(xmin + (xmax - xmin) * i / 4)
            p.append(f'<line x1="{gx}" y1="{H-B}" x2="{gx}" y2="{H-B+4}" stroke="{FG}"/>')
            p.append(f'<text x="{gx}" y="{H-B+14}" text-anchor="middle" font-size="10" fill="{MUTED}">{xfmt(xmin + (xmax - xmin) * i / 4)}</text>')
    for i in range(5):
        yv = -lim + 2 * lim * i / 4
        gy = Y(yv)
        p.append(f'<line x1="{L}" y1="{gy}" x2="{W-R}" y2="{gy}" stroke="{BORDER}"/>')
        p.append(f'<text x="{L-8}" y="{gy+3.5}" text-anchor="end" font-size="10" fill="{MUTED}">{yv/1000:+.1f}k</text>')
    p.append(f'<line x1="{L}" y1="{H-B}" x2="{W-R}" y2="{H-B}" stroke="{FG}" stroke-width="1.1"/>')
    p.append(f'<line x1="{L}" y1="{T}" x2="{L}" y2="{H-B}" stroke="{FG}" stroke-width="1.1"/>')
    p.append(f'<line x1="{L}" y1="{Y(0)}" x2="{W-R}" y2="{Y(0)}" stroke="{LINE}" stroke-width="1.6"/>')
    p.append(f'<text x="{(L+W-R)/2}" y="{H-6}" text-anchor="middle" font-size="11" fill="{FG}">{xlabel}</text>')
    p.append(f'<text x="14" y="{(T+H-B)/2}" text-anchor="middle" font-size="11" fill="{FG}" transform="rotate(-90 14 {(T+H-B)/2})">Residual</text>')
    for x, y, l in zip(xs, res, labels):
        p.append(f'<circle cx="{X(x)}" cy="{Y(y)}" r="2.6" fill="{tcolor(l)}" opacity="0.95"><title>{tfmt(l, x, y)}</title></circle>')
    p.append('</svg>')
    return "\n".join(p)


def legend_svg(lx0, lx1, ly):
    return ('<defs><linearGradient id="tg" x1="0" y1="0" x2="1" y2="0">'
            '<stop offset="0" stop-color="#ff453a"/><stop offset="0.5" stop-color="#34c759"/>'
            '<stop offset="1" stop-color="#0a84ff"/></linearGradient></defs>'
            f'<rect x="{lx0}" y="{ly}" width="{lx1-lx0}" height="10" fill="url(#tg)" stroke="#c8c8c8" stroke-width="0.5"/>'
            f'<text x="{lx0}" y="{ly+24}" font-size="11" fill="{FG}" font-weight="600">2010</text>'
            f'<text x="{(lx0+lx1)/2}" y="{ly+24}" font-size="11" fill="{FG}" font-weight="600">2017</text>'
            f'<text x="{lx1}" y="{ly+24}" text-anchor="end" font-size="11" fill="{FG}" font-weight="600">2026</text>')


def doc(children, W, H):
    inner = []
    for svgstr, x, y, w, h in children:
        tag = svgstr.split('>', 1)[0]
        tag = tag.replace('viewBox=', f'x="{x}" y="{y}" width="{w}" height="{h}" viewBox=')
        inner.append(tag + '>' + svgstr.split('>', 1)[1])
    ly = H - 34
    return (f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}">'
            + FONT + "".join(inner) + legend_svg(84, W - 84, ly) + '</svg>')


def flagship(months, Q, A):
    W, H = 920, 560
    s1, b, a0 = scatter_svg(Q, A, months, "Questions posted that month", W, H,
                            tfmt=lambda l, x, y: f"{l} — {x:,} questions, {y:,} answers (ratio {y/x:.2f})")
    s2 = residual_svg(Q, A, months, "Questions posted that month", 920, 240, b, a0)
    return doc([(s1, 0, 0, W, H), (s2, 0, 560, 920, 240)], 920, 860)


def grid2x2(months, Q, A, U):
    t = [int(m[:4]) + (int(m[5:7]) - 1) / 12 for m in months]
    moy = [int(m[5:7]) for m in months]
    cw, ch, gap = 430, 310, 16
    children = []
    specs = [
        (Q, A, "Questions that month", None, None),
        (t, A, "Year", [(y + 0.5, str(y)) for y in range(2010, 2027, 2)], lambda v: f"{v:.0f}"),
        (U, A, "New user registrations that month", None, None),
        (moy, A, "Calendar month (1=Jan .. 12=Dec)", [(m, str(m)) for m in (1, 4, 7, 10)], lambda v: f"{v:.0f}"),
    ]
    for i, (xs, ys, xlab, ticks, xfmt) in enumerate(specs):
        y = i * (ch + gap)
        s1, b, a0 = scatter_svg(xs, ys, months, xlab, cw, ch, ticks=ticks, xfmt=xfmt)
        s2 = residual_svg(xs, ys, months, xlab, cw, ch, b, a0, ticks=ticks, xfmt=xfmt)
        children.append((s1, 0, y, cw, ch))
        children.append((s2, cw + gap, y, cw, ch))
    W = 2 * cw + gap
    H = 4 * (ch + gap) + 40
    return doc(children, W, H)


def main():
    months, Q, A, U = load()
    print(f"loaded {len(months)} months")
    with open(os.path.join(HERE, "mse_answers_vs_questions.svg"), "w") as f:
        f.write(flagship(months, Q, A))
    with open(os.path.join(HERE, "mse_2x2_grid.svg"), "w") as f:
        f.write(grid2x2(months, Q, A, U))
    print("wrote mse_answers_vs_questions.svg, mse_2x2_grid.svg")


if __name__ == "__main__":
    main()
