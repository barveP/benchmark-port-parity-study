#!/usr/bin/env python3
"""First-pass check. (1) Error rates of the 'run-score ranges overlap' rule with k runs per side,
by simulation with normal noise. (2) Rough run-to-run spread in the published parity files.
Usage: parity_power.py <harbor_clone_dir>"""
import json, glob, os, sys, random, statistics as st, math
random.seed(7)
def nonoverlap_rate(k, shift, n=200000):
    c = 0
    for _ in range(n):
        a = [random.gauss(0, 1) for _ in range(k)]
        b = [random.gauss(shift, 1) for _ in range(k)]
        if max(a) < min(b) or max(b) < min(a):
            c += 1
    return c / n
print("P(rule says MISMATCH) by true gap, in units of run-to-run SD")
print("k runs/side | gap 0 (false alarm) | gap 1 SD | gap 2 SD | gap 3 SD | gap 4 SD")
for k in (2, 3, 5, 8):
    print(k, *[f"{nonoverlap_rate(k, s):.3f}" for s in (0, 1, 2, 3, 4)], sep=" | ")
print("exact false alarm for k=3: 2*(3!*3!)/6! =", 2 * math.factorial(3) ** 2 / math.factorial(6))

root = sys.argv[1]
sds = []; gaps = []; n_rows = 0
for f in sorted(glob.glob(os.path.join(root, "adapters", "*", "parity_experiment.json"))):
    d = json.load(open(f))
    if isinstance(d, dict): d = [d]
    for e in d:
        for m in e.get("metrics", []) or []:
            a = m.get("original_runs"); b = m.get("harbor_runs")
            if not (isinstance(a, list) and isinstance(b, list)): continue
            a = [x for x in a if isinstance(x, (int, float)) and not isinstance(x, bool)]
            b = [x for x in b if isinstance(x, (int, float)) and not isinstance(x, bool)]
            if len(a) != 3 or len(b) != 3: continue
            name = str(m.get("metric", "")).lower()
            if "stderr" in name or "std" in name: continue          # not a score
            vals = a + b
            if min(vals) < 0 or max(vals) > 100: continue            # keep rate-like metrics only
            scale = 100.0 if max(vals) <= 1.0 else 1.0               # fractions -> percentage points
            a = [x * scale for x in a]; b = [x * scale for x in b]
            pooled = math.sqrt((st.variance(a) + st.variance(b)) / 2)
            n_rows += 1
            sds.append(pooled); gaps.append(abs(st.mean(a) - st.mean(b)))
sds.sort(); gaps.sort()
q = lambda v, p: v[min(len(v) - 1, int(p * len(v)))]
print(f"\nrate-like metric rows with exactly 3 runs per side: {n_rows}")
print(f"run-to-run SD in points: median {q(sds,.5):.2f}, 75th pct {q(sds,.75):.2f}, 90th pct {q(sds,.9):.2f}; zero-SD rows: {sum(1 for s in sds if s == 0)}")
print(f"|gap between means| in points: median {q(gaps,.5):.2f}, 75th pct {q(gaps,.75):.2f}, 90th pct {q(gaps,.9):.2f}, max {gaps[-1]:.2f}")
# 95% CI half-width on the gap for 3 vs 3 runs (t, df=4 -> 2.776): 2.776*SD*sqrt(2/3)
hw = [2.776 * s * math.sqrt(2 / 3) for s in sds]
print(f"95% CI half-width on the gap, points: median {q(hw,.5):.2f}, 75th pct {q(hw,.75):.2f}, 90th pct {q(hw,.9):.2f}")
for margin in (1, 2, 3, 5):
    ok = sum(1 for g, h in zip([abs(x) for x in gaps], hw) if g + h <= margin)
    print(f"rows where the data could establish equivalence within +-{margin} points (|gap|+halfwidth <= margin): {ok} of {n_rows}")
