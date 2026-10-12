#!/usr/bin/env python3
"""Phase 2, RQ3b: paired per-task analysis of parity experiments.

For each adapter with recovered per-task outcomes on both sides (data/pertask/<adapter>/{original,harbor}.csv,
columns run,task_id,reward), align tasks by id and compare the sides task by task:
  d_i = mean reward of task i on the Harbor side - mean reward of task i on the original side (points)
  paired estimate = mean of d_i over common tasks; 90% and 95% intervals by task-level bootstrap
  (10,000 resamples, seed 7, percentile method); paired smallest provable margin = the farthest end of
  the 90% interval from zero, i.e. equivalence within ±m is shown iff the 90% interval lies in [-m, m].
Next to it, the run-level (unpaired) 90% interval computed from the same files' run means with the
pooled t, so the two interval widths can be compared on identical data. Also validates the recovered
run means against the published run lists.
Usage: python -I scripts/p2_rq3_paired.py <pertask_dir> <snapshot_dir> <phase2_dir>
"""
import csv
import glob
import json
import os
import statistics
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parity_lib import diff_ci_halfwidth, iter_experiments, lenient_runs  # noqa: E402

pertask_dir, snap, p2 = sys.argv[1:4]
rng = np.random.default_rng(7)
B = 10_000


def load(path):
    runs = {}
    for r in csv.DictReader(open(path)):
        try:
            runs.setdefault(int(float(r["run"])), {})[r["task_id"]] = float(r["reward"])
        except (ValueError, KeyError):
            continue
    return runs


def published_runs(adapter):
    """All published run lists for this adapter (any experiment), in points."""
    out = []
    for a, i, e in iter_experiments(snap):
        if a != adapter:
            continue
        for m in e.get("metrics") or []:
            for side in ("original", "harbor"):
                for suf in ("_runs", "_trials"):
                    v = lenient_runs(m.get(side + suf))
                    if v:
                        sc = 100 if max(v) <= 1.0 else 1
                        out.append((i, m.get("metric"), side, sorted(round(x * sc, 2) for x in v)))
    return out


def matches(means, adapter, side):
    """Does the multiset of recovered run means match some published run list within 0.15 points?"""
    got = sorted(round(x, 2) for x in means)
    for i, metric, s, pub in published_runs(adapter):
        if s == side and len(pub) == len(got) and all(abs(x - y) <= 0.15 for x, y in zip(got, pub)):
            return f"match exp{i} {metric}"
    return f"no match (recovered {got})"


