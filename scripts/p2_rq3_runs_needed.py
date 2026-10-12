#!/usr/bin/env python3
"""Phase 2, RQ3a: runs per side needed to show equivalence at a stated margin, with proper TOST power.

Pre-registered design: smallest k with P(TOST at alpha .05 shows equivalence within ±m) >= 0.8 (and 0.9),
for margins 2, 3, 5 points, under a true gap of 0 and of 0.6 points, at the 25th, 50th and 75th
percentile of the observed pooled run-to-run SD (headline set, k = 3), and per comparison using its
own pooled SD. Also the power of the first pass's plug-in rule at its k, and the k at which the overlap
rule's own false-alarm rate drops below 5% (k = 4, closed form) for contrast.
Usage: python -I scripts/p2_rq3_runs_needed.py <phase2_dir>
"""
import csv
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parity_lib import rule_false_alarm_exact, runs_needed_plugin, runs_needed_power, tost_power  # noqa: E402

p2 = sys.argv[1]
summ = json.load(open(os.path.join(p2, "rq2_summary.json")))["summaries"]["headline_k3"]
q25, q50, q75 = summ["sd_quartiles"]
MARGINS, GAPS, POWERS = (2, 3, 5), (0.0, 0.6), (0.8, 0.9)
table = {}
for label, sd in (("sd_p25", q25), ("sd_p50", q50), ("sd_p75", q75)):
    for g in GAPS:
        for m in MARGINS:
            cell = {"sd": sd, "true_gap": g, "margin": m}
            for pw in POWERS:
                cell[f"k_power{int(pw * 100)}"] = runs_needed_power(m, g, sd, pw)
            kp = runs_needed_plugin(m, g if g > 0 else 0.0, sd)
            cell["k_plugin"] = kp
            cell["power_at_plugin_k"] = round(tost_power(kp, g, sd, m), 3) if kp else None
            cell["power_at_k3"] = round(tost_power(3, g, sd, m), 3)
            table[f"{label},gap={g},m={m}"] = cell

# per comparison, using its own pooled SD and assuming its observed gap is the true gap (and gap 0)
rows = list(csv.DictReader(open(os.path.join(p2, "rq2_comparisons.csv"))))
per = []
for r in rows:
    if int(r["k_original"]) != 3 or int(r["k_harbor"]) != 3:
        continue
    sd, g = float(r["pooled_sd"]), abs(float(r["gap"]))
    rec = {"adapter": r["adapter"], "exp": r["exp"], "metric": r["metric"], "pooled_sd": sd, "abs_gap": g}
    for m in MARGINS:
        k0 = runs_needed_power(m, 0.0, sd, 0.8, kmax=400) if sd > 0 else 2
        rec[f"k80_m{m}_gap0"] = k0 if k0 is not None else ">400"
        if g >= m:
            rec[f"k80_m{m}_obsgap"] = "gap >= margin"
        else:
            kg = runs_needed_power(m, g, sd, 0.8, kmax=400) if sd > 0 else 2
            rec[f"k80_m{m}_obsgap"] = kg if kg is not None else ">400"
    per.append(rec)
with open(os.path.join(p2, "rq3_runs_needed_per_comparison.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(per[0].keys())); w.writeheader(); w.writerows(per)
dist = {}
BIG = 10_000  # stands for "> 400 runs" in the quantiles and shares (kept in the denominators)
for m in MARGINS:
    v0 = np.array([x[f"k80_m{m}_gap0"] if isinstance(x[f"k80_m{m}_gap0"], int) else BIG for x in per], dtype=float)
    vg = [x[f"k80_m{m}_obsgap"] for x in per]
    reach = [v for v in vg if isinstance(v, int)]
    q = [float(x) for x in np.percentile(v0, [25, 50, 75])]
    dist[f"m={m}"] = {"n": len(per), "gap0_quartiles": [(">400" if x >= BIG else x) for x in q], "gap0_n_over_400": int(np.sum(v0 >= BIG)),
                      "gap0_share_k_le_3": float(np.mean(v0 <= 3)), "gap0_share_k_le_5": float(np.mean(v0 <= 5)), "gap0_share_k_le_10": float(np.mean(v0 <= 10)),
                      "obsgap_gap_ge_margin": sum(1 for v in vg if v == "gap >= margin"), "obsgap_over_400": sum(1 for v in vg if v == ">400"),
                      "obsgap_quartiles_of_reachable": [float(x) for x in np.percentile(reach, [25, 50, 75])] if reach else None}
overlap_fa = {str(k): rule_false_alarm_exact(k) for k in range(2, 11)}
res = {"headline_sd_quartiles": [q25, q50, q75], "table": table, "per_comparison_distribution_k3": dist, "overlap_false_alarm_by_k": overlap_fa}
with open(os.path.join(p2, "rq3_runs_needed.json"), "w") as fh:
    json.dump(res, fh, indent=1)
print(f"observed pooled SD quartiles (k=3 set): {q25:.2f} / {q50:.2f} / {q75:.2f} points")
print("runs per side for 80% / 90% TOST power (true gap 0 | true gap 0.6), by margin:")
for label in ("sd_p25", "sd_p50", "sd_p75"):
    for m in MARGINS:
        c0, c6 = table[f"{label},gap=0.0,m={m}"], table[f"{label},gap=0.6,m={m}"]
        print(f"  {label} ±{m}: gap0 {c0['k_power80']}/{c0['k_power90']} (power at k=3: {c0['power_at_k3']}) | gap0.6 {c6['k_power80']}/{c6['k_power90']} (plug-in k {c6['k_plugin']} has power {c6['power_at_plugin_k']})")
print("per comparison (k=3 set), runs for 80% power at true gap 0 by margin:", {m: (round(v['gap0_quartiles'][1]), f"share needing <=3 runs: {v['gap0_share_k_le_3']:.2f}, <=5: {v['gap0_share_k_le_5']:.2f}, <=10: {v['gap0_share_k_le_10']:.2f}") for m, v in dist.items()})
print("comparisons whose observed gap already exceeds the margin:", {m: v["obsgap_gap_ge_margin"] for m, v in dist.items()}, "| needing more than 400 runs at gap 0:", {m: v["gap0_n_over_400"] for m, v in dist.items()})
