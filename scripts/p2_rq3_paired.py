#!/usr/bin/env python3
"""Phase 2, RQ3b: paired per-task analysis of parity experiments.

For each adapter in the primary paired set (data/pertask/MANIFEST.json use_for_paired and not a
Terminal-Bench leg; amendment 6a), tasks are aligned by id across all runs on both sides and compared
task by task: d_i = Harbor task mean - original task mean (points). Reported per adapter:
  paired estimate = mean d_i; 90% and 95% task-level bootstrap intervals (10,000 resamples, seed 7);
  paired smallest provable margin = farthest end of the 90% interval from zero;
  run-level (unpaired) 90% interval from the same files' run means (pooled t), for comparison;
  diagnostics (amendment 6d): a within-task permutation test (2,000 permutations) of whether the
  task-level spread of d_i exceeds what shared per-task probabilities produce; the permutation null of
  the run/paired width ratio; the two-sided permutation p-value of the mean gap (exchangeability);
  per side, the dispersion ratio of real run scores (observed between-run variance over the variance
  implied by within-task flip rates); the CMH z test on binary outcomes.
Validation: recovered run means are matched to the published run lists (original, harbor and
tb_adapter fields); the crustbench swap and other documented cases are read from the manifest.
Usage: python -I scripts/p2_rq3_paired.py <pertask_dir> <snapshot_dir> <phase2_dir>
"""
import csv
import glob
import json
import math
import os
import statistics
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parity_lib import diff_ci_halfwidth, iter_experiments, lenient_runs, paired_task_verdicts, t_quantile  # noqa: E402

pertask_dir, snap, p2 = sys.argv[1:4]
rng = np.random.default_rng(7)
B, NPERM = 10_000, 2_000
manifest = json.load(open(os.path.join(pertask_dir, "MANIFEST.json")))["adapters"]


def load(path, drop):
    runs = {}
    for r in csv.DictReader(open(path)):
        try:
            k = int(float(r["run"]))
            if k in drop:
                continue
            runs.setdefault(k, {})[r["task_id"]] = float(r["reward"])
        except (ValueError, KeyError):
            continue
    return runs


def published_runs(adapter):
    out = []
    for a, i, e in iter_experiments(snap):
        if a != adapter:
            continue
        for m in e.get("metrics") or []:
            for side in ("original", "harbor", "tb_adapter"):
                for suf in ("_runs", "_trials"):
                    v = lenient_runs(m.get(side + suf))
                    if v:
                        sc = 100 if max(v) <= 1.0 else 1
                        out.append((i, m.get("metric"), side, sorted(round(x * sc, 2) for x in v)))
    return out


def matches(means, adapter, sides):
    got = sorted(round(x, 2) for x in means)
    for i, metric, s, pub in published_runs(adapter):
        if s in sides and len(pub) == len(got) and all(abs(x - y) <= 0.15 for x, y in zip(got, pub)):
            return f"match exp{i} {s} {metric}"
    return "no match"


def dispersion(X):
    """X: runs x tasks. Observed var of run means / implied var from within-task variances; None if k < 2."""
    if X.shape[0] < 2:
        return None
    implied = X.var(0, ddof=1).sum() / X.shape[1] ** 2
    return float(X.mean(1).var(ddof=1) / implied) if implied > 0 else None


