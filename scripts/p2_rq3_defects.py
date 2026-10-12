#!/usr/bin/env python3
"""Phase 2, RQ3c: injected-defect study on real per-task outcomes.

Primary model (amendment 6b): adapters with binary per-task outcomes and validated replicate Harbor
runs (MANIFEST.json use_for_defect_model and binary_outcomes). A task's pass probability is its light-
shrinkage pass rate (passes + 0.05) / (runs + 0.1) (amendment 5). Both sides share these probabilities;
a defect on the port side BREAKS a fraction f of tasks (probability 0) or LEAKS them (probability 1);
f = 0 is the no-defect control (amendment 3). For k runs per side, run scores are simulated and each
rule applied: R, S1, S2, S3, W, T (run level), E3, E5 (TOST shown), P and PE3/PE5 (paired t on task
means), CMH (stratified-by-task z; amendment 6c). Sensitivities: Beta(1,1) prior (break, k = 3);
fractional-score adapters by within-task resampling of their observed rewards. Aggregates report the
mean, median and interquartile range over adapters. Per adapter, the model's run SD
100 sqrt(sum p (1 - p)) / n and the dispersion ratio of the real Harbor runs (observed between-run
variance over the variance implied by within-task flip rates) are recorded.
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
FS, KS, CHUNK = (0.0, 0.02, 0.05, 0.1, 0.2), (3, 5, 10), 250
RULES = ("R", "S1", "S2", "S3", "W", "T", "E3", "E5", "P", "PE3", "PE5", "CMH")
rng = np.random.default_rng(7)
man = json.load(open(os.path.join(pertask_dir, "MANIFEST.json")))["adapters"]


def load_tasks(adapter):
    """{task_id: [rewards over runs]} for the Harbor side, applying drop_runs and scaling to [0, 1]."""
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


def dispersion_ratio(by_task):
    """Observed variance of the real run scores over the variance implied by within-task flip rates.

    Only tasks present in every run are used; implied Var(run mean) = sum_i s_i^2 / n^2 with s_i^2 the
    sample variance of task i over its runs. Returns None when fewer than 2 complete runs exist.
    """
    runs = max(len(v) for v in by_task.values())
    full = [v for v in by_task.values() if len(v) == runs]
    if runs < 2 or len(full) < 2:
        return None
    X = np.array(full)  # tasks x runs
    obs = X.mean(0).var(ddof=1) * 1e4
    implied = X.var(1, ddof=1).sum() / len(full) ** 2 * 1e4
    return float(obs / implied) if implied > 0 else None


def simulate_cell(draw_a, draw_b, k, n, n_def, kind, reps):
    """draw_a(reps, k) -> outcomes (reps, k, n) for the original side; draw_b(reps, k, defect_mask) for the port."""
    acc = {}
    gaps = []
    for start in range(0, reps, CHUNK):
        r = min(CHUNK, reps - start)
        mask = np.zeros((r, n), dtype=bool)
        if n_def:
            for i in range(r):
                mask[i, rng.choice(n, n_def, replace=False)] = True
        xa = draw_a(r, k)
        xb = draw_b(r, k, mask, kind)
        a, b = xa.mean(2) * 100, xb.mean(2) * 100
        v = rule_verdicts(a, b, margins=(3, 5)); v.update(paired_task_verdicts(xa, xb))
        for key in RULES:
            acc[key] = acc.get(key, 0) + int(v[key].sum())
        gaps.append(float((b.mean(1) - a.mean(1)).mean()) * r)
    return {key: val / reps for key, val in acc.items()} | {"expected_gap_points": sum(gaps) / reps, "n_tasks_affected": n_def}


results = {}
for adapter in sorted(a for a, v in man.items() if v.get("use_for_defect_model")):
    by_task = load_tasks(adapter)
    n = len(by_task)
    if n < 20:
        continue
    binary = bool(man[adapter].get("binary_outcomes"))
    per = {"n_tasks": n, "runs_per_task": float(np.mean([len(v) for v in by_task.values()])), "binary_outcomes": binary,
           "dispersion_ratio_harbor_runs": dispersion_ratio(by_task)}
    if binary:
        for prior, (alpha, beta) in (("light", (0.05, 0.05)), ("beta11", (1.0, 1.0))):
            p_i = np.array([(sum(v) + alpha) / (len(v) + alpha + beta) for v in by_task.values()])
            per[f"base_rate_points_{prior}"] = float(p_i.mean() * 100)
            per[f"model_run_sd_points_{prior}"] = float(100 * math.sqrt((p_i * (1 - p_i)).sum()) / n)

            def draw_a(r, k, p_i=p_i):
                return rng.random((r, k, n)) < p_i

            def draw_b(r, k, mask, kind, p_i=p_i):
                pb = np.where(mask, 0.0 if kind == "break" else 1.0, p_i)
                return rng.random((r, k, n)) < pb[:, None, :]

            for kind in ("break", "leak"):
                for fr in FS:
                    for k in KS:
                        if prior == "beta11" and (k != 3 or kind != "break"):
                            continue
                        n_def = 0 if fr == 0 else max(1, int(round(fr * n)))
                        cell = f"{kind},f={fr},k={k}" if prior == "light" else f"beta11,{kind},f={fr},k={k}"
                        per[cell] = simulate_cell(draw_a, draw_b, k, n, n_def, kind, REPS)
    else:
        # fractional scores: resample each task's observed rewards across its runs (within-task bootstrap)
        obs = [np.array(v) for v in by_task.values()]
        per["base_rate_points_resample"] = float(np.mean([v.mean() for v in obs]) * 100)
        per["model_run_sd_points_resample"] = float(100 * math.sqrt(sum(v.var() for v in obs)) / n)
        lens = np.array([len(v) for v in obs]); maxlen = lens.max()
        padded = np.array([np.pad(v, (0, maxlen - len(v)), mode="edge") for v in obs])  # tasks x maxlen

        def draw_a(r, k):
            idx = (rng.random((r, k, n)) * lens).astype(int)
            return padded[np.arange(n), idx]

        def draw_b(r, k, mask, kind):
            x = draw_a(r, k)
            return np.where(mask[:, None, :], 0.0 if kind == "break" else 1.0, x)

        for kind in ("break", "leak"):
            for fr in FS:
                for k in KS:
                    n_def = 0 if fr == 0 else max(1, int(round(fr * n)))
                    per[f"resample,{kind},f={fr},k={k}"] = simulate_cell(draw_a, draw_b, k, n, n_def, kind, REPS)
    results[adapter] = per
    c = per.get("break,f=0.1,k=3") or per.get("resample,break,f=0.1,k=3")
    print(f"{adapter}: n={n} {'binary' if binary else 'fractional'} model sd {per.get('model_run_sd_points_light', per.get('model_run_sd_points_resample')):.1f} dispersion {per['dispersion_ratio_harbor_runs']} | break 10% k=3 gap {c['expected_gap_points']:.1f} -> R {c['R']:.2f} T {c['T']:.2f} P {c['P']:.2f} CMH {c['CMH']:.2f} | E5 {c['E5']:.2f}")


def aggregate(adapters, prefix=""):
    out = {}
    cells = sorted({key for a in adapters for key in results[a] if key.startswith(prefix) and "f=" in key and not key.startswith(("beta11", "resample")) == (prefix == "")} if prefix else
                   {key for a in adapters for key in results[a] if "f=" in key and not key.startswith(("beta11", "resample"))})
    for cell in cells:
        vals = {rule: np.array([results[a][cell][rule] for a in adapters if cell in results[a]]) for rule in RULES}
        out[cell] = {rule: {"mean": float(v.mean()), "median": float(np.median(v)), "q25": float(np.percentile(v, 25)), "q75": float(np.percentile(v, 75))} for rule, v in vals.items()}
        g = np.array([results[a][cell]["expected_gap_points"] for a in adapters if cell in results[a]])
        out[cell]["expected_gap_points"] = {"mean": float(g.mean()), "median": float(np.median(g))}
        out[cell]["n_adapters"] = int(len(g))
    return out


binary_adapters = [a for a in results if results[a]["binary_outcomes"]]
frac_adapters = [a for a in results if not results[a]["binary_outcomes"]]
well_dispersed = [a for a in binary_adapters if results[a]["dispersion_ratio_harbor_runs"] is None or results[a]["dispersion_ratio_harbor_runs"] >= 0.1 + 1e-9]
agg = {"primary_binary_light": aggregate(binary_adapters), "binary_dispersion_ratio_ge_0.1": aggregate(well_dispersed),
       "beta11_break_k3": {cell: aggregate(binary_adapters, "beta11")[cell] for cell in aggregate(binary_adapters, "beta11")} if binary_adapters else {},
       "fractional_resample": aggregate(frac_adapters, "resample") if frac_adapters else {}}
summary = {"reps": REPS, "fractions": FS, "ks": KS, "n_binary": len(binary_adapters), "n_fractional": len(frac_adapters), "n_well_dispersed": len(well_dispersed),
           "dispersion_ratio_quartiles_binary": [float(x) for x in np.percentile([results[a]["dispersion_ratio_harbor_runs"] for a in binary_adapters if results[a]["dispersion_ratio_harbor_runs"] is not None], [25, 50, 75])],
           "under_dispersed_below_0.1": sorted(a for a in binary_adapters if results[a]["dispersion_ratio_harbor_runs"] is not None and results[a]["dispersion_ratio_harbor_runs"] < 0.1 + 1e-9),
           "model_run_sd_quartiles_light": [float(x) for x in np.percentile([results[a]["model_run_sd_points_light"] for a in binary_adapters], [25, 50, 75])],
           "p_minus_t_at_break10_k3": {"n_P_gt_T": int(sum(results[a]["break,f=0.1,k=3"]["P"] > results[a]["break,f=0.1,k=3"]["T"] for a in binary_adapters)),
                                        "quartiles": [float(x) for x in np.percentile([results[a]["break,f=0.1,k=3"]["P"] - results[a]["break,f=0.1,k=3"]["T"] for a in binary_adapters], [25, 50, 75])]}}
with open(os.path.join(p2, "rq3_defects.json"), "w") as fh:
    json.dump({"summary": summary, "aggregate": agg, "adapters": results}, fh, indent=1)

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
os.makedirs(os.path.join(p2, "figures"), exist_ok=True)
A = agg["primary_binary_light"]
fig, axes = plt.subplots(1, 3, figsize=(12.5, 3.6), sharey=True)
for ax, (kind, k) in zip(axes, (("break", 3), ("leak", 3), ("break", 10))):
    for rule, lab, ls, col in (("R", "range overlap", "-", "tab:blue"), ("T", "pooled t-test", ":", "tab:green"), ("P", "paired per-task t", "-", "tab:red"), ("CMH", "stratified per-task test", "--", "tab:purple")):
        ys = [A[f"{kind},f={fr},k={k}"][rule]["mean"] for fr in FS]
        ax.plot(FS, ys, ls, marker="o", ms=3, color=col, label=lab)
        if rule in ("T", "CMH"):
            ax.fill_between(FS, [A[f"{kind},f={fr},k={k}"][rule]["q25"] for fr in FS], [A[f"{kind},f={fr},k={k}"][rule]["q75"] for fr in FS], color=col, alpha=0.08)
    ax.axvline(0, color="grey", lw=0.5)
    ax.set_xlabel(f"fraction of tasks {'broken' if kind == 'break' else 'leaked'} on the port side")
    ax.set_title(f"{kind} defect, k = {k}; mean over {len(binary_adapters)} adapters (bands: IQR)", fontsize=9); ax.set_ylim(0, 1)
axes[0].set_ylabel("P(verdict = mismatch)"); axes[0].legend(fontsize=7, frameon=False)
fig.tight_layout(); fig.savefig(os.path.join(p2, "figures", "fig_rq3_defects.png"), dpi=200); fig.savefig(os.path.join(p2, "figures", "fig_rq3_defects.pdf"))

print("binary adapters:", len(binary_adapters), "| fractional:", frac_adapters, "| under-dispersed (<0.1):", summary["under_dispersed_below_0.1"])
print("dispersion ratio quartiles:", [round(x, 2) for x in summary["dispersion_ratio_quartiles_binary"]], "| model run SD quartiles:", [round(x, 2) for x in summary["model_run_sd_quartiles_light"]])
for cell in ("break,f=0.0,k=3", "break,f=0.02,k=3", "break,f=0.05,k=3", "break,f=0.1,k=3", "break,f=0.2,k=3", "leak,f=0.1,k=3", "break,f=0.1,k=5", "break,f=0.0,k=10", "break,f=0.1,k=10"):
    v = A[cell]
    print(f"{cell:18s} gap {v['expected_gap_points']['mean']:+5.1f} | " + " ".join(f"{r} {v[r]['mean']:.2f}({v[r]['median']:.2f})" for r in ("R", "S1", "T", "P", "CMH", "E3", "E5", "PE5")))
print("well-dispersed only, break 10% k=3:", {r: round(agg["binary_dispersion_ratio_ge_0.1"]["break,f=0.1,k=3"][r]["mean"], 2) for r in ("R", "T", "P", "CMH", "E5")})
print("beta11 break 10% k=3:", {r: round(agg["beta11_break_k3"]["beta11,break,f=0.1,k=3"][r]["mean"], 2) for r in ("R", "T", "P", "CMH")} if agg["beta11_break_k3"] else None)
print("fractional (resample) break 10% k=3:", {r: round(agg["fractional_resample"]["resample,break,f=0.1,k=3"][r]["mean"], 2) for r in ("R", "T", "P", "E5")} if agg["fractional_resample"] else None)
print("P - T at break 10% k=3:", summary["p_minus_t_at_break10_k3"])
