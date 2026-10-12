#!/usr/bin/env python3
"""Phase 2, RQ2: what does the published evidence establish?

Reads the pre-registered comparison table and, for every analysable comparison (>= 2 runs per side,
not identical lists, not zero spread on both sides, point-scale metric), computes the gap, 95% and
90% pooled-t intervals (Welch as sensitivity), the smallest provable margin |gap| + hw90, and the
verdict of each decision rule (R, S1, S2, W, E at 1/2/3/5/10). Summaries: headline set (k = 3 on
both sides), full set (k >= 2), by parity set, by k, one comparison per adapter, with/without the
degenerate rows. Data-quality lists are collected from the selection log and the Phase 0 outputs.
Usage: python -I scripts/p2_rq2_evidence.py <phase2_dir> <phase0_dir>
"""
import ast
import csv
import json
import math
import os
import statistics
import sys

import numpy as np
from scipy.stats import ttest_ind

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parity_lib import diff_ci_halfwidth, pooled_sd, range_separation, ranges_overlap, rule_false_alarm_exact, sem, welch_ci_halfwidth  # noqa: E402

p2, p0 = sys.argv[1], sys.argv[2]
MARGINS = (1, 2, 3, 5, 10)
rows = list(csv.DictReader(open(os.path.join(p2, "comparisons.csv"))))
for r in rows:
    r["original_runs"] = ast.literal_eval(r["original_runs"]); r["harbor_runs"] = ast.literal_eval(r["harbor_runs"])
    for f in ("k_original", "k_harbor", "exp"):
        r[f] = int(r[f])
    for f in ("native_units", "identical_lists", "zero_spread_both", "zero_spread_one", "single_run_side", "scaled_x100", "in_paper_table"):
        r[f] = r[f] == "True"


def analyse(r):
    a, b = r["original_runs"], r["harbor_runs"]
    g = statistics.mean(b) - statistics.mean(a)
    s = pooled_sd(a, b)
    hw95, hw90 = diff_ci_halfwidth(a, b, 0.95), diff_ci_halfwidth(a, b, 0.90)
    hw95w, hw90w = welch_ci_halfwidth(a, b, 0.95), welch_ci_halfwidth(a, b, 0.90)
    sea, seb = sem(a), sem(b)
    pw = float(ttest_ind(a, b, equal_var=False).pvalue) if (statistics.variance(a) + statistics.variance(b)) > 0 else (0.0 if g != 0 else 1.0)
    out = {"gap": g, "abs_gap": abs(g), "pooled_sd": s, "hw95": hw95, "hw90": hw90, "hw95_welch": hw95w, "hw90_welch": hw90w,
           "ci95_low": g - hw95, "ci95_high": g + hw95, "smallest_margin": abs(g) + hw90, "smallest_margin_welch": abs(g) + hw90w,
           "sem_original": sea, "sem_harbor": seb, "gap_in_sd": abs(g) / s if s > 0 else float("inf"),
           "R_overlap": ranges_overlap(a, b, eps=1e-9), "R_overlap_eps0": ranges_overlap(a, b), "range_separation": range_separation(a, b),
           "S1_match": abs(g) <= sea + seb + 1e-12, "S2_match": abs(g) <= math.sqrt(sea ** 2 + seb ** 2) + 1e-12,
           "S3_match": abs(g) <= max(sea, seb) + 1e-12,
           "welch_p": pw, "W_mismatch": pw < 0.05, "T_mismatch": abs(g) > hw95, "distinguishable_95": abs(g) > hw95}
    for m in MARGINS:
        out[f"E{m}"] = out["smallest_margin"] <= m
        out[f"E{m}_welch"] = out["smallest_margin_welch"] <= m
    return out


analysable = [r for r in rows if r["k_original"] >= 2 and r["k_harbor"] >= 2 and not r["identical_lists"] and not r["zero_spread_both"] and not r["native_units"]]
excluded = {"single_run_side": [r for r in rows if r["single_run_side"]], "identical_lists": [r for r in rows if r["identical_lists"] and not r["single_run_side"]],
            "zero_spread_both": [r for r in rows if r["zero_spread_both"] and not r["identical_lists"]], "native_units": [r for r in rows if r["native_units"]]}
for r in analysable:
    r.update(analyse(r))
