#!/usr/bin/env python3
"""Phase 2, RQ1: what does the range-overlap rule guarantee, and how do alternatives compare?

Decision rules on two run lists a (original) and b (Harbor), k runs each:
  R  : range overlap (Harbor's rule; ties count as overlap)                -> "match" / "mismatch"
  S1 : mean ± SEM bars overlap, |gap| <= SEM_a + SEM_b                       -> paper reading 1
  S2 : |gap| <= SE of the difference, i.e. |t| <= 1                          -> paper reading 2
  W  : Welch t-test, mismatch iff p < 0.05
  E_m: TOST at margin m points, pooled t, alpha 0.05: equivalence shown iff |gap| + t(.95, 2k-2) s_p sqrt(2/k) <= m
For R, S1, S2, W we report P(verdict = mismatch) as a function of the true gap: at gap 0 it is the
false-alarm rate, at gap > 0 the detection rate. For E_m we report P(equivalence shown).
Noise models (pre-registered): normal (gap in SD units, exact where possible), binomial pass rates over n
tasks (gap in points), and realistic per-task heterogeneity from recovered per-task outcomes when
data/pertask/ exists. Usage: python -I scripts/p2_rq1_rules.py <out_dir> [pertask_dir] [n_trials]
"""
import csv
import glob
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parity_lib import rule_false_alarm_exact, rule_mismatch_rate_normal, rule_verdicts, runs_needed_power, t_quantile  # noqa: E402

out = sys.argv[1]
pertask_dir = sys.argv[2] if len(sys.argv) > 2 and os.path.isdir(sys.argv[2]) else None
N = int(sys.argv[3]) if len(sys.argv) > 3 else 200_000
os.makedirs(os.path.join(out, "figures"), exist_ok=True)
rng = np.random.default_rng(7)


RULES = ("R", "S1", "S2", "S3", "W", "T")


def rates(a, b, margins):
    v = rule_verdicts(a, b, margins)
    return {key: float(val.mean()) for key, val in v.items() if key != "t_pooled_abs"}


results = {"n_trials": N, "seed": 7}

# ---------------------------------------------------------------- (a) normal noise, gap in SD units
KS, DELTAS = (2, 3, 4, 5, 6, 8, 10), (0, 0.5, 1, 1.5, 2, 3, 4)
normal, matched = {}, {}
for k in KS:
    a0 = rng.standard_normal((N, k)); b0 = rng.standard_normal((N, k))
    v0 = rule_verdicts(a0, b0, margins=(0.5, 1, 2, 3))
    t0 = v0["t_pooled_abs"]
    fa_k = {r: float(v0[r].mean()) for r in RULES}
    fa_k["R"] = rule_false_alarm_exact(k)
    thresholds = {r: float(np.quantile(t0, 1 - fa_k[r])) for r in RULES}  # |t| threshold with the same false alarm as rule r
    for d in DELTAS:
        a = rng.standard_normal((N, k)); b = rng.standard_normal((N, k)) + d
        v = rule_verdicts(a, b, margins=(0.5, 1, 2, 3))
        r = {key: float(val.mean()) for key, val in v.items() if key != "t_pooled_abs"}
        r["R_exact"] = rule_mismatch_rate_normal(k, d)
        r["t_at_matched_false_alarm"] = {rule: float((v["t_pooled_abs"] > thresholds[rule]).mean()) for rule in RULES}
        normal[f"k={k},gap={d}"] = r
    matched[str(k)] = {"false_alarm": fa_k, "t_threshold": thresholds}
    if k == 3:
        sp0 = np.sqrt((a0.var(1, ddof=1) + b0.var(1, ddof=1)) / 2)
        matched["expected_smallest_margin_sd_units_k3"] = float((np.abs(b0.mean(1) - a0.mean(1)) + t_quantile(0.95, 4) * sp0 * math.sqrt(2 / 3)).mean())
results_matched = matched
results["normal_sd_units"] = normal
results["matched_false_alarm"] = results_matched
results["closed_form_false_alarm"] = {str(k): rule_false_alarm_exact(k) for k in KS}
results["tost_runs_needed_sd_units_power80_gap0"] = {str(m): runs_needed_power(m, 0.0, 1.0, 0.8) for m in (1, 1.5, 2, 3)}

