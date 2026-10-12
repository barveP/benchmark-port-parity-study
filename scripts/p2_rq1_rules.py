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
from scipy.stats import norm, t as tdist

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parity_lib import rule_false_alarm_exact, rule_mismatch_rate_normal, t_quantile  # noqa: E402

out = sys.argv[1]
pertask_dir = sys.argv[2] if len(sys.argv) > 2 and os.path.isdir(sys.argv[2]) else None
N = int(sys.argv[3]) if len(sys.argv) > 3 else 200_000
os.makedirs(os.path.join(out, "figures"), exist_ok=True)
rng = np.random.default_rng(7)


def verdicts(a, b, margins=(1, 2, 3, 5, 10)):
    """Vectorised rules. a, b: arrays (trials, k). Returns dict of boolean arrays: True = mismatch (R,S1,S2,W)
    or True = equivalence shown (E_m)."""
    k1, k2 = a.shape[1], b.shape[1]
    ma, mb = a.mean(1), b.mean(1)
    va, vb = a.var(1, ddof=1), b.var(1, ddof=1)
    gap = mb - ma
    sea, seb = np.sqrt(va / k1), np.sqrt(vb / k2)
    res = {
        "R": (a.max(1) < b.min(1) - 1e-9) | (b.max(1) < a.min(1) - 1e-9),
        "S1": np.abs(gap) > sea + seb + 1e-12,
        "S2": np.abs(gap) > np.sqrt(sea ** 2 + seb ** 2) + 1e-12,
    }
    # Welch
    se2 = va / k1 + vb / k2
    with np.errstate(divide="ignore", invalid="ignore"):
        tw = np.where(se2 > 0, gap / np.sqrt(se2), np.where(gap != 0, np.inf, 0.0))
        df = np.where(se2 > 0, se2 ** 2 / ((va / k1) ** 2 / (k1 - 1) + (vb / k2) ** 2 / (k2 - 1)), 1.0)
        df = np.where(np.isfinite(df) & (df > 0), df, 1.0)
        p = 2 * tdist.sf(np.abs(tw), df)
    res["W"] = p < 0.05
    # pooled TOST
    sp = np.sqrt(((k1 - 1) * va + (k2 - 1) * vb) / (k1 + k2 - 2))
    hw90 = t_quantile(0.95, k1 + k2 - 2) * sp * math.sqrt(1 / k1 + 1 / k2)
    for m in margins:
        res[f"E{m}"] = np.abs(gap) + hw90 <= m
    return res


def rates(a, b, margins):
    v = verdicts(a, b, margins)
    return {key: float(val.mean()) for key, val in v.items()}


results = {"n_trials": N, "seed": 7}

# ---------------------------------------------------------------- (a) normal noise, gap in SD units
KS, DELTAS = (2, 3, 4, 5, 6, 8, 10), (0, 0.5, 1, 1.5, 2, 3, 4)
normal = {}
for k in KS:
    for d in DELTAS:
        a = rng.standard_normal((N, k)); b = rng.standard_normal((N, k)) + d
        r = rates(a, b, margins=(0.5, 1, 2, 3))  # margins in SD units here
        r["R_exact"] = rule_mismatch_rate_normal(k, d)
        normal[f"k={k},gap={d}"] = r
results["normal_sd_units"] = normal
results["closed_form_false_alarm"] = {str(k): rule_false_alarm_exact(k) for k in KS}

# "rewards noise": fixed true gap of 2 points, common SD sigma; and one-sided (port noisier, original SD 1)
noise_common = {str(s): {"R": 1 - rule_mismatch_rate_normal(3, 2.0 / s)} for s in (0.25, 0.5, 1, 1.5, 2, 3, 5, 10, 100)}
for s in (0.25, 0.5, 1, 1.5, 2, 3, 5, 10, 100):
    a = rng.standard_normal((N, 3)) * s; b = rng.standard_normal((N, 3)) * s + 2.0
    r = rates(a, b, margins=(3, 5))
    noise_common[str(s)].update({"W_pass": 1 - r["W"], "S1_pass": 1 - r["S1"], "E3": r["E3"], "E5": r["E5"]})
