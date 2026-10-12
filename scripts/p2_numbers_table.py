#!/usr/bin/env python3
"""Phase 2: write results/phase2/NUMBERS_phase2.md, mapping each number quoted in the Phase 2 memo
to its value, script and output file. Usage: python -I scripts/p2_numbers_table.py <phase2_dir>
"""
import json
import os
import sys

p2 = sys.argv[1]
L = lambda n: json.load(open(os.path.join(p2, n)))  # noqa: E731
r1, r2, r3n, r3p, r3d = L("rq1_rules.json"), L("rq2_summary.json"), L("rq3_runs_needed.json"), L("rq3_paired.json"), L("rq3_defects.json")
s1, h = r1["summary"], r2["summaries"]["headline_k3"]
rows = []
A = lambda label, val, script, out: rows.append((label, val, script, out))  # noqa: E731
S, O = "scripts/p2_rq1_rules.py", "results/phase2/rq1_rules.json"
for r in ("R", "S1", "S2", "S3", "T", "W"):
    A(f"RQ1 false alarm at k=3, {r}", round(s1["k3_normal_false_alarm"][r], 3), S, O)
    A(f"RQ1 detect 2 SD at k=3, {r}", round(s1["k3_normal_detect_2sd"][r], 3), S, O)
    A(f"RQ1 t-statistic at {r}'s false alarm detects 2 SD", round(s1["k3_t_at_matched_false_alarm_detect_2sd"][r], 3), S, O)
A("RQ1 R false alarm by k", {k: round(v, 3) for k, v in s1["false_alarm_by_k"]["R"].items()}, S, O)
A("RQ1 R detects 2 SD by k", {k: round(v, 2) for k, v in s1["R_detect_2sd_by_k"].items()}, S, O)
A("RQ1 T detects 2 SD by k", {k: round(v, 2) for k, v in s1["T_detect_2sd_by_k"].items()}, S, O)
A("RQ1 P(pass) for a 2-point gap by common SD, k=3", {k: round(v["R"], 2) for k, v in r1["pass_prob_fixed_gap2_common_sd_k3"].items()}, S, O)
A("RQ1 P(pass), port side noisier only", {k: round(v["R_pass"], 2) for k, v in r1["pass_prob_fixed_gap1_port_sd_only_k3"].items()}, S, O)
A("RQ1 discrete false alarm by n tasks (k=3, p=0.3)", {k: round(v, 3) for k, v in s1["binomial_k3_p0.3_false_alarm_by_n"].items()}, S, O)
A("RQ1 realistic medians (light prior)", {c: {r: round(v, 2) for r, v in d.items()} for c, d in s1["realistic_median_over_adapters"].items()}, S, O)
A("RQ1 realistic implied run SD quartiles", {k: [round(x, 2) for x in v] for k, v in s1["realistic_implied_run_sd_quartiles"].items()}, S, O)
A("RQ1 expected smallest provable margin under parity, k=3 (SD units)", round(s1["expected_smallest_margin_sd_units_k3"], 2), S, O)
A("RQ1 runs/side for 80% TOST power at gap 0, margin in SD", s1["tost_runs_needed_sd_units_power80_gap0"], S, O)
S, O = "scripts/p2_rq2_evidence.py", "results/phase2/rq2_summary.json"
for key in ("headline_k3", "all_k_ge_2", "one_per_adapter", "in_paper_table_k3", "subset_k3", "full_k3", "with_identical_rows"):
    x = r2["summaries"][key]
    A(f"RQ2 [{x['label']}] n / median gap / median SD / margin quartiles / within 2,3,5 / fail overlap / S1,S2,S3 / passes with margin>5",
      [x["n"], round(x["median_abs_gap"], 2), round(x["median_pooled_sd"], 2), [round(q, 1) for q in x["smallest_margin_quartiles"]],
       [x["within_margin_tost"][m] for m in ("2", "3", "5")], x["n_fail_overlap"], [x["n_S1_mismatch"], x["n_S2_mismatch"], x["n_S3_mismatch"]], x["overlap_pass_but_margin_over_5"]], S, O)
A("RQ2 headline within-margin range under ±0.1 perturbation", h["within_margin_range_under_0.1_perturbation"], S, O)
A("RQ2 headline largest gaps (adapter, metric, gap, margin)", h["largest_gaps"][:4], S, O)
A("RQ2 overlap vs TOST agreement (headline)", r2["summaries"]["overlap_vs_tost_headline"], S, O)
A("RQ2 selection check (expected, observed, p)", {k: (round(v["expected_mismatches_if_all_ports_perfect"], 1), v["observed"], round(v["p_observed_or_fewer"], 3)) for k, v in r2["summaries"]["selection_check_headline"].items()}, S, O)
A("RQ2 by k: n and within 3 / 5", {k: (v["n"], v["within_margin_tost"]["3"], v["within_margin_tost"]["5"]) for k, v in r2["summaries"]["by_k"].items() if v["n"]}, S, O)
S, O = "scripts/p2_rq3_runs_needed.py", "results/phase2/rq3_runs_needed.json"
A("RQ3 observed pooled SD quartiles (k=3 set)", [round(x, 2) for x in r3n["headline_sd_quartiles"]], S, O)
for key, v in r3n["table"].items():
    A(f"RQ3 runs/side {key}: 80% / 90% power (plug-in k, its power)", [v["k_power80"], v["k_power90"], v["k_plugin"], v["power_at_plugin_k"]], S, O)
A("RQ3 per-comparison runs for ±3 at gap 0 (quartiles; share <=3, <=5, <=10)", [r3n["per_comparison_distribution_k3"]["m=3"][k] for k in ("gap0_quartiles", "gap0_share_k_le_3", "gap0_share_k_le_5", "gap0_share_k_le_10")], S, O)
A("RQ3 comparisons whose gap exceeds the margin (±2, ±3, ±5)", {m: v["obsgap_unreachable_gap_ge_margin"] for m, v in r3n["per_comparison_distribution_k3"].items()}, S, O)
S, O = "scripts/p2_rq3_paired.py", "results/phase2/rq3_paired.json"
for k, v in r3p["summary"].items():
    A(f"RQ3 paired: {k}", v if not isinstance(v, list) else [round(x, 2) for x in v], S, O)
S, O = "scripts/p2_rq3_defects.py", "results/phase2/rq3_defects.json"
A("RQ3 defects: adapters, replications", [r3d["n_adapters"], r3d["reps"]], S, O)
for cell in ("break,f=0.0,k=3", "break,f=0.02,k=3", "break,f=0.05,k=3", "break,f=0.1,k=3", "break,f=0.2,k=3", "leak,f=0.1,k=3", "break,f=0.1,k=5", "break,f=0.1,k=10", "break,f=0.0,k=5", "break,f=0.0,k=10", "beta11,break,f=0.1,k=3"):
    v = r3d["aggregate"][cell]
    A(f"RQ3 defects {cell}: gap, R, S1, T, paired, E3, E5", [round(v["expected_gap_points_median"], 1)] + [round(v[r], 2) for r in ("R", "S1", "T", "P", "E3", "E5")], S, O)
lines = ["# Phase 2 numbers: value, script, output", "", "| Number | Value | Script | Output |", "|---|---|---|---|"]
for label, val, script, out in rows:
    lines.append(f"| {label} | `{json.dumps(val)}` | `{script}` | `{out}` |")
with open(os.path.join(p2, "NUMBERS_phase2.md"), "w") as fh:
    fh.write("\n".join(lines) + "\n")
print(f"{len(rows)} numbers written to {os.path.join(p2, 'NUMBERS_phase2.md')}")