results, rows = {}, []
for d in sorted(glob.glob(os.path.join(pertask_dir, "*"))):
    adapter = os.path.basename(d)
    fo, fh = os.path.join(d, "original.csv"), os.path.join(d, "harbor.csv")
    if not (os.path.exists(fo) and os.path.exists(fh)):
        continue
    ro, rh = load(fo), load(fh)
    if not ro or not rh:
        continue
    scale = 100.0 if max(max(v.values()) for v in list(ro.values()) + list(rh.values())) <= 1.0 else 1.0
    tasks_o = set.intersection(*[set(v) for v in ro.values()]); tasks_h = set.intersection(*[set(v) for v in rh.values()])
    common = sorted(tasks_o & tasks_h)
    if len(common) < 5:
        results[adapter] = {"status": "too few common tasks", "n_common": len(common), "n_original": len(tasks_o), "n_harbor": len(tasks_h)}
        continue
    po = np.array([[ro[r][t] * scale for t in common] for r in sorted(ro)])  # runs x tasks
    ph = np.array([[rh[r][t] * scale for t in common] for r in sorted(rh)])
    task_o, task_h = po.mean(0), ph.mean(0)
    d_i = task_h - task_o
    est = float(d_i.mean())
    idx = rng.integers(0, len(common), (B, len(common)))
    boot = d_i[idx].mean(1)
    lo90, hi90 = np.percentile(boot, [5, 95]); lo95, hi95 = np.percentile(boot, [2.5, 97.5])
    paired_margin = float(max(abs(lo90), abs(hi90)))
    # run-level, unpaired, from the same files
    run_o, run_h = po.mean(1).tolist(), ph.mean(1).tolist()
    run_gap = statistics.mean(run_h) - statistics.mean(run_o)
    if min(len(run_o), len(run_h)) >= 2:
        hw90 = diff_ci_halfwidth(run_o, run_h, 0.90); hw95 = diff_ci_halfwidth(run_o, run_h, 0.95)
        run_margin = abs(run_gap) + hw90
    else:
        hw90 = hw95 = run_margin = float("nan")
    binary = bool(np.all(np.isin(np.concatenate([po.ravel(), ph.ravel()]), [0.0, scale])))
    discordant = int(np.sum(task_o != task_h))
    swapped = matches(run_o, adapter, "harbor").startswith("match") and matches(run_h, adapter, "original").startswith("match") \
        and not (matches(run_o, adapter, "original").startswith("match") and matches(run_h, adapter, "harbor").startswith("match"))
    rec = {"status": "ok", "n_common": len(common), "n_original_tasks": len(tasks_o), "n_harbor_tasks": len(tasks_h),
           "sides_swapped_vs_published": swapped,
           "k_original": po.shape[0], "k_harbor": ph.shape[0], "binary_outcomes": binary,
           "validation_original": matches(run_o, adapter, "original"), "validation_harbor": matches(run_h, adapter, "harbor"),
           "mean_original": float(task_o.mean()), "mean_harbor": float(task_h.mean()),
           "paired_gap": est, "paired_ci90": [float(lo90), float(hi90)], "paired_ci95": [float(lo95), float(hi95)],
           "paired_halfwidth90": float((hi90 - lo90) / 2), "paired_smallest_margin": paired_margin,
           "run_gap": float(run_gap), "run_halfwidth90": float(hw90), "run_halfwidth95": float(hw95), "run_smallest_margin": float(run_margin),
           "width_ratio_run_over_paired": float(hw90 / ((hi90 - lo90) / 2)) if (hi90 - lo90) > 0 and hw90 == hw90 else None,
           "tasks_with_different_pass_rate": discordant, "share_tasks_discordant": discordant / len(common),
           "sd_of_task_differences": float(d_i.std(ddof=1))}
    results[adapter] = rec
    rows.append({"adapter": adapter, **{k: (round(v, 3) if isinstance(v, float) else v) for k, v in rec.items() if not isinstance(v, list)}})

ok = [r for r in results.values() if r.get("status") == "ok"]
summary = {"n_adapters_with_both_sides": len(ok), "n_adapters_skipped": len(results) - len(ok),
           "validation_both_match": sum(1 for r in ok if r["validation_original"].startswith("match") and r["validation_harbor"].startswith("match")),
           "sides_swapped_vs_published": [a for a, r in results.items() if r.get("sides_swapped_vs_published")],
           "paired_margin_quartiles": [float(x) for x in np.percentile([r["paired_smallest_margin"] for r in ok], [25, 50, 75])] if ok else None,
           "run_margin_quartiles": [float(x) for x in np.percentile([r["run_smallest_margin"] for r in ok if r["run_smallest_margin"] == r["run_smallest_margin"]], [25, 50, 75])] if ok else None,
           "width_ratio_quartiles": [float(x) for x in np.percentile([r["width_ratio_run_over_paired"] for r in ok if r["width_ratio_run_over_paired"]], [25, 50, 75])] if ok else None,
           "paired_within": {str(m): sum(1 for r in ok if r["paired_smallest_margin"] <= m) for m in (1, 2, 3, 5)},
           "run_within": {str(m): sum(1 for r in ok if r["run_smallest_margin"] <= m) for m in (1, 2, 3, 5)},
           "paired_gap_distinguishable_95": sum(1 for r in ok if r["paired_ci95"][0] > 0 or r["paired_ci95"][1] < 0)}
with open(os.path.join(p2, "rq3_paired.json"), "w") as fh:
    json.dump({"summary": summary, "adapters": results}, fh, indent=1)
if rows:
    with open(os.path.join(p2, "rq3_paired.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(json.dumps(summary, indent=1))
for a, r in results.items():
    if r.get("status") == "ok":
        print(f"{a}: n={r['n_common']} k={r['k_original']}v{r['k_harbor']} | paired gap {r['paired_gap']:+.2f} [90%: {r['paired_ci90'][0]:+.2f}, {r['paired_ci90'][1]:+.2f}] margin {r['paired_smallest_margin']:.2f} | run-level gap {r['run_gap']:+.2f} ± {r['run_halfwidth90']:.2f} margin {r['run_smallest_margin']:.2f} | width ratio {r['width_ratio_run_over_paired']} | discordant tasks {r['share_tasks_discordant']:.2f} | valid: {r['validation_original'][:12]} / {r['validation_harbor'][:12]}")
    else:
        print(f"{a}: {r}")
