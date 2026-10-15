#!/usr/bin/env python3
"""Phase 0, number set B: Harbor's range-overlap rule applied to every metric row.

Reproduces the first pass (scripts/first_pass/parity_overlap.py) with the same definitions:
  * a side's run list = first non-empty numeric list among <side>_runs, <side>_trials
    (non-numeric entries such as "58.3%" are dropped; rows using tb_adapter_* are not paired)
  * paired row = both original and harbor run lists present
  * NO-OVERLAP = max(a) < min(b) or max(b) < min(a)
  * identical = the two run lists are equal
  * zero spread on both sides = len(a) >= 2 and each list holds a single distinct value
Usage: python -I scripts/p0_overlap.py <snapshot_dir> <out_dir>
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parity_lib import iter_metric_rows, lenient_runs, mean, range_separation, ranges_overlap, side_runs, zero_spread  # noqa: E402

root, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)

rows = []
for adapter, i, e, j, m in iter_metric_rows(root):
    a, b = side_runs(m, "original"), side_runs(m, "harbor")
    row = {"adapter": adapter, "exp": i, "metric_index": j, "agent": e.get("agent"),
           "model": e.get("model"), "metric": m.get("metric")}
    la = lenient_runs(m.get("original_runs")) or lenient_runs(m.get("original_trials"))
    lb = lenient_runs(m.get("harbor_runs")) or lenient_runs(m.get("harbor_trials"))
    row["lists_both_sides_lenient"] = bool(la and lb)
    if a is None or b is None:
        row["status"] = "no-paired-runs"
    else:
        row.update({
            "status": "overlap" if ranges_overlap(a, b) else "NO-OVERLAP",
            "k_original": len(a), "k_harbor": len(b),
            "original_runs": a, "harbor_runs": b,
            "mean_original": mean(a), "mean_harbor": mean(b), "gap": abs(mean(a) - mean(b)),
            "separation": range_separation(a, b),
            "float_tie": 0 < range_separation(a, b) < 1e-9,
            "identical_lists": a == b,
            "zero_spread_both": len(a) >= 2 and zero_spread(a) and zero_spread(b),
            "single_run_side": min(len(a), len(b)) < 2,
        })
    rows.append(row)

paired = [r for r in rows if r["status"] != "no-paired-runs"]
fail = [r for r in paired if r["status"] == "NO-OVERLAP"]
res = {
    "n_metric_rows": len(rows),
    "n_paired": len(paired),
    "n_paired_note": "rows with NUMERIC run lists on both sides; string-valued lists ('58.3%') are dropped here",
    "n_rows_with_lists_both_sides_incl_strings": sum(1 for r in rows if r["lists_both_sides_lenient"]),
    "n_no_paired_runs": len(rows) - len(paired),
    "n_fail_overlap": len(fail),
    "n_fail_overlap_3v3": sum(1 for r in fail if r["k_original"] == 3 and r["k_harbor"] == 3),
    "n_fail_overlap_single_run_side": sum(1 for r in fail if r["single_run_side"]),
    "n_fail_overlap_excluding_float_ties": sum(1 for r in fail if not r["float_tie"]),
    "fail_rows": [f"{r['adapter']} | {r['metric']} | k={r['k_original']}v{r['k_harbor']} | separation {r['separation']:.4g}{' (floating-point tie)' if r['float_tie'] else ''} | orig {r['original_runs']} | harbor {r['harbor_runs']}" for r in fail],
    "fail_row_keys": [[r["adapter"], r["metric"]] for r in fail],
    "adapters_with_a_failing_row": sorted({r["adapter"] for r in fail}),
    "n_identical_lists": sum(1 for r in paired if r["identical_lists"]),
    "n_zero_spread_both": sum(1 for r in paired if r["zero_spread_both"]),
    "n_single_run_side": sum(1 for r in paired if r["single_run_side"]),
}
with open(os.path.join(out, "overlap.json"), "w") as fh:
    json.dump(res, fh, indent=1)
cols = ["adapter", "exp", "metric_index", "agent", "model", "metric", "status", "k_original", "k_harbor",
        "mean_original", "mean_harbor", "gap", "separation", "float_tie", "identical_lists", "zero_spread_both", "single_run_side",
        "original_runs", "harbor_runs"]
with open(os.path.join(out, "overlap_rows.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)

print(f"metric rows {res['n_metric_rows']} | paired (numeric lists both sides) {res['n_paired']} | no paired runs {res['n_no_paired_runs']} | with lists on both sides counting string-valued lists {res['n_rows_with_lists_both_sides_incl_strings']}")
print(f"fail range-overlap: {res['n_fail_overlap']} (3v3: {res['n_fail_overlap_3v3']}, single-run side: {res['n_fail_overlap_single_run_side']}); excluding floating-point ties: {res['n_fail_overlap_excluding_float_ties']}")
print(f"identical run lists: {res['n_identical_lists']} | zero spread both sides: {res['n_zero_spread_both']} | single-run side: {res['n_single_run_side']}")
for s in res["fail_rows"]:
    print("   FAIL:", s)
