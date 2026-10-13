#!/usr/bin/env python3
"""Read a Harbor parity_experiment.json and print, for every metric row with runs on both sides:
the range-overlap verdict Harbor uses, the gap with its 90% and 95% intervals, the smallest margin within which
equivalence can be shown (TOST, alpha .05), and the runs per side needed to show equivalence within
3 and 5 points at 80% power using that row's own run-to-run SD (if the true gap were 0).

Usage: python -I scripts/parity_verdict.py <parity_experiment.json> [--margin M]
Conventions: scores are converted to points (fractions x100); runs are treated as independent draws
with a common variance across sides (pooled t); "n/a" where a side has fewer than 2 runs.
"""
import argparse
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parity_lib import diff_ci_halfwidth, lenient_runs, pooled_sd, range_separation, ranges_overlap, runs_needed_power  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("path")
ap.add_argument("--margin", type=float, default=None, help="also report whether equivalence is shown within ±M points")
args = ap.parse_args()
d = json.load(open(args.path))
exps = d if isinstance(d, list) else [d]


def runs(m, side):
    for suf in ("_runs", "_trials"):
        v = lenient_runs(m.get(side + suf))
        if v:
            return v
    return None


for e in exps:
    print(f"== {e.get('adapter_name')} | agent {e.get('agent')} | model {e.get('model')} | parity set {e.get('parity_benchmark_size')}/{e.get('adapted_benchmark_size')}")
    for m in e.get("metrics") or []:
        a, b = runs(m, "original"), runs(m, "harbor")
        name = m.get("metric")
        if not (a and b):
            print(f"   {name}: no run lists on both sides")
            continue
        if max(a + b) <= 1.0 and min(a + b) >= 0 and "%" not in str(m.get("original", "")) + str(m.get("harbor", "")):
            a, b = [x * 100 for x in a], [x * 100 for x in b]
        gap = statistics.mean(b) - statistics.mean(a)
        ov = ranges_overlap(a, b, eps=1e-9)
        line = f"   {name}: k={len(a)}v{len(b)} | ranges {'overlap' if ov else 'DO NOT overlap'} (separation {range_separation(a, b):+.3g}) | gap {gap:+.2f} pts"
        if min(len(a), len(b)) < 2:
            print(line + " | interval n/a (a side has one run)")
            continue
        sd = pooled_sd(a, b)
        hw95, hw90 = diff_ci_halfwidth(a, b, 0.95), diff_ci_halfwidth(a, b, 0.90)
        sm = abs(gap) + hw90
        line += f" [90%: {gap - hw90:+.2f}, {gap + hw90:+.2f}] [95%: {gap - hw95:+.2f}, {gap + hw95:+.2f}] | run SD {sd:.2f} | smallest provable margin ±{sm:.1f} pts"
        if args.margin is not None:
            line += f" | within ±{args.margin:g}: {'shown' if sm <= args.margin else 'NOT shown'}"
        if sd > 0:
            k3, k5 = runs_needed_power(3, 0.0, sd, 0.8, kmax=500), runs_needed_power(5, 0.0, sd, 0.8, kmax=500)
            line += f" | runs/side for 80% power at this noise: ±3 -> {k3 or '>500'}, ±5 -> {k5 or '>500'}"
        else:
            line += " | zero spread on both sides: no noise estimate"
        print(line)
