#!/usr/bin/env python3
"""First-pass check, cleaner cut: one primary (first rate-like) metric per experiment, exactly 3 runs per side.
Usage: parity_clean.py <harbor_clone_dir>"""
import json, glob, os, sys, statistics as st, math
root = sys.argv[1]
rows = []
n_exp = 0
for f in sorted(glob.glob(os.path.join(root, "adapters", "*", "parity_experiment.json"))):
    name = f.split(os.sep)[-2]
    d = json.load(open(f))
    if isinstance(d, dict): d = [d]
    for e in d:
        n_exp += 1
        for m in e.get("metrics", []) or []:
            a = m.get("original_runs"); b = m.get("harbor_runs")
            if not (isinstance(a, list) and isinstance(b, list)): continue
            a = [x for x in a if isinstance(x, (int, float)) and not isinstance(x, bool)]
            b = [x for x in b if isinstance(x, (int, float)) and not isinstance(x, bool)]
            if len(a) != 3 or len(b) != 3: continue
            mn = str(m.get("metric", "")).lower()
            if any(t in mn for t in ("stderr", "std", "missing", "cost", "token", "time", "latency")): continue
            vals = a + b
            if min(vals) < 0 or max(vals) > 100: continue
            scale = 100.0 if max(vals) <= 1.0 else 1.0
            a = [x * scale for x in a]; b = [x * scale for x in b]
            rows.append((name, m.get("metric"), a, b))
            break   # first qualifying metric only
print("experiments:", n_exp, "| with a rate-like primary metric and 3 runs per side:", len(rows))
ident = [r for r in rows if r[2] == r[3]]
zero = [r for r in rows if len(set(r[2])) == 1 and len(set(r[3])) == 1]
print("identical run lists on both sides:", len(ident), "| zero spread on both sides:", len(zero))
use = [r for r in rows if not (len(set(r[2])) == 1 and len(set(r[3])) == 1)]
sd = []; gap = []; hw = []; fail = 0
for name, metric, a, b in use:
    s = math.sqrt((st.variance(a) + st.variance(b)) / 2)
    g = abs(st.mean(a) - st.mean(b))
    h = 2.776 * s * math.sqrt(2 / 3)       # 95% CI half-width on the gap, t with 4 df
    sd.append(s); gap.append(g); hw.append(h)
    if max(a) < min(b) or max(b) < min(a): fail += 1
q = lambda v, p: sorted(v)[min(len(v) - 1, int(p * len(v)))]
n = len(use)
print(f"analysed (non-degenerate): {n}")
print(f"run-to-run SD, points: median {q(sd,.5):.2f} | 75th {q(sd,.75):.2f}")
print(f"|gap| original vs port, points: median {q(gap,.5):.2f} | 75th {q(gap,.75):.2f} | max {max(gap):.2f}")
print(f"95% CI half-width on the gap, points: median {q(hw,.5):.2f} | 25th {q(hw,.25):.2f} | 75th {q(hw,.75):.2f}")
print(f"fail Harbor's range-overlap rule: {fail} of {n}")
for mgn in (1, 2, 3, 5, 10):
    ok = sum(1 for g, h in zip(gap, hw) if g + h <= mgn)
    print(f"can show port is within +-{mgn} points of the original: {ok} of {n} ({100*ok/n:.0f}%)")
sig = sum(1 for g, h in zip(gap, hw) if g > h)
print(f"gap is statistically distinguishable from zero (|gap| > half-width): {sig} of {n}")