# "rewards noise": fixed true gap of 2 points, common SD sigma; and one-sided (port noisier, original SD 1)
noise_common = {str(s): {"R": 1 - rule_mismatch_rate_normal(3, 2.0 / s)} for s in (0.25, 0.5, 1, 1.5, 2, 3, 5, 10, 100)}
for s in (0.25, 0.5, 1, 1.5, 2, 3, 5, 10, 100):
    a = rng.standard_normal((N, 3)) * s; b = rng.standard_normal((N, 3)) * s + 2.0
    r = rates(a, b, margins=(3, 5))
    noise_common[str(s)].update({"W_pass": 1 - r["W"], "T_pass": 1 - r["T"], "S1_pass": 1 - r["S1"], "E3": r["E3"], "E5": r["E5"]})
noise_one_sided = {}
for s in (0.25, 0.5, 1, 2, 4, 8, 32, 100):
    a = rng.standard_normal((N, 3)); b = rng.standard_normal((N, 3)) * s + 1.0
    r = rates(a, b, margins=(3,))
    noise_one_sided[str(s)] = {"R_pass": 1 - r["R"], "W_pass": 1 - r["W"], "T_pass": 1 - r["T"], "S1_pass": 1 - r["S1"]}
results["pass_prob_fixed_gap2_common_sd_k3"] = noise_common
results["pass_prob_fixed_gap1_port_sd_only_k3"] = noise_one_sided

# ---------------------------------------------------------------- (b) binomial pass rates, gap in points
binom = {}
for n in (10, 30, 50, 100, 300, 1000):
    for p in (0.1, 0.3, 0.5):
        for k in (3, 5):
            for d in (0, 1, 2, 3, 5, 10):
                pb = min(1.0, p + d / 100)
                a = rng.binomial(n, p, (N, k)) * 100.0 / n
                b = rng.binomial(n, pb, (N, k)) * 100.0 / n
                r = rates(a, b, margins=(2, 3, 5))
                sd_a, sd_b = 100 * math.sqrt(p * (1 - p) / n), 100 * math.sqrt(pb * (1 - pb) / n)
                r["implied_run_sd_points"] = sd_a
                r["gap_in_pooled_sd"] = d / math.sqrt((sd_a ** 2 + sd_b ** 2) / 2) if d else 0.0
                binom[f"n={n},p={p},k={k},gap={d}"] = r
results["binomial_points"] = binom

# ---------------------------------------------------------------- (c) realistic per-task heterogeneity
realistic = {}
if pertask_dir:
    man_path = os.path.join(pertask_dir, "MANIFEST.json")
    allowed = None
    if os.path.exists(man_path):
        allowed = {a for a, v in json.load(open(man_path))["adapters"].items() if v.get("use_for_defect_model") and v.get("binary_outcomes")}
    files = sorted(glob.glob(os.path.join(pertask_dir, "*", "harbor.csv")))
    for f in files:
        adapter = os.path.basename(os.path.dirname(f))
        if allowed is not None and adapter not in allowed:
            continue
        by_task = {}
        for row in csv.DictReader(open(f)):
            try:
                by_task.setdefault(row["task_id"], []).append(float(row["reward"]))
            except ValueError:
                pass
        if len(by_task) < 20:
            continue
        vals = np.array([v for lst in by_task.values() for v in lst]); sc = 1.0 if vals.max() <= 1.0 else 0.01
        per = {"n_tasks": len(by_task), "runs_per_task": float(np.mean([len(v) for v in by_task.values()]))}
        # a task's pass probability from its runs: primary light shrinkage (amendment 5); Beta(1,1) as sensitivity
        for prior, (alpha, beta) in (("light", (0.05, 0.05)), ("beta11", (1.0, 1.0))):
            p_i = np.array([(sum(v) * sc + alpha) / (len(v) + alpha + beta) for v in by_task.values()])
            base = float(p_i.mean() * 100)
            per[f"base_rate_points_{prior}"] = base
            per[f"model_run_sd_points_{prior}"] = float(100 * math.sqrt((p_i * (1 - p_i)).sum()) / len(p_i))
            for k in (3, 5):
                for d in (0, 1, 2, 3, 5, 10):
                    if prior == "beta11" and k != 3:
                        continue
                    factor = max(0.0, 1 - d / base) if base > 0 else 0.0  # scale so the expected mean drops by d points
                    nt = 20000
                    a = (rng.random((nt, k, len(p_i))) < p_i).mean(2) * 100
                    b = (rng.random((nt, k, len(p_i))) < p_i * factor).mean(2) * 100
                    r = rates(a, b, margins=(2, 3, 5))
                    r["implied_run_sd_points"] = float(a.std(1, ddof=1).mean())
                    per[f"{prior},k={k},gap={d}"] = r
        realistic[adapter] = per
results["realistic_pertask"] = realistic

