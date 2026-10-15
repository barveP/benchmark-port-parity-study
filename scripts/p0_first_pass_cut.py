#!/usr/bin/env python3
"""Phase 0, number set D: the first pass's "one main metric per experiment" cut (43 comparisons),
plus the sensitivity variants and the power calculation that the independent review asked for.

BASE variant reproduces scripts/first_pass/parity_clean.py and scripts/first_pass/parity_tost.py EXACTLY, including the
crude metric filter (to be replaced by a rule written down before Phase 2). Selection, per
experiment, over its metric rows in file order:
  1. original_runs and harbor_runs are lists (BASE: *_runs only; variant "trials": fall back to
     *_trials as the overlap pass does); keep numeric entries (variant "lenient": also parse
     strings such as "58.3%")
  2. exactly 3 runs on each side
  3. metric name (lower-cased) contains none of: stderr, std, missing, cost, token, time, latency
  4. all six values lie in [0, 100]; if all are <= 1.0 they are fractions and are scaled by 100
  5. the first metric passing 1-4 is the experiment's main metric. If both sides have zero spread
     the experiment is dropped (no later metric is tried).
Statistics per comparison (a = original runs, b = harbor runs):
  s     = pooled run-to-run SD = sqrt((var(a) + var(b)) / 2), sample variances
  gap   = |mean(a) - mean(b)|
  hw95  = t(0.975, 4) * s * sqrt(2/3)   95% CI half-width on the gap (pooled t, 4 df)
  hw90  = t(0.95, 4)  * s * sqrt(2/3)   90% CI half-width = the TOST interval at alpha 0.05
  equivalence within +-m shown by TOST (alpha .05) iff gap + hw90 <= m; by the 95% CI iff gap + hw95 <= m
  gap distinguishable from zero at the 95% level iff gap > hw95
  Welch variants of hw90/hw95 (unequal variances, Satterthwaite df) are reported as a sensitivity check.
Runs needed:
  plug-in (first pass): smallest k with 0.6 + t(0.95, 2k-2) * s_med * sqrt(2/k) <= m
  power-based: smallest k with P(TOST passes | true gap 0.6, sigma = s_med) >= 80% (and 90%)
Usage: python -I scripts/p0_first_pass_cut.py <snapshot_dir> <out_dir>
"""
import csv
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parity_lib import (diff_ci_halfwidth, iter_experiments, lenient_runs, mean, numeric_runs, pooled_sd,  # noqa: E402
                        ranges_overlap, runs_needed_plugin, runs_needed_power, t_quantile, welch_ci_halfwidth,
                        zero_spread)

SIDE_WORDS = ("stderr", "std", "missing", "cost", "token", "time", "latency")
MARGINS = (1, 2, 3, 5, 10)
root, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)


def select(use_trials: bool, lenient: bool):
    """Return (selected rows, rows excluded for zero spread, n_experiments) under a variant."""
    parse = lenient_runs if lenient else numeric_runs
    selected, excluded, n_exp = [], [], 0
    for adapter, i, e in iter_experiments(root):
        n_exp += 1
        for m in e.get("metrics") or []:
            a = b = None
            for suf in (("_runs", "_trials") if use_trials else ("_runs",)):
                a = a if a else (parse(m.get("original" + suf)) if isinstance(m.get("original" + suf), list) else None)
                b = b if b else (parse(m.get("harbor" + suf)) if isinstance(m.get("harbor" + suf), list) else None)
            if not (a and b) or len(a) != 3 or len(b) != 3:
                continue
            name = str(m.get("metric", "")).lower()
            if any(w in name for w in SIDE_WORDS):
                continue
            vals = a + b
            if min(vals) < 0 or max(vals) > 100:
                continue
            scale = 100.0 if max(vals) <= 1.0 else 1.0
            a, b = [x * scale for x in a], [x * scale for x in b]
            row = {"adapter": adapter, "exp": i, "agent": e.get("agent"), "model": e.get("model"),
                   "metric": m.get("metric"), "scaled_x100": scale == 100.0, "original_runs": a, "harbor_runs": b,
                   "raw_len_original": len(m.get("original_runs") or m.get("original_trials") or []),
                   "raw_len_harbor": len(m.get("harbor_runs") or m.get("harbor_trials") or [])}
            (excluded if zero_spread(a) and zero_spread(b) else selected).append(row)
            break
    return selected, excluded, n_exp