# native-unit rows: standardized gap only
for r in excluded["native_units"]:
    if r["k_original"] >= 2 and r["k_harbor"] >= 2:
        a, b = r["original_runs"], r["harbor_runs"]; s = pooled_sd(a, b)
        r["gap_in_sd"] = abs(statistics.mean(b) - statistics.mean(a)) / s if s > 0 else float("inf"); r["R_overlap"] = ranges_overlap(a, b, eps=1e-9)


def summarise(sub, label):
    n = len(sub)
    if n == 0:
        return {"label": label, "n": 0}
    sm = np.array([r["smallest_margin"] for r in sub]); smw = np.array([r["smallest_margin_welch"] for r in sub])
    gaps = np.array([r["abs_gap"] for r in sub]); sds = np.array([r["pooled_sd"] for r in sub])
    return {"label": label, "n": n,
            "median_abs_gap": float(np.median(gaps)), "gap_quartiles": [float(x) for x in np.percentile(gaps, [25, 50, 75])],
            "median_pooled_sd": float(np.median(sds)), "sd_quartiles": [float(x) for x in np.percentile(sds, [25, 50, 75])],
            "smallest_margin_quartiles": [float(x) for x in np.percentile(sm, [25, 50, 75])],
            "within_margin_tost": {str(m): int(np.sum(sm <= m)) for m in MARGINS},
            "within_margin_tost_welch": {str(m): int(np.sum(smw <= m)) for m in MARGINS},
            "within_margin_share": {str(m): round(float(np.mean(sm <= m)), 3) for m in MARGINS},
            "n_fail_overlap": int(sum(not r["R_overlap"] for r in sub)), "n_fail_overlap_eps0": int(sum(not r["R_overlap_eps0"] for r in sub)),
            "n_S1_mismatch": int(sum(not r["S1_match"] for r in sub)), "n_S2_mismatch": int(sum(not r["S2_match"] for r in sub)),
            "n_S3_mismatch": int(sum(not r["S3_match"] for r in sub)),
            "near_threshold_within_0.1": {str(m): int(np.sum(np.abs(sm - m) <= 0.1)) for m in MARGINS},
            "within_margin_range_under_0.1_perturbation": {str(m): [int(np.sum(sm <= m - 0.1)), int(np.sum(sm <= m + 0.1))] for m in MARGINS},
            "n_W_mismatch": int(sum(r["W_mismatch"] for r in sub)), "n_distinguishable_95": int(sum(r["distinguishable_95"] for r in sub)),
            "largest_gaps": [(r["adapter"], r["metric"], round(r["gap"], 2), round(r["smallest_margin"], 2)) for r in sorted(sub, key=lambda r: -r["abs_gap"])[:6]],
            "overlap_pass_but_margin_over_5": int(sum(r["R_overlap"] and r["smallest_margin"] > 5 for r in sub)),
            "overlap_fail_but_equiv_within_5": int(sum((not r["R_overlap"]) and r["E5"] for r in sub)),
            "overlap_fail_but_equiv_within_3": int(sum((not r["R_overlap"]) and r["E3"] for r in sub))}


head = [r for r in analysable if r["k_original"] == 3 and r["k_harbor"] == 3]
one_per_adapter = {}
for r in analysable:  # one comparison per adapter: the paper-table row if any, else the first experiment
    cur = one_per_adapter.get(r["adapter"])
    if cur is None or (r["selection_branch"].startswith("1:") and not cur["selection_branch"].startswith("1:")):
        one_per_adapter[r["adapter"]] = r
summaries = {
    "headline_k3": summarise(head, "k = 3 on both sides"),
    "all_k_ge_2": summarise(analysable, "all comparisons with >= 2 runs per side"),
    "one_per_adapter": summarise(list(one_per_adapter.values()), "one comparison per adapter"),
    "subset_k3": summarise([r for r in head if r["parity_set"] == "subset"], "k = 3, parity on a subset"),
    "full_k3": summarise([r for r in head if r["parity_set"] == "full"], "k = 3, parity on the full set"),
    "with_identical_rows": summarise(analysable + [dict(r, **analyse(r)) for r in excluded["identical_lists"] if r["k_original"] >= 2 and r["k_harbor"] >= 2 and not r["native_units"] and not r["zero_spread_both"]], "k >= 2 including identical non-constant rows (zero-width intervals excluded)"),
    "by_k": {**{f"{k}v{k}": summarise([r for r in analysable if r["k_original"] == k and r["k_harbor"] == k], f"k = {k}") for k in (2, 3, 4, 5, 6)},
             "unequal": summarise([r for r in analysable if r["k_original"] != r["k_harbor"]], "unequal k")},
    "zero_spread_one_side_k3": summarise([r for r in head if r["zero_spread_one"]], "k = 3, zero spread on one side"),
    "in_paper_table_k3": summarise([r for r in head if r["selection_branch"].startswith("1:")], "k = 3, row matches the paper table"),
}
# agreement table between the overlap verdict and TOST at 3 and 5 points (headline set)
agree = {}
for m in (3, 5):
    agree[f"m={m}"] = {"overlap_pass_equiv_shown": int(sum(r["R_overlap"] and r[f"E{m}"] for r in head)),
                       "overlap_pass_equiv_not_shown": int(sum(r["R_overlap"] and not r[f"E{m}"] for r in head)),
                       "overlap_fail_equiv_shown": int(sum((not r["R_overlap"]) and r[f"E{m}"] for r in head)),
                       "overlap_fail_equiv_not_shown": int(sum((not r["R_overlap"]) and not r[f"E{m}"] for r in head))}