# ---------------------------------------------------------------- summaries used in the memo
summ = {}
k3 = {d: normal[f"k=3,gap={d}"] for d in DELTAS}
summ["k3_normal_false_alarm"] = {r: k3[0][r] for r in RULES}
summ["k3_normal_detect_2sd"] = {r: k3[2][r] for r in RULES}
summ["k3_normal_detect_1sd"] = {r: k3[1][r] for r in RULES}
summ["k3_t_at_matched_false_alarm_detect_2sd"] = k3[2]["t_at_matched_false_alarm"]
summ["k3_t_at_matched_false_alarm_detect_1sd"] = k3[1]["t_at_matched_false_alarm"]
summ["false_alarm_by_k"] = {r: {str(k): (rule_false_alarm_exact(k) if r == "R" else normal[f"k={k},gap=0"][r]) for k in KS} for r in RULES}
summ["R_detect_2sd_by_k"] = {str(k): normal[f"k={k},gap=2"]["R_exact"] for k in KS}
summ["W_detect_2sd_by_k"] = {str(k): normal[f"k={k},gap=2"]["W"] for k in KS}
summ["T_detect_2sd_by_k"] = {str(k): normal[f"k={k},gap=2"]["T"] for k in KS}
summ["expected_smallest_margin_sd_units_k3"] = results_matched["expected_smallest_margin_sd_units_k3"]
summ["tost_runs_needed_sd_units_power80_gap0"] = results["tost_runs_needed_sd_units_power80_gap0"]
summ["E_equiv_shown_at_gap0_by_k_margin1sd"] = {str(k): normal[f"k={k},gap=0"]["E1"] for k in KS}
summ["binomial_k3_p0.3_false_alarm_by_n"] = {str(n): binom[f"n={n},p=0.3,k=3,gap=0"]["R"] for n in (10, 30, 50, 100, 300, 1000)}
summ["binomial_k3_p0.3_detect_5pts_by_n"] = {str(n): {r: binom[f"n={n},p=0.3,k=3,gap=5"][r] for r in RULES} | {"gap_in_pooled_sd": binom[f"n={n},p=0.3,k=3,gap=5"]["gap_in_pooled_sd"]} for n in (10, 30, 50, 100, 300, 1000)}
if realistic:
    summ["realistic_k3_false_alarm_R"] = {a: v["light,k=3,gap=0"]["R"] for a, v in realistic.items()}
    summ["realistic_k3_detect_5pts"] = {a: {r: v["light,k=3,gap=5"][r] for r in RULES} for a, v in realistic.items()}
    summ["realistic_median_over_adapters"] = {cell: {r: float(np.median([v[cell][r] for v in realistic.values()])) for r in RULES + ("E3", "E5")} for cell in ("light,k=3,gap=0", "light,k=3,gap=2", "light,k=3,gap=5", "light,k=5,gap=5", "beta11,k=3,gap=0", "beta11,k=3,gap=5")}
    summ["realistic_model_run_sd_quartiles"] = {prior: [float(x) for x in np.percentile([v[f"model_run_sd_points_{prior}"] for v in realistic.values()], [25, 50, 75])] for prior in ("light", "beta11")}
results["summary"] = summ
with open(os.path.join(out, "rq1_rules.json"), "w") as fh:
    json.dump(results, fh, indent=1)

# ---------------------------------------------------------------- figure
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sd_ticks = None
try:
    sd_ticks = json.load(open(os.path.join(out, "rq2_summary.json")))["summaries"]["headline_k3"]["sd_quartiles"]
except Exception:
    pass
fig, axes = plt.subplots(2, 2, figsize=(10, 7.2))
ax = axes[0, 0]
for rule, lab, ls in (("R", "range overlap (Harbor)", "-"), ("S1", "mean ± SEM bars overlap", "--"), ("S2", "|gap| ≤ SE of difference", "-."), ("T", "pooled t-test, p < .05", "-"), ("W", "Welch t-test, p < .05", ":")):
    ax.plot(DELTAS, [normal[f"k=3,gap={d}"][rule] for d in DELTAS], ls, marker="o", ms=3, label=lab)
ax.set_xlabel("true gap, in run-to-run SDs"); ax.set_ylabel("P(verdict = mismatch)"); ax.set_title("(a) k = 3, normal noise; curves differ mainly by their false-alarm rate", fontsize=9)
ax.axhline(0.05, color="grey", lw=0.5); ax.text(3.6, 0.06, "0.05", fontsize=7, color="grey"); ax.legend(fontsize=7, frameon=False); ax.set_ylim(0, 1)
ax = axes[0, 1]
for rule, lab in (("R", "range overlap"), ("S1", "SEM bars overlap"), ("T", "pooled t-test"), ("W", "Welch t-test")):
    ax.plot(KS, [summ["false_alarm_by_k"][rule][str(k)] for k in KS], marker="o", ms=3, label=lab)