def analyse(selected):
    for r in selected:
        a, b = r["original_runs"], r["harbor_runs"]
        r["pooled_sd"] = s = pooled_sd(a, b)
        r["gap"] = g = abs(mean(a) - mean(b))
        r["mean_original"], r["mean_harbor"] = mean(a), mean(b)
        r["hw95"], r["hw90"] = diff_ci_halfwidth(a, b, 0.95), diff_ci_halfwidth(a, b, 0.90)
        r["hw95_welch"], r["hw90_welch"] = welch_ci_halfwidth(a, b, 0.95), welch_ci_halfwidth(a, b, 0.90)
        r["fails_overlap"] = not ranges_overlap(a, b)
        r["distinguishable_from_zero"] = g > r["hw95"]
        r["smallest_margin_tost"] = g + r["hw90"]
        r["smallest_margin_ci95"] = g + r["hw95"]
        r["smallest_margin_tost_welch"] = g + r["hw90_welch"]
        r["identical_lists"] = a == b
        r["zero_spread_one_side"] = zero_spread(a) != zero_spread(b)
    n = len(selected)
    gaps = np.array([r["gap"] for r in selected]); sds = np.array([r["pooled_sd"] for r in selected])
    hw90 = np.array([r["hw90"] for r in selected]); hw95 = np.array([r["hw95"] for r in selected])
    hw90w = np.array([r["hw90_welch"] for r in selected])
    return {
        "n_analysed": n,
        "median_pooled_sd": float(np.median(sds)), "median_gap": float(np.median(gaps)),
        "largest_gaps": [(r["adapter"], r["metric"], round(r["gap"], 2)) for r in sorted(selected, key=lambda r: -r["gap"])[:5]],
        "n_fail_overlap": int(sum(r["fails_overlap"] for r in selected)),
        "fail_overlap_rows": [(r["adapter"], r["metric"], r["original_runs"], r["harbor_runs"]) for r in selected if r["fails_overlap"]],
        "tost_within": {str(m): int(np.sum(gaps + hw90 <= m)) for m in MARGINS},
        "ci95_within": {str(m): int(np.sum(gaps + hw95 <= m)) for m in MARGINS},
        "tost_within_welch": {str(m): int(np.sum(gaps + hw90w <= m)) for m in MARGINS},
        "n_distinguishable_from_zero": int(np.sum(gaps > hw95)),
        "median_hw95": float(np.median(hw95)), "median_hw90": float(np.median(hw90)),
        "smallest_margin_tost_quartiles": [float(x) for x in np.percentile(gaps + hw90, [25, 50, 75])],
        "n_identical_lists_in_set": int(sum(r["identical_lists"] for r in selected)),
        "n_zero_spread_one_side_in_set": int(sum(r["zero_spread_one_side"] for r in selected)),
        "knife_edge_rows": [(r["adapter"], r["metric"], m, round(r["smallest_margin_tost"], 4)) for r in selected
                            for m in MARGINS if abs(r["smallest_margin_tost"] - m) < 0.05],
    }


variants = {"base": (False, False), "trials": (True, False), "lenient": (False, True), "trials+lenient": (True, True)}
results = {}
for name, (ut, le) in variants.items():
    sel, exc, n_exp = select(ut, le)
    res = analyse(sel)
    res.update({"n_experiments": n_exp, "n_selected_incl_zero_spread": len(sel) + len(exc), "n_excluded_zero_spread_both": len(exc)})
    results[name] = (res, sel)