results, rows = {}, []
for d in sorted(glob.glob(os.path.join(pertask_dir, "*"))):
    adapter = os.path.basename(d)
    m = manifest.get(adapter, {})
    fo, fh = os.path.join(d, "original.csv"), os.path.join(d, "harbor.csv")
    if not (os.path.exists(fo) and os.path.exists(fh)):
        continue
    if not m.get("use_for_paired"):
        results[adapter] = {"status": "excluded by manifest", "reason": m.get("paired_note") or m.get("replicate_note") or "validation against published run scores failed"}
        continue
    drop = m.get("drop_runs") or {}
    ro, rh = load(fo, set(drop.get("original", []))), load(fh, set(drop.get("harbor", [])))
    if not ro or not rh:
        continue
    scale = 100.0 if max(max(v.values()) for v in list(ro.values()) + list(rh.values())) <= 1.0 else 1.0
    tasks_o = set.intersection(*[set(v) for v in ro.values()]); tasks_h = set.intersection(*[set(v) for v in rh.values()])
    common = sorted(tasks_o & tasks_h)
    if len(common) < 20:
        results[adapter] = {"status": "too few common tasks", "n_common": len(common)}
        continue
    po = np.array([[ro[r][t] * scale for t in common] for r in sorted(ro)])  # runs x tasks
    ph = np.array([[rh[r][t] * scale for t in common] for r in sorted(rh)])
    ka, kb, n = po.shape[0], ph.shape[0], len(common)
    task_o, task_h = po.mean(0), ph.mean(0)
    d_i = task_h - task_o
    est = float(d_i.mean())
    idx = rng.integers(0, n, (B, n))
    boot = d_i[idx].mean(1)
    lo90, hi90 = np.percentile(boot, [5, 95]); lo95, hi95 = np.percentile(boot, [2.5, 97.5])
    paired_margin = float(max(abs(lo90), abs(hi90)))
    run_o, run_h = po.mean(1).tolist(), ph.mean(1).tolist()
    run_gap = statistics.mean(run_h) - statistics.mean(run_o)
    if min(ka, kb) >= 2:
        hw90 = diff_ci_halfwidth(run_o, run_h, 0.90); hw95 = diff_ci_halfwidth(run_o, run_h, 0.95)
        run_margin = abs(run_gap) + hw90
    else:
        hw90 = hw95 = run_margin = None
    paired_hw90 = float((hi90 - lo90) / 2)
    ratio = (hw90 / paired_hw90) if (hw90 is not None and paired_hw90 > 0) else None
    # ---- within-task permutation null: shuffle each task's ka + kb outcomes across the run slots
    X = np.concatenate([po, ph], 0)  # (ka+kb) x n
    sd_obs = float(d_i.std(ddof=1))
    perm_sd, perm_gap, perm_ratio = np.empty(NPERM), np.empty(NPERM), np.empty(NPERM)
    for b in range(NPERM):
        order = np.argsort(rng.random(X.shape), axis=0)
        Xp = np.take_along_axis(X, order, axis=0)
        da = Xp[ka:].mean(0) - Xp[:ka].mean(0)
        perm_sd[b] = da.std(ddof=1); perm_gap[b] = da.mean()
        if hw90 is not None:
            ro_, rh_ = Xp[:ka].mean(1), Xp[ka:].mean(1)
            sp = math.sqrt(((ka - 1) * ro_.var(ddof=1) + (kb - 1) * rh_.var(ddof=1)) / (ka + kb - 2))
            hw_run = t_quantile(0.95, ka + kb - 2) * sp * math.sqrt(1 / ka + 1 / kb)
            hw_pair = 1.645 * da.std(ddof=1) / math.sqrt(n)
            perm_ratio[b] = hw_run / hw_pair if hw_pair > 0 else np.nan
    p_sd = float((np.sum(perm_sd >= sd_obs) + 1) / (NPERM + 1))
    p_gap = float((np.sum(np.abs(perm_gap) >= abs(est)) + 1) / (NPERM + 1))
    null_ratio = [float(x) for x in np.nanpercentile(perm_ratio, [25, 50, 75])] if hw90 is not None else None
    ratio_pct = float(np.nanmean(perm_ratio <= ratio)) if (ratio is not None) else None
    binary = bool(np.all(np.isin(X, [0.0, 100.0])))
    cmh = None
    if binary:
        v = paired_task_verdicts((po[None] / 100), (ph[None] / 100), margins=(3,))
        cmh = bool(v["CMH"][0])
    rec = {"status": "ok", "secondary_leg": bool(m.get("paired_secondary_leg")), "n_common": n, "n_original_tasks": len(tasks_o), "n_harbor_tasks": len(tasks_h),
           "k_original": ka, "k_harbor": kb, "binary_outcomes": binary, "manifest_note": m.get("paired_note"),
           "validation_original": matches(run_o, adapter, ("original", "tb_adapter")), "validation_harbor": matches(run_h, adapter, ("harbor",)),
           "sides_swapped_vs_published": adapter == "crustbench",
           "mean_original": float(task_o.mean()), "mean_harbor": float(task_h.mean()),
           "paired_gap": est, "paired_ci90": [float(lo90), float(hi90)], "paired_ci95": [float(lo95), float(hi95)],
           "paired_halfwidth90": paired_hw90, "paired_smallest_margin": paired_margin,
           "run_gap": float(run_gap), "run_halfwidth90": hw90, "run_halfwidth95": hw95, "run_smallest_margin": run_margin,
           "width_ratio_run_over_paired": ratio, "width_ratio_null_quartiles": null_ratio, "width_ratio_percentile_in_null": ratio_pct,
           "sd_of_task_differences": sd_obs, "p_sd_task_differences_exceeds_shared_noise": p_sd, "p_mean_gap_exchangeable": p_gap,
           "cmh_reject_at_0.05": cmh,
           "dispersion_ratio_original": dispersion(po), "dispersion_ratio_harbor": dispersion(ph),
           "tasks_with_different_pass_rate": int(np.sum(task_o != task_h)), "share_tasks_discordant": float(np.mean(task_o != task_h))}
    results[adapter] = rec
    rows.append({"adapter": adapter, **{k: (round(v, 4) if isinstance(v, float) else v) for k, v in rec.items() if k not in ("paired_ci90", "paired_ci95", "width_ratio_null_quartiles")}})

primary = {a: r for a, r in results.items() if r.get("status") == "ok" and not r["secondary_leg"]}
secondary = {a: r for a, r in results.items() if r.get("status") == "ok" and r["secondary_leg"]}