noise_one_sided = {}
for s in (0.25, 0.5, 1, 2, 4, 8, 32, 100):
    a = rng.standard_normal((N, 3)); b = rng.standard_normal((N, 3)) * s + 1.0
    r = rates(a, b, margins=(3,))
    noise_one_sided[str(s)] = {"R_pass": 1 - r["R"], "W_pass": 1 - r["W"], "S1_pass": 1 - r["S1"]}
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
                r["implied_run_sd_points"] = 100 * math.sqrt(p * (1 - p) / n)
                binom[f"n={n},p={p},k={k},gap={d}"] = r
results["binomial_points"] = binom

# ---------------------------------------------------------------- (c) realistic per-task heterogeneity
realistic = {}
if pertask_dir:
    files = sorted(glob.glob(os.path.join(pertask_dir, "*", "harbor.csv")))
    for f in files:
        adapter = os.path.basename(os.path.dirname(f))
        by_task = {}
        for row in csv.DictReader(open(f)):
            try:
                by_task.setdefault(row["task_id"], []).append(float(row["reward"]))
            except ValueError:
                pass
        if len(by_task) < 20:
            continue
        # a task's pass probability: Beta(1,1)-shrunk pass rate over its runs; fractional rewards treated as probabilities
        p_i = np.array([(sum(v) + 1) / (len(v) + 2) for v in by_task.values()])
        base = float(p_i.mean() * 100)
        per = {"n_tasks": len(p_i), "base_rate_points": base, "runs_per_task": float(np.mean([len(v) for v in by_task.values()]))}
        for k in (3, 5):
            for d in (0, 1, 2, 3, 5, 10):
                # port side: scale pass probabilities so the expected mean drops by d points
                factor = max(0.0, 1 - d / base) if base > 0 else 0.0
                pa = p_i; pbv = p_i * factor
                nt = 20000  # trials (per-task simulation is heavier)
                a = (rng.random((nt, k, len(p_i))) < pa).mean(2) * 100
                b = (rng.random((nt, k, len(p_i))) < pbv).mean(2) * 100
                r = rates(a, b, margins=(2, 3, 5))
                r["implied_run_sd_points"] = float(a.std(1, ddof=1).mean())
                per[f"k={k},gap={d}"] = r
        realistic[adapter] = per
results["realistic_pertask"] = realistic

# ---------------------------------------------------------------- summaries used in the memo
summ = {}
k3 = {d: normal[f"k=3,gap={d}"] for d in DELTAS}
summ["k3_normal_false_alarm"] = {r: k3[0][r] for r in ("R", "S1", "S2", "W")}
summ["k3_normal_detect_2sd"] = {r: k3[2][r] for r in ("R", "S1", "S2", "W")}
summ["k3_normal_detect_1sd"] = {r: k3[1][r] for r in ("R", "S1", "S2", "W")}
summ["R_detect_2sd_by_k"] = {str(k): normal[f"k={k},gap=2"]["R_exact"] for k in KS}
summ["W_detect_2sd_by_k"] = {str(k): normal[f"k={k},gap=2"]["W"] for k in KS}
summ["E_equiv_shown_at_gap0_by_k_margin1sd"] = {str(k): normal[f"k={k},gap=0"]["E1"] for k in KS}
summ["binomial_k3_p0.3_false_alarm_by_n"] = {str(n): binom[f"n={n},p=0.3,k=3,gap=0"]["R"] for n in (10, 30, 50, 100, 300, 1000)}
summ["binomial_k3_p0.3_detect_5pts_by_n"] = {str(n): {r: binom[f"n={n},p=0.3,k=3,gap=5"][r] for r in ("R", "S1", "S2", "W")} for n in (10, 30, 50, 100, 300, 1000)}
if realistic:
    summ["realistic_k3_false_alarm_R"] = {a: v["k=3,gap=0"]["R"] for a, v in realistic.items()}
    summ["realistic_k3_detect_5pts"] = {a: {r: v["k=3,gap=5"][r] for r in ("R", "S1", "S2", "W")} for a, v in realistic.items()}
