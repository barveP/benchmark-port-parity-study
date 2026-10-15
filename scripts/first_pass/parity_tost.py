#!/usr/bin/env python3
"""Lead's check: same 43 comparisons, standard equivalence test convention (TOST at alpha=0.05 = 90% CI inside margin).
Also: runs per side needed at the median noise level. Usage: parity_tost.py <harbor_clone_dir>"""
import json, glob, os, sys, statistics as st, math
# two-sided t quantiles: t.95 (for 90% CI) and t.975 (for 95% CI) by degrees of freedom
T95 = {2:2.920,4:2.132,6:1.943,8:1.860,10:1.812,12:1.782,14:1.761,16:1.746,18:1.734,20:1.725,22:1.717,24:1.711,26:1.706,28:1.701,30:1.697,34:1.691,38:1.686,48:1.677,58:1.672,78:1.665,98:1.661}
def t95(df):
    ks = sorted(T95); 
    for k in ks:
        if df <= k: return T95[k]
    return 1.645
root = sys.argv[1]; rows = []
for f in sorted(glob.glob(os.path.join(root, "adapters", "*", "parity_experiment.json"))):
    d = json.load(open(f)); d = [d] if isinstance(d, dict) else d
    for e in d:
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
            sc = 100.0 if max(vals) <= 1.0 else 1.0
            a = [x*sc for x in a]; b = [x*sc for x in b]
            if len(set(a)) == 1 and len(set(b)) == 1: break
            rows.append((f.split(os.sep)[-2], m.get("metric"), a, b)); break
n = len(rows); sd = []; res = []
for name, metric, a, b in rows:
    s = math.sqrt((st.variance(a) + st.variance(b)) / 2); g = abs(st.mean(a) - st.mean(b))
    h90 = 2.132 * s * math.sqrt(2/3)
    sd.append(s); res.append((g, h90, name, metric))
print("comparisons:", n)
for mgn in (2, 3, 5):
    ok = [r for r in res if r[0] + r[1] <= mgn]
    print(f"equivalence within +-{mgn} points established (TOST, alpha .05): {len(ok)} of {n} ({100*len(ok)/n:.0f}%)")
med = sorted(sd)[n//2]; hw = sorted(r[1] for r in res)[n//2]
print(f"median run-to-run SD {med:.2f} points; median 90% CI half-width on the gap {hw:.2f} points")
print("runs per side needed at the median noise level, assuming the true gap is 0.6 points (the observed median):")
for mgn in (2, 3, 5):
    for k in range(2, 200):
        h = t95(2*k-2) * med * math.sqrt(2/k)
        if 0.6 + h <= mgn:
            print(f"  within +-{mgn} points: {k} runs per side"); break
worst = sorted(res, key=lambda r: -(r[0]))[:5]
print("largest observed gaps (points):", [(r[2], r[3], round(r[0],2)) for r in worst])
