#!/usr/bin/env python3
"""Phase 0, number set C: error rates of the range-overlap rule under normal noise.

For k runs per side and a true gap of delta run-to-run SDs, report P(rule says MISMATCH):
  * sim   : Monte Carlo, 200,000 trials, fixed seed (reproduces the first pass)
  * exact : numerical integral (parity_lib.rule_mismatch_rate_normal)
  * closed: 2 (k!)^2 / (2k)! at delta = 0 (holds for any continuous noise)
Usage: python -I scripts/p0_rule_error_rates.py <out_dir> [n_trials]
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parity_lib import rule_false_alarm_binomial_sim, rule_false_alarm_exact, rule_mismatch_rate_normal, rule_mismatch_rate_sim  # noqa: E402

out = sys.argv[1]
n = int(sys.argv[2]) if len(sys.argv) > 2 else 200_000
os.makedirs(out, exist_ok=True)
KS, DELTAS = (2, 3, 5, 8), (0, 1, 2, 3, 4)

table = {}
for k in KS:
    table[k] = {d: {"sim": rule_mismatch_rate_sim(k, d, n=n), "exact": rule_mismatch_rate_normal(k, d)} for d in DELTAS}
closed = {k: rule_false_alarm_exact(k) for k in range(1, 11)}
exact_by_k = {k: {d: rule_mismatch_rate_normal(k, d) for d in (0, 0.5, 1, 1.5, 2, 2.5, 3, 4)} for k in range(1, 11)}

# discrete scores: pass rates over n_tasks tasks tie, and ties count as overlap -> fewer false alarms
discrete = {str(nt): rule_false_alarm_binomial_sim(3, nt, 0.4, n=n) for nt in (10, 30, 100, 300, 1000)}
# "rewards noise": P(pass) for a fixed true gap of 2 points at k=3 as the common run-to-run SD grows
noise = {str(sg): 1 - rule_mismatch_rate_normal(3, 2.0 / sg) for sg in (0.25, 0.5, 1, 1.5, 2.16, 3, 5, 10, 100)}
res = {"n_trials": n, "seed": 7,
       "discrete_false_alarm_k3_binomial_p0.4_by_n_tasks": discrete,
       "pass_prob_k3_true_gap_2_points_by_common_sd": noise,
       "sim": {str(k): {str(d): v["sim"] for d, v in row.items()} for k, row in table.items()},
       "exact": {str(k): {str(d): v["exact"] for d, v in row.items()} for k, row in table.items()},
       "closed_form_false_alarm": {str(k): v for k, v in closed.items()},
       "exact_extended": {str(k): {str(d): v for d, v in row.items()} for k, row in exact_by_k.items()}}
with open(os.path.join(out, "rule_error_rates.json"), "w") as fh:
    json.dump(res, fh, indent=1)

lines = ["P(rule says MISMATCH) by true gap in run-to-run SDs; sim (exact) per cell",
         "| k | gap 0 (false alarm) | 1 SD | 2 SD | 3 SD | 4 SD | closed form at 0 |", "|---|---|---|---|---|---|---|"]
for k in KS:
    cells = [f"{table[k][d]['sim']:.3f} ({table[k][d]['exact']:.3f})" for d in DELTAS]
    lines.append(f"| {k} | " + " | ".join(cells) + f" | {closed[k]:.4f} |")
lines += ["", "False alarm at k=3 when scores are pass rates over n tasks (binomial, p=0.4; ties count as overlap):",
          " | ".join(f"n={k}: {v:.3f}" for k, v in discrete.items()) + f" | continuous: {closed[3]:.3f}",
          "", "P(pass) at k=3 for a true gap of 2 points, by common run-to-run SD (points):",
          " | ".join(f"SD {k}: {v:.3f}" for k, v in noise.items())]
md = "\n".join(lines)
with open(os.path.join(out, "rule_error_rates.md"), "w") as fh:
    fh.write(md + "\n")
print(md)
