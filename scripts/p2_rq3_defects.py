#!/usr/bin/env python3
"""Phase 2, RQ3c: injected-defect study on real per-task outcomes.

For each adapter with Harbor-side per-task outcomes (data/pertask/<adapter>/harbor.csv, >= 20 tasks), a
task's pass probability is its Beta(1,1)-shrunk pass rate over the available runs. Under parity both
sides share these probabilities. A defect on the port side either BREAKS a random fraction f of tasks
(probability set to 0) or LEAKS them (probability set to 1). For k runs per side we simulate run
scores and apply each rule: R (range overlap), S1, S2 (SEM readings), W (Welch, p < .05), E3 and E5
(TOST at 3 and 5 points: "equivalence shown"), and the paired per-task test on the simulated per-task
outcomes (paired t on task-level differences, p < .05) with paired TOST at 3 and 5. Detection rate
over REPS replications. Pre-registered: f in {0.02, 0.05, 0.1, 0.2}, k in {3, 5, 10}, 2,000 replications.
Usage: python -I scripts/p2_rq3_defects.py <pertask_dir> <phase2_dir> [reps]
"""
import csv
import glob
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parity_lib import paired_task_verdicts, rule_verdicts  # noqa: E402

pertask_dir, p2 = sys.argv[1], sys.argv[2]
REPS = int(sys.argv[3]) if len(sys.argv) > 3 else 2000
FS, KS, CHUNK = (0.0, 0.02, 0.05, 0.1, 0.2), (3, 5, 10), 250  # f = 0 is the no-defect control (amendment 3)
rng = np.random.default_rng(7)


results = {}
for f in sorted(glob.glob(os.path.join(pertask_dir, "*", "harbor.csv"))):
    adapter = os.path.basename(os.path.dirname(f))
    by_task = {}
    for row in csv.DictReader(open(f)):
        try:
            by_task.setdefault(row["task_id"], []).append(float(row["reward"]))
        except ValueError:
            pass
    if len(by_task) < 20:
        continue
    vals = np.array([v for lst in by_task.values() for v in lst])
    scale = 1.0 if vals.max() <= 1.0 else 1 / 100
    p_i = np.array([(sum(v) * scale + 1) / (len(v) + 2) for v in by_task.values()])
    n = len(p_i)
    per = {"n_tasks": n, "base_rate_points": float(p_i.mean() * 100), "runs_per_task": float(np.mean([len(v) for v in by_task.values()]))}
    for kind in ("break", "leak"):
        for fr in FS:
            n_def = 0 if fr == 0 else max(1, int(round(fr * n)))
            for k in KS:
                acc = {}
                exp_gap = []
                for start in range(0, REPS, CHUNK):
                    reps = min(CHUNK, REPS - start)
                    pb = np.tile(p_i, (reps, 1))
                    for r in range(reps):
                        if n_def:
                            idx = rng.choice(n, n_def, replace=False)
                            pb[r, idx] = 0.0 if kind == "break" else 1.0
                    exp_gap.append(float(((pb - p_i).mean(1) * 100).mean()))
                    xa = rng.random((reps, k, n)) < p_i
                    xb = rng.random((reps, k, n)) < pb[:, None, :]
                    a, b = xa.mean(2) * 100, xb.mean(2) * 100
                    v = rule_verdicts(a, b, margins=(3, 5)); v.update(paired_task_verdicts(xa, xb))
                    for key, arr in v.items():
                        acc[key] = acc.get(key, 0) + int(arr.sum())
                per[f"{kind},f={fr},k={k}"] = {key: val / REPS for key, val in acc.items()} | {"expected_gap_points": float(np.mean(exp_gap)), "n_tasks_affected": n_def}
    results[adapter] = per
    print(f"{adapter}: n={n} base {per['base_rate_points']:.1f} | break f=0.1 k=3 gap {per['break,f=0.1,k=3']['expected_gap_points']:.1f} pts -> R {per['break,f=0.1,k=3']['R']:.2f} W {per['break,f=0.1,k=3']['W']:.2f} paired {per['break,f=0.1,k=3']['P']:.2f} | E5 shown {per['break,f=0.1,k=3']['E5']:.2f} paired E5 {per['break,f=0.1,k=3']['PE5']:.2f}")

# aggregate: mean detection over adapters per cell
agg = {}
cells = [key for key in next(iter(results.values())) if "," in key] if results else []
for cell in cells:
    agg[cell] = {rule: float(np.mean([results[a][cell][rule] for a in results])) for rule in ("R", "S1", "S2", "W", "E3", "E5", "P", "PE3", "PE5")}
    agg[cell]["expected_gap_points_median"] = float(np.median([results[a][cell]["expected_gap_points"] for a in results]))
with open(os.path.join(p2, "rq3_defects.json"), "w") as fh:
    json.dump({"reps": REPS, "fractions": FS, "ks": KS, "n_adapters": len(results), "aggregate": agg, "adapters": results}, fh, indent=1)

if results:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    os.makedirs(os.path.join(p2, "figures"), exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.4), sharey=True)
    for ax, kind in zip(axes, ("break", "leak")):
        for rule, lab, ls in (("R", "range overlap", "-"), ("S1", "SEM bars overlap", "--"), ("W", "Welch t-test", ":"), ("P", "paired per-task t-test", "-")):
            ax.plot(FS, [agg[f"{kind},f={fr},k=3"][rule] for fr in FS], ls, marker="o", ms=3, label=lab)
        ax.axvline(0, color="grey", lw=0.5)
        ax.set_xlabel(f"fraction of tasks {'broken' if kind == 'break' else 'leaked'} on the port side"); ax.set_title(f"{kind} defect, k = 3, mean over {len(results)} adapters", fontsize=10)
        ax.set_ylim(0, 1)
    axes[0].set_ylabel("P(defect detected)"); axes[0].legend(fontsize=7, frameon=False)
    fig.tight_layout(); fig.savefig(os.path.join(p2, "figures", "fig_rq3_defects.png"), dpi=200); fig.savefig(os.path.join(p2, "figures", "fig_rq3_defects.pdf"))
print("adapters:", len(results))
for cell in ("break,f=0.0,k=3", "break,f=0.05,k=3", "break,f=0.1,k=3", "break,f=0.2,k=3", "leak,f=0.1,k=3", "break,f=0.0,k=10", "break,f=0.1,k=10"):
    if cell in agg:
        print(cell, {r: round(v, 2) for r, v in agg[cell].items()})
