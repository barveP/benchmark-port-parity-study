#!/usr/bin/env python3
"""Phase 0: compare every number reported by the exploratory first pass (scripts/first_pass/) with the
regenerated results, and write NUMBERS.md mapping each number to its script and output file.
The first-pass values are kept as constants in this file.
Usage: python -I scripts/p0_check_first_pass.py <results_dir> <numbers_md_path>
"""
import json
import os
import sys

res_dir, numbers_md = sys.argv[1], sys.argv[2]
L = lambda name: json.load(open(os.path.join(res_dir, name)))  # noqa: E731
inv, ov, rr, fp = L("inventory.json"), L("overlap.json"), L("rule_error_rates.json"), L("first_pass_cut.json")

rows = []  # (label, first-pass value, reproduced value, script, output, tolerance)
def add(label, first_pass, got, script, output, tol=0):
    rows.append((label, first_pass, got, script, output, tol))

S_INV, S_OV, S_RR, S_FP = "scripts/p0_inventory.py", "scripts/p0_overlap.py", "scripts/p0_rule_error_rates.py", "scripts/p0_first_pass_cut.py"
O_INV, O_OV, O_RR, O_FP = "results/phase0/inventory.json", "results/phase0/overlap.json", "results/phase0/rule_error_rates.json", "results/phase0/first_pass_cut.json"

add("files", 84, inv["n_files"], S_INV, O_INV)
add("experiments", 121, inv["n_experiments"], S_INV, O_INV)
add("metric rows", 298, inv["n_metric_rows"], S_INV, O_INV)
r = inv["runs_per_side_by_experiment"]
for k, v in (("3", 68), ("1", 15), ("2", 9), ("5", 9), ("4", 4), ("6", 2), ("8", 2), ("missing", 12)):
    label = "experiments with no run count recorded" if k == "missing" else f"experiments with {k} run{'' if k == '1' else 's'} per side"
    add(label, v, r.get(k, 0), S_INV, O_INV)
add("parity on a subset", 38, inv["parity_set"].get("subset", 0), S_INV, O_INV)
add("parity on the full set", 77, inv["parity_set"].get("full", 0), S_INV, O_INV)
add("parity set unknown", 6, inv["parity_set"].get("unknown", 0), S_INV, O_INV)
add("metric rows with runs on both sides", 254, ov["n_paired"], S_OV, O_OV)
add("rows failing range overlap", 8, ov["n_fail_overlap"], S_OV, O_OV)
add("  of which 3 runs per side", 5, ov["n_fail_overlap_3v3"], S_OV, O_OV)
add("  of which a single run on one side", 3, ov["n_fail_overlap_single_run_side"], S_OV, O_OV)
first_pass_fail = {("hle", "Calibration error (%, beta=10)"), ("pixiu", "acc_stderr"), ("pixiu", "bart_score"),
                   ("research-code-bench", "scaled_success_rate (%)"), ("usaco", "Resolved Rate (%)"),
                   ("osworld", "success rate (pass@1, no-result counted as 0)"), ("programbench", "test_pass_rate"),
                   ("swebench", "Resolved Rate")}
got_fail = {tuple(x) for x in ov["fail_row_keys"]}
add("failing rows are the eight the first pass names", "yes", "yes" if got_fail == first_pass_fail else f"NO: {sorted(got_fail ^ first_pass_fail)}", S_OV, O_OV)
add("rows with identical run lists", 45, ov["n_identical_lists"], S_OV, O_OV)
add("rows with zero spread on both sides", 36, ov["n_zero_spread_both"], S_OV, O_OV)
first_pass_sim = {"2": [0.33, 0.49, 0.78, 0.94, 0.99], "3": [0.10, 0.26, 0.63, 0.89, 0.98],
                  "5": [0.008, 0.07, 0.38, 0.77, 0.96], "8": [0.000, 0.01, 0.16, 0.59, 0.90]}
for k, vals in first_pass_sim.items():
    for d, v in zip(("0", "1", "2", "3", "4"), vals):
        add(f"P(mismatch) k={k}, gap {d} SD (simulation)", v, round(rr["sim"][k][d], 3), S_RR, O_RR, tol=0.01)  # first-pass values are rounded to 2 decimals; Monte Carlo SE ~0.001
add("closed form k=3: 2(3!)^2/6!", 0.10, rr["closed_form_false_alarm"]["3"], S_RR, O_RR, tol=1e-12)
import math  # noqa: E402
worst = 0.0
for k in first_pass_sim:
    for d in ("0", "1", "2", "3", "4"):
        p_exact, p_sim = rr["exact"][k][d], rr["sim"][k][d]
        se = math.sqrt(max(p_exact * (1 - p_exact), 1e-7) / rr["n_trials"])
        worst = max(worst, abs(p_sim - p_exact) / se)