base, selected = results["base"]
s_med, gap_med = base["median_pooled_sd"], base["median_gap"]
base["runs_needed_plugin_gap0.6_median_sd"] = {str(m): runs_needed_plugin(m, 0.6, s_med) for m in (2, 3, 5)}
base["runs_needed_power80_gap0.6_median_sd"] = {str(m): runs_needed_power(m, 0.6, s_med, 0.8) for m in (2, 3, 5)}
base["runs_needed_power90_gap0.6_median_sd"] = {str(m): runs_needed_power(m, 0.6, s_med, 0.9) for m in (2, 3, 5)}
base["runs_needed_power80_gap0_median_sd"] = {str(m): runs_needed_power(m, 0.0, s_med, 0.8) for m in (2, 3, 5)}
from parity_lib import tost_power  # noqa: E402
base["tost_power_at_plugin_k"] = {str(m): round(tost_power(base["runs_needed_plugin_gap0.6_median_sd"][str(m)], 0.6, s_med, m), 3) for m in (2, 3, 5)}
base["t_quantiles"] = {"t975_df4": t_quantile(0.975, 4), "t95_df4": t_quantile(0.95, 4)}
base["sensitivity_variants"] = {name: {k: v for k, v in res.items() if k in ("n_analysed", "median_pooled_sd", "median_gap", "tost_within", "ci95_within", "tost_within_welch", "n_fail_overlap", "n_distinguishable_from_zero")} for name, (res, _) in results.items()}

with open(os.path.join(out, "first_pass_cut.json"), "w") as fh:
    json.dump(base, fh, indent=1)
cols = ["adapter", "exp", "agent", "model", "metric", "scaled_x100", "mean_original", "mean_harbor", "gap", "pooled_sd",
        "hw90", "hw95", "hw90_welch", "hw95_welch", "smallest_margin_tost", "smallest_margin_ci95", "smallest_margin_tost_welch",
        "fails_overlap", "distinguishable_from_zero", "identical_lists", "zero_spread_one_side", "raw_len_original", "raw_len_harbor",
        "original_runs", "harbor_runs"]
for name, (_, sel) in results.items():
    fn = "first_pass_cut_rows.csv" if name == "base" else f"first_pass_cut_rows_{name.replace('+', '_')}.csv"
    with open(os.path.join(out, fn), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(sorted(sel, key=lambda r: (r["adapter"], r["exp"])))

n = base["n_analysed"]
print(f"experiments {base['n_experiments']} | first rate-like 3v3 metric found in {base['n_selected_incl_zero_spread']} | zero spread both sides (excluded) {base['n_excluded_zero_spread_both']} | analysed {n}")
print(f"median pooled run-to-run SD {s_med:.2f} points | median |gap| {gap_med:.2f} points")
print("largest gaps:", base["largest_gaps"])
print(f"fail range-overlap: {base['n_fail_overlap']} of {n}:", base["fail_overlap_rows"])
print("TOST (alpha .05) equivalence shown within +-m:", base["tost_within"], "| Welch:", base["tost_within_welch"])
print("95% CI equivalence shown within +-m:        ", base["ci95_within"])
print(f"gap distinguishable from zero (95%): {base['n_distinguishable_from_zero']} of {n}")
print("smallest provable margin (TOST) quartiles:", [round(x, 2) for x in base["smallest_margin_tost_quartiles"]])
print("knife-edge rows (within 0.05 of a margin):", base["knife_edge_rows"])
print("runs per side, plug-in heuristic (gap 0.6, median SD):", base["runs_needed_plugin_gap0.6_median_sd"], "| TOST power at those k:", base["tost_power_at_plugin_k"])
print("runs per side for 80% TOST power (gap 0.6, median SD):", base["runs_needed_power80_gap0.6_median_sd"], "| 90%:", base["runs_needed_power90_gap0.6_median_sd"], "| 80% at gap 0:", base["runs_needed_power80_gap0_median_sd"])
print("sensitivity variants:")
for name, v in base["sensitivity_variants"].items():
    print(f"   {name:15s} n={v['n_analysed']} median SD {v['median_pooled_sd']:.2f} gap {v['median_gap']:.2f} TOST {v['tost_within']} CI95 {v['ci95_within']} fail {v['n_fail_overlap']} distinguishable {v['n_distinguishable_from_zero']}")