summaries["overlap_vs_tost_headline"] = agree
rq1_path = os.path.join(p2, "rq1_rules.json")
if os.path.exists(rq1_path):
    from scipy.stats import binom
    rq1 = json.load(open(rq1_path))
    fa = {"R": rule_false_alarm_exact(3), **{r: rq1["normal_sd_units"]["k=3,gap=0"][r] for r in ("S1", "S2", "S3", "W", "T") if r in rq1["normal_sd_units"]["k=3,gap=0"]}}
    obs = {"R": summaries["headline_k3"]["n_fail_overlap"], "S1": summaries["headline_k3"]["n_S1_mismatch"], "S2": summaries["headline_k3"]["n_S2_mismatch"],
           "S3": summaries["headline_k3"]["n_S3_mismatch"], "W": summaries["headline_k3"]["n_W_mismatch"], "T": int(sum(r["T_mismatch"] for r in head))}
    n = summaries["headline_k3"]["n"]
    summaries["selection_check_headline"] = {r: {"false_alarm_under_parity": fa[r], "expected_mismatches_if_all_ports_perfect": n * fa[r], "observed": obs[r],
                                                 "p_observed_or_fewer": float(binom.cdf(obs[r], n, fa[r]))} for r in fa}

# data quality
sel = json.load(open(os.path.join(p2, "selection_log.json")))
inv = json.load(open(os.path.join(p0, "inventory.json")))
rep = json.load(open(os.path.join(p0, "reported_vs_runs.json")))
dq = {"experiments": sel["n_experiments"], "comparisons": sel["n_comparisons"], "transitive_legs": sel["n_legs"],
      "experiments_without_comparison": sel["experiments_without_comparison"],
      "single_run_rows": [f"{r['adapter']}#{r['exp']} {r['metric']} k={r['k_original']}v{r['k_harbor']} gap={round(statistics.mean(r['harbor_runs']) - statistics.mean(r['original_runs']), 2)}" for r in excluded["single_run_side"]],
      "identical_lists": [f"{r['adapter']}#{r['exp']} {r['metric']} {r['original_runs']}" for r in excluded["identical_lists"]],
      "zero_spread_both": [f"{r['adapter']}#{r['exp']} {r['metric']} {r['original_runs']}" for r in rows if r["zero_spread_both"]],
      "zero_spread_one_side": [f"{r['adapter']}#{r['exp']} {r['metric']} orig={r['original_runs']} harbor={r['harbor_runs']}" for r in analysable if r["zero_spread_one"]],
      "native_unit_rows": [f"{r['adapter']}#{r['exp']} {r['metric']} orig={r['original_runs']} harbor={r['harbor_runs']} gap/SD={round(r.get('gap_in_sd', float('nan')), 2)}" for r in excluded["native_units"]],
      "declared_runs_differ_from_lists": inv["declared_runs_differ_from_actual"],
      "run_lists_with_string_values": inv["run_lists_with_non_numeric_entries"],
      "reported_string_vs_runs": rep["by_mean_ok_and_err_class"], "reported_mean_mismatches": rep["mean_mismatch_rows"],
      "original_variant_rows": sel["original_variant_rows"], "excluded_side_quantity_names": sel["excluded_side_quantities"],
      "parity_set_counts": sel["parity_set_counts"], "selection_branch_counts": sel["selection_branch_counts"]}

with open(os.path.join(p2, "rq2_summary.json"), "w") as fh:
    json.dump({"summaries": summaries, "data_quality": dq}, fh, indent=1)