add("simulation vs exact integral, worst absolute difference in Monte Carlo SEs (must be < 4)", "< 4", round(worst, 2), S_RR, O_RR, tol=4)
add("first-pass cut: comparisons analysed", 43, fp["n_analysed"], S_FP, O_FP)
add("first-pass cut: median run-to-run SD (points)", 2.2, round(fp["median_pooled_sd"], 1), S_FP, O_FP, tol=0.05)
add("first-pass cut: median gap (points)", 0.6, round(fp["median_gap"], 1), S_FP, O_FP, tol=0.05)
lg = {a: g for a, _, g in fp["largest_gaps"]}
for a, g in (("rexbench", 8.3), ("pixiu", 4.9), ("gdb", 4.6), ("multi-swe-bench", 3.3), ("usaco", 2.6)):
    add(f"first-pass cut: largest gaps, {a}", g, round(lg.get(a, float('nan')), 1), S_FP, O_FP, tol=0.05)
add("first-pass cut: fail range overlap", 1, fp["n_fail_overlap"], S_FP, O_FP)
fr = fp["fail_overlap_rows"]
add("first-pass cut: the one failure is usaco [39.5, 40.5, 41.0] vs [45.7, 42.1, 41.1]", "yes",
    "yes" if fr and fr[0][0] == "usaco" and fr[0][2] == [39.5, 40.5, 41.0] and fr[0][3] == [45.7, 42.1, 41.1] else "NO", S_FP, O_FP)
for m, v in (("2", 5), ("3", 12), ("5", 23)):
    add(f"first-pass cut: TOST equivalence within +-{m}", v, fp["tost_within"][m], S_FP, O_FP)
for m, v in (("2", 3), ("3", 7), ("5", 16)):
    add(f"first-pass cut: 95% CI equivalence within +-{m}", v, fp["ci95_within"][m], S_FP, O_FP)
add("first-pass cut: gaps distinguishable from zero", 0, fp["n_distinguishable_from_zero"], S_FP, O_FP)
for m, v in (("2", 14), ("3", 6), ("5", 3)):
    add(f"runs per side needed for +-{m} (median noise, gap 0.6; first-pass plug-in rule)", v, fp["runs_needed_plugin_gap0.6_median_sd"][m], S_FP, O_FP)
for k in first_pass_sim:
    add(f"exact integral equals closed form at gap 0, k={k}", rr["closed_form_false_alarm"][k], rr["exact"][k]["0"], S_RR, O_RR, tol=1e-9)
for k, vals in first_pass_sim.items():
    for d, v in zip(("0", "1", "2", "3", "4"), vals):
        add(f"P(mismatch) k={k}, gap {d} SD: first pass (rounded) vs exact integral", v, round(rr["exact"][k][d], 3), S_RR, O_RR, tol=0.0075)

def ok(first_pass, got, tol):
    if isinstance(first_pass, str) and first_pass.startswith("<"):
        return float(got) < float(first_pass[1:])
    try:
        return abs(float(first_pass) - float(got)) <= tol
    except (TypeError, ValueError):
        return first_pass == got

n_ok = sum(ok(f, g, t) for _, f, g, _, _, t in rows)
lines = ["# Numbers: first pass vs reproduction", "",
         f"Source snapshot: Harbor commit dc933be707feafbb9efcdf092cb8a0e391332617 (see data/raw/MANIFEST.json). "
         f"{n_ok} of {len(rows)} numbers match; where the first pass rounded a value, a match means agreement "
         "within that rounding (for the simulated probabilities, within rounding plus Monte Carlo error).", "",
         "The first-pass cut is the first pass's one-main-metric-per-experiment selection of 43 comparisons "
         "(three runs per side), defined in `scripts/p0_first_pass_cut.py`.", "",
         "| Number (as reported by the first pass) | First pass | Reproduced | Match | Script | Output |", "|---|---|---|---|---|---|"]
for label, f, g, s, o, t in rows:
    lines.append(f"| {label} | {f} | {g} | {'yes' if ok(f, g, t) else 'NO'} | `{s}` | `{o}` |")
with open(numbers_md, "w") as fh:
    fh.write("\n".join(lines) + "\n")
print("\n".join(lines))
print(f"\n{n_ok} of {len(rows)} match")
sys.exit(0 if n_ok == len(rows) else 1)