ax.set_xlabel("runs per side k"); ax.set_ylabel("false alarm: P(mismatch | perfect port)"); ax.set_title("(b) false-alarm rate by k", fontsize=9); ax.set_ylim(0, 0.4); ax.legend(fontsize=7, frameon=False)
ax = axes[1, 0]
for rule, lab in (("R", "range overlap"), ("S1", "SEM bars overlap"), ("T", "pooled t-test"), ("W", "Welch t-test")):
    ax.plot(KS, [normal[f"k={k},gap=2"][rule if rule != "R" else "R_exact"] for k in KS], marker="o", ms=3, label=lab)
ax.set_xlabel("runs per side k"); ax.set_ylabel("P(detect a 2 SD gap)"); ax.set_title("(c) detection of a fixed 2 SD gap by k", fontsize=9); ax.set_ylim(0, 1); ax.legend(fontsize=7, frameon=False)
ax = axes[1, 1]
sds = [0.25, 0.5, 1, 1.5, 2, 3, 5, 10]
ax.plot(sds, [noise_common[str(s)]["R"] for s in sds], marker="o", ms=3, label="range overlap: P(pass)")
ax.plot(sds, [noise_common[str(s)]["T_pass"] for s in sds], marker="^", ms=3, label="pooled t-test: P(no significant gap)")
ax.plot(sds, [noise_common[str(s)]["E3"] for s in sds], marker="s", ms=3, label="TOST ±3: P(equivalence shown)")
if sd_ticks:
    for q in sd_ticks:
        ax.axvline(q, color="grey", lw=0.6, ls="--")
    ax.text(sd_ticks[1] * 1.05, 0.03, "observed SD quartiles", fontsize=7, color="grey")
ax.set_xscale("log"); ax.set_xlabel("run-to-run SD, points (both sides)"); ax.set_ylabel("probability (pass, or equivalence shown)"); ax.set_title("(d) true gap fixed at 2 points, k = 3", fontsize=9); ax.set_ylim(0, 1); ax.legend(fontsize=7, frameon=False)
fig.tight_layout()
fig.savefig(os.path.join(out, "figures", "fig_rq1_rules.png"), dpi=200)
fig.savefig(os.path.join(out, "figures", "fig_rq1_rules.pdf"))

print("k=3, normal: false alarm", {r: round(v, 3) for r, v in summ["k3_normal_false_alarm"].items()})
print("k=3, normal: detect 1 SD", {r: round(v, 3) for r, v in summ["k3_normal_detect_1sd"].items()}, "| detect 2 SD", {r: round(v, 3) for r, v in summ["k3_normal_detect_2sd"].items()})
print("k=3: t-statistic at each rule's false alarm detects 2 SD:", {r: round(v, 3) for r, v in summ["k3_t_at_matched_false_alarm_detect_2sd"].items()})
print(f"k=3: expected smallest provable margin under parity: {summ['expected_smallest_margin_sd_units_k3']:.2f} SD | runs/side for 80% TOST power at gap 0 by margin in SD:", summ["tost_runs_needed_sd_units_power80_gap0"])
print("R detects 2 SD gap by k:", {k: round(v, 3) for k, v in summ["R_detect_2sd_by_k"].items()})
print("W detects 2 SD gap by k:", {k: round(v, 3) for k, v in summ["W_detect_2sd_by_k"].items()})
print("TOST(±1 SD) shows equivalence at gap 0, by k:", {k: round(v, 3) for k, v in summ["E_equiv_shown_at_gap0_by_k_margin1sd"].items()})
print("binomial k=3 p=.3: R false alarm by n:", {n: round(v, 3) for n, v in summ["binomial_k3_p0.3_false_alarm_by_n"].items()})
print("binomial k=3 p=.3: detect 5-point gap by n:", {n: {r: round(x, 2) for r, x in v.items()} for n, v in summ["binomial_k3_p0.3_detect_5pts_by_n"].items()})
print("pass prob, gap 2 points, common SD:", {s: round(v["R"], 3) for s, v in noise_common.items()})
print("pass prob, gap 1 SD, port SD only:", {s: round(v["R_pass"], 3) for s, v in noise_one_sided.items()})
print("realistic adapters simulated:", len(realistic))
if realistic:
    print("realistic, median over adapters:", {c: {r: round(v, 2) for r, v in d.items()} for c, d in summ["realistic_median_over_adapters"].items()})
    print("model run SD quartiles by prior:", {k: [round(x, 2) for x in v] for k, v in summ["realistic_model_run_sd_quartiles"].items()})
