#!/usr/bin/env python3
"""Phase 2, RQ3 follow-up: how often would a dispersion ratio below 0.1 arise by chance?

For each adapter in the injected-defect study (binary outcomes, validated replicate Harbor runs), draw
independent per-task outcomes from its light-shrinkage pass probabilities at its own run count, compute
the same dispersion ratio as scripts/p2_rq3_defects.py (observed between-run variance of the run score
over the variance implied by within-task flip rates), and record P(ratio < 0.1) under independence.
The expected number of adapters below 0.1 is the sum of these probabilities; the chance of at least the
observed count is from a Poisson-binomial tail (by convolution).
Usage: python -I scripts/p2_rq3_dispersion_null.py <pertask_dir> <phase2_dir> [reps]
"""
import csv
import json
import os
import sys

import numpy as np

pertask_dir, p2 = sys.argv[1], sys.argv[2]
REPS = int(sys.argv[3]) if len(sys.argv) > 3 else 20000
rng = np.random.default_rng(11)
man = json.load(open(os.path.join(pertask_dir, "MANIFEST.json")))["adapters"]
defects = json.load(open(os.path.join(p2, "rq3_defects.json")))
adapters = sorted(a for a, v in defects["adapters"].items() if v.get("binary_outcomes") and "break,f=0.0,k=3" in v)
assert len(adapters) == defects["summary"]["n_binary"], (len(adapters), defects["summary"]["n_binary"])


def load_tasks(adapter):
    """Same loader as p2_rq3_defects.py: {task_id: [rewards over runs]} for the Harbor side."""
    drop = set((man[adapter].get("drop_runs") or {}).get("harbor", []))
    by_task = {}
    for row in csv.DictReader(open(os.path.join(pertask_dir, adapter, "harbor.csv"))):
        try:
            run, rew = int(float(row["run"])), float(row["reward"])
        except ValueError:
            continue
        if run in drop:
            continue
        by_task.setdefault(row["task_id"], []).append(rew)
    vals = np.array([v for lst in by_task.values() for v in lst])
    sc = 1.0 if vals.max() <= 1.0 else 0.01
    return {t: [x * sc for x in v] for t, v in by_task.items()}


def dispersion_ratio_matrix(X):
    """X is tasks x runs. Same ratio as in p2_rq3_defects.run_dispersion."""
    obs = X.mean(0).var(ddof=1)
    implied = X.var(1, ddof=1).sum() / X.shape[0] ** 2
    return obs / implied if implied > 0 else np.nan


out = {"reps": REPS, "threshold": 0.1, "adapters": {}}
probs = []
for a in adapters:
    by_task = load_tasks(a)
    runs = max(len(v) for v in by_task.values())
    full = np.array([v for v in by_task.values() if len(v) == runs])
    if runs < 2 or len(full) < 2:
        continue
    n = len(full)
    p = (full.sum(1) + 0.05) / (runs + 0.1)  # light shrinkage, amendment 5
    observed = float(dispersion_ratio_matrix(full))
    below = 0
    for start in range(0, REPS, 500):
        r = min(500, REPS - start)
        draws = rng.random((r, n, runs)) < p[None, :, None]
        X = draws.astype(float)
        obs = X.mean(1).var(axis=1, ddof=1)
        implied = X.var(axis=2, ddof=1).sum(axis=1) / n ** 2
        ratio = np.where(implied > 0, obs / np.where(implied > 0, implied, 1), np.nan)
        below += int(np.nansum(ratio < 0.1))
    pr = below / REPS
    probs.append(pr)
    out["adapters"][a] = {"runs": runs, "n_tasks": n, "observed_ratio": round(observed, 4), "observed_ratio_exact": observed, "p_ratio_below_0.1_under_independence": round(pr, 4)}
obs_count = sum(1 for v in out["adapters"].values() if v["observed_ratio_exact"] < 0.1 + 1e-9)
# Poisson-binomial distribution of the count under independence
dist = np.array([1.0])
for pr in probs:
    dist = np.convolve(dist, [1 - pr, pr])
out["summary"] = {"n_adapters": len(probs), "expected_below_0.1_under_independence": round(float(sum(probs)), 2),
                  "observed_below_0.1": obs_count, "p_at_least_observed_under_independence": round(float(dist[obs_count:].sum()), 4),
                  "per_adapter_prob_quartiles": [round(float(x), 3) for x in np.percentile(probs, [25, 50, 75])]}
json.dump(out, open(os.path.join(p2, "rq3_dispersion_null.json"), "w"), indent=1)
print(json.dumps(out["summary"]))