def summarise(S):
    if not S:
        return {"n": 0}
    both = [r for r in S.values() if r["run_smallest_margin"] is not None]
    ratios = [r["width_ratio_run_over_paired"] for r in both if r["width_ratio_run_over_paired"] is not None]
    return {"n": len(S), "n_with_run_interval": len(both),
            "validation_both_match": sum(1 for r in S.values() if r["validation_original"].startswith("match") and r["validation_harbor"].startswith("match")),
            "paired_margin_quartiles": [float(x) for x in np.percentile([r["paired_smallest_margin"] for r in S.values()], [25, 50, 75])],
            "run_margin_quartiles": [float(x) for x in np.percentile([r["run_smallest_margin"] for r in both], [25, 50, 75])] if both else None,
            "width_ratio_quartiles": [float(x) for x in np.percentile(ratios, [25, 50, 75])] if ratios else None,
            "width_ratio_null_median_quartiles": [float(x) for x in np.percentile([r["width_ratio_null_quartiles"][1] for r in both if r["width_ratio_null_quartiles"]], [25, 50, 75])] if both else None,
            "n_ratio_below_1": sum(1 for x in ratios if x < 1), "n_ratio_below_null_q25": sum(1 for r in both if r["width_ratio_run_over_paired"] is not None and r["width_ratio_null_quartiles"] and r["width_ratio_run_over_paired"] < r["width_ratio_null_quartiles"][0]),
            "paired_within": {str(m): sum(1 for r in both if r["paired_smallest_margin"] <= m) for m in (1, 2, 3, 5)},
            "run_within": {str(m): sum(1 for r in both if r["run_smallest_margin"] <= m) for m in (1, 2, 3, 5)},
            "n_sd_task_diff_exceeds_noise_p05": sum(1 for r in S.values() if r["p_sd_task_differences_exceeds_shared_noise"] < 0.05),
            "n_sd_task_diff_exceeds_noise_p01": sum(1 for r in S.values() if r["p_sd_task_differences_exceeds_shared_noise"] < 0.01),
            "n_mean_gap_not_exchangeable_p05": sum(1 for r in S.values() if r["p_mean_gap_exchangeable"] < 0.05),
            "n_cmh_reject": sum(1 for r in S.values() if r["cmh_reject_at_0.05"]), "n_binary": sum(1 for r in S.values() if r["binary_outcomes"]),
            "paired_gap_distinguishable_95": sum(1 for r in S.values() if r["paired_ci95"][0] > 0 or r["paired_ci95"][1] < 0),
            "dispersion_ratio_harbor_quartiles": [float(x) for x in np.percentile([r["dispersion_ratio_harbor"] for r in both if r["dispersion_ratio_harbor"] is not None], [25, 50, 75])] if both else None,
            "dispersion_ratio_original_quartiles": [float(x) for x in np.percentile([r["dispersion_ratio_original"] for r in both if r["dispersion_ratio_original"] is not None], [25, 50, 75])] if both else None,
            "under_dispersed_below_0.1": sorted(a for a, r in S.items() if any((r[f"dispersion_ratio_{s}"] or 1) < 0.1 for s in ("original", "harbor"))),
            "discordance_share_quartiles": [float(x) for x in np.percentile([r["share_tasks_discordant"] for r in S.values()], [25, 50, 75])]}


summary = {"primary": summarise(primary), "secondary_terminal_bench_legs": summarise(secondary), "excluded": {a: r for a, r in results.items() if r.get("status") != "ok"}}
with open(os.path.join(p2, "rq3_paired.json"), "w") as fh:
    json.dump({"summary": summary, "adapters": results}, fh, indent=1)
if rows:
    with open(os.path.join(p2, "rq3_paired.csv"), "w", newline="") as fh:
        fields = list(dict.fromkeys(k for r in rows for k in r))
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
print(json.dumps({k: v for k, v in summary["primary"].items()}, indent=1))
print("secondary legs:", {k: summary["secondary_terminal_bench_legs"].get(k) for k in ("n", "paired_margin_quartiles", "run_margin_quartiles")})
for a, r in results.items():
    if r.get("status") == "ok":
        print(f"{'[leg] ' if r['secondary_leg'] else ''}{a}: n={r['n_common']} k={r['k_original']}v{r['k_harbor']} | paired {r['paired_gap']:+.2f} [{r['paired_ci90'][0]:+.2f},{r['paired_ci90'][1]:+.2f}] m={r['paired_smallest_margin']:.2f} | run m={r['run_smallest_margin'] if r['run_smallest_margin'] is None else round(r['run_smallest_margin'], 2)} ratio={None if r['width_ratio_run_over_paired'] is None else round(r['width_ratio_run_over_paired'], 2)} null={None if not r['width_ratio_null_quartiles'] else round(r['width_ratio_null_quartiles'][1], 2)} | p_sd={r['p_sd_task_differences_exceeds_shared_noise']:.3f} p_gap={r['p_mean_gap_exchangeable']:.2f} cmh={r['cmh_reject_at_0.05']} | disp o/h={None if r['dispersion_ratio_original'] is None else round(r['dispersion_ratio_original'], 2)}/{None if r['dispersion_ratio_harbor'] is None else round(r['dispersion_ratio_harbor'], 2)} | {r['validation_original'][:9]}/{r['validation_harbor'][:9]}")