cols = ["adapter", "exp", "agent", "model", "metric", "selection_branch", "k_original", "k_harbor", "parity_set", "parity_n", "adapted_n",
        "mean_original", "mean_harbor", "gap", "pooled_sd", "gap_in_sd", "ci95_low", "ci95_high", "hw90", "smallest_margin", "smallest_margin_welch",
        "R_overlap", "R_overlap_eps0", "range_separation", "S1_match", "S2_match", "welch_p", "W_mismatch", "distinguishable_95",
        "E1", "E2", "E3", "E5", "E10", "zero_spread_one", "original_runs", "harbor_runs"]
with open(os.path.join(p2, "rq2_comparisons.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    w.writerows(sorted(analysable, key=lambda r: r["smallest_margin"]))

# figure: smallest provable margin per comparison, headline set
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
os.makedirs(os.path.join(p2, "figures"), exist_ok=True)
hs = sorted(head, key=lambda r: r["smallest_margin"])
fig, ax = plt.subplots(figsize=(7.2, 0.17 * len(hs) + 1.2))
y = np.arange(len(hs))
XLIM = 16
for i, r in enumerate(hs):
    col = "tab:red" if not r["R_overlap"] else "tab:blue"
    lo, hi = r["gap"] - r["hw90"], r["gap"] + r["hw90"]
    ax.plot([max(lo, -XLIM), min(hi, XLIM)], [i, i], color=col, lw=1.2)
    if lo < -XLIM:
        ax.plot(-XLIM + 0.3, i, "<", color=col, ms=4)
    if hi > XLIM:
        ax.plot(XLIM - 0.3, i, ">", color=col, ms=4)
    ax.plot(r["gap"], i, "o", color=col, ms=2.5)
for m, ls in ((3, "--"), (5, ":")):
    ax.axvline(m, color="grey", ls=ls, lw=0.7); ax.axvline(-m, color="grey", ls=ls, lw=0.7)
ax.axvline(0, color="black", lw=0.5)
ax.set_yticks(y); ax.set_yticklabels([f"{r['adapter']} ({r['exp']})" if sum(1 for q in hs if q['adapter'] == r['adapter']) > 1 else r["adapter"] for r in hs], fontsize=5.5)
ax.set_xlabel("Harbor minus original, points, with the 90% (TOST) interval; red = fails range overlap; arrows = interval continues", fontsize=8)
ax.set_xlim(-XLIM, XLIM)
fig.tight_layout(); fig.savefig(os.path.join(p2, "figures", "fig_rq2_margins.png"), dpi=200); fig.savefig(os.path.join(p2, "figures", "fig_rq2_margins.pdf"))

for key in ("headline_k3", "all_k_ge_2", "one_per_adapter", "subset_k3", "full_k3", "with_identical_rows", "in_paper_table_k3"):
    s = summaries[key]
    if s["n"] == 0:
        continue
    print(f"[{s['label']}] n={s['n']} | median |gap| {s['median_abs_gap']:.2f} | median SD {s['median_pooled_sd']:.2f} | smallest margin quartiles {[round(x, 1) for x in s['smallest_margin_quartiles']]} | TOST within ±1/2/3/5/10: {list(s['within_margin_tost'].values())} | Welch: {list(s['within_margin_tost_welch'].values())} | fail overlap {s['n_fail_overlap']} | S1 mismatch {s['n_S1_mismatch']} | S2 {s['n_S2_mismatch']} | W {s['n_W_mismatch']} | distinguishable {s['n_distinguishable_95']} | overlap pass but margin>5: {s['overlap_pass_but_margin_over_5']}")
print("by k:", {k: (v["n"], v["within_margin_tost"]) for k, v in summaries["by_k"].items() if v["n"]})
print("overlap vs TOST (k=3):", agree)
if "selection_check_headline" in summaries:
    print("selection check (headline): " + "; ".join(f"{r}: expected {v['expected_mismatches_if_all_ports_perfect']:.1f} observed {v['observed']} p={v['p_observed_or_fewer']:.3f}" for r, v in summaries["selection_check_headline"].items()))
print("near-threshold (headline):", summaries["headline_k3"]["near_threshold_within_0.1"], "| within-margin range under ±0.1:", summaries["headline_k3"]["within_margin_range_under_0.1_perturbation"])
print("largest gaps (k=3):", summaries["headline_k3"]["largest_gaps"])
print("single-run rows:", dq["single_run_rows"]); print("identical:", dq["identical_lists"]); print("zero both:", dq["zero_spread_both"]); print("native:", dq["native_unit_rows"])