results["summary"] = summ
with open(os.path.join(out, "rq1_rules.json"), "w") as fh:
    json.dump(results, fh, indent=1)

# ---------------------------------------------------------------- figure
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

fig, axes = plt.subplots(1, 3, figsize=(12, 3.6))
ax = axes[0]
for rule, lab, ls in (("R", "range overlap (Harbor)", "-"), ("S1", "mean ± SEM bars overlap", "--"), ("S2", "|gap| ≤ SE of difference", "-."), ("W", "Welch t-test, p < .05", ":")):
    ax.plot(DELTAS, [normal[f"k=3,gap={d}"][rule] for d in DELTAS], ls, marker="o", ms=3, label=lab)
ax.set_xlabel("true gap, in run-to-run SDs"); ax.set_ylabel("P(verdict = mismatch)"); ax.set_title("k = 3 runs per side, normal noise", fontsize=10)
ax.axhline(0.05, color="grey", lw=0.5); ax.legend(fontsize=7, frameon=False); ax.set_ylim(0, 1)
ax = axes[1]
for rule, lab in (("R", "range overlap"), ("S1", "SEM bars overlap"), ("W", "Welch t-test")):
    ax.plot(KS, [normal[f"k={k},gap=2"][rule if rule != "R" else "R_exact"] for k in KS], marker="o", ms=3, label=lab)
ax.set_xlabel("runs per side k"); ax.set_ylabel("P(detect a 2 SD gap)"); ax.set_title("detection of a fixed 2 SD gap", fontsize=10); ax.set_ylim(0, 1); ax.legend(fontsize=7, frameon=False)
ax = axes[2]
sds = [0.25, 0.5, 1, 1.5, 2, 3, 5, 10]
ax.plot(sds, [noise_common[str(s)]["R"] for s in sds], marker="o", ms=3, label="range overlap: P(pass)")
ax.plot(sds, [noise_common[str(s)]["E3"] for s in sds], marker="s", ms=3, label="TOST ±3: P(equivalence shown)")
ax.plot(sds, [noise_common[str(s)]["W_pass"] for s in sds], marker="^", ms=3, label="Welch: P(no significant gap)")
ax.set_xscale("log"); ax.set_xlabel("run-to-run SD, points (both sides)"); ax.set_ylabel("probability"); ax.set_title("true gap fixed at 2 points, k = 3", fontsize=10); ax.set_ylim(0, 1); ax.legend(fontsize=7, frameon=False)
fig.tight_layout()
fig.savefig(os.path.join(out, "figures", "fig_rq1_rules.png"), dpi=200)
fig.savefig(os.path.join(out, "figures", "fig_rq1_rules.pdf"))

print("k=3, normal: false alarm", {r: round(v, 3) for r, v in summ["k3_normal_false_alarm"].items()})
print("k=3, normal: detect 1 SD", {r: round(v, 3) for r, v in summ["k3_normal_detect_1sd"].items()}, "| detect 2 SD", {r: round(v, 3) for r, v in summ["k3_normal_detect_2sd"].items()})
print("R detects 2 SD gap by k:", {k: round(v, 3) for k, v in summ["R_detect_2sd_by_k"].items()})
print("W detects 2 SD gap by k:", {k: round(v, 3) for k, v in summ["W_detect_2sd_by_k"].items()})
print("TOST(±1 SD) shows equivalence at gap 0, by k:", {k: round(v, 3) for k, v in summ["E_equiv_shown_at_gap0_by_k_margin1sd"].items()})
print("binomial k=3 p=.3: R false alarm by n:", {n: round(v, 3) for n, v in summ["binomial_k3_p0.3_false_alarm_by_n"].items()})
print("binomial k=3 p=.3: detect 5-point gap by n:", {n: {r: round(x, 2) for r, x in v.items()} for n, v in summ["binomial_k3_p0.3_detect_5pts_by_n"].items()})
print("pass prob, gap 2 points, common SD:", {s: round(v["R"], 3) for s, v in noise_common.items()})
print("pass prob, gap 1 SD, port SD only:", {s: round(v["R_pass"], 3) for s, v in noise_one_sided.items()})
print("realistic adapters simulated:", len(realistic))
