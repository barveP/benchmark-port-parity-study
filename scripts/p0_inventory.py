#!/usr/bin/env python3
"""Phase 0, number set A: inventory of the parity snapshot.

Reproduces the first pass (scripts/first_pass/parity_summary.py) with the same definitions:
  * experiment = one JSON object; a file holding a single object counts as one
  * runs per side = field number_of_runs, else number_of_trials; null or absent -> "missing"
  * subset/full = parity_benchmark_size < adapted_benchmark_size, both numeric; else "unknown"
Usage: python -I scripts/p0_inventory.py <snapshot_dir> <out_dir>
"""
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parity_lib import is_num, iter_experiments, lenient_runs, snapshot_files  # noqa: E402

root, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)

n_exp = n_rows = rows_with_runs = 0
runs = collections.Counter()
actual_runs = collections.Counter()
declared_vs_actual = []
sizes = collections.Counter()
exp_keys = collections.Counter()
row_keys = collections.Counter()
runlist_keys = collections.Counter()
runlist_len = collections.Counter()
nonlist = []
nonnumeric = []
adapters = set()

for adapter, i, e in iter_experiments(root):
    n_exp += 1
    adapters.add(adapter)
    exp_keys.update(e.keys())
    nr = e.get("number_of_runs", e.get("number_of_trials"))
    if isinstance(nr, float) and nr.is_integer():
        nr = int(nr)
    runs[str(nr) if nr is not None else "missing"] += 1
    # actual run-list lengths (lenient parsing, first of <side>_runs / <side>_trials per row)
    actual = []
    for m in e.get("metrics") or []:
        ko = kh = None
        for suf in ("_runs", "_trials"):
            lo, lh = lenient_runs(m.get("original" + suf)), lenient_runs(m.get("harbor" + suf))
            ko = ko if ko is not None else (len(lo) if lo else None)
            kh = kh if kh is not None else (len(lh) if lh else None)
        if ko is not None and kh is not None:
            actual.append((ko, kh))
    if actual:
        amin = min(min(x) for x in actual)
        actual_runs[str(amin)] += 1
        if nr is None or any(x != (nr, nr) for x in actual):
            declared_vs_actual.append(f"{adapter}#{i}: declared {nr}, actual (original, harbor) per row {sorted(set(actual))}")
    else:
        actual_runs["no paired run lists"] += 1
    a, p = e.get("adapted_benchmark_size"), e.get("parity_benchmark_size")
    if is_num(a) and is_num(p):
        sizes["subset" if p < a else "full"] += 1
    else:
        sizes["unknown"] += 1
    for m in e.get("metrics") or []:
        n_rows += 1
        row_keys.update(m.keys())
        any_list = False
        for key, v in m.items():
            if not (key.endswith("_runs") or key.endswith("_trials")):
                continue
            if not isinstance(v, list):
                nonlist.append(f"{adapter}#{i} {m.get('metric')!r} {key}={v!r}")
                continue
            any_list = True
            runlist_keys[key] += 1
            runlist_len[len(v)] += 1
            if any(not is_num(x) for x in v):
                nonnumeric.append(f"{adapter}#{i} {m.get('metric')!r} {key}={v!r}")
        rows_with_runs += any_list

res = {
    "n_files": len(snapshot_files(root)),
    "n_adapters": len(adapters),
    "n_experiments": n_exp,
    "n_metric_rows": n_rows,
    "n_metric_rows_with_any_run_list": rows_with_runs,
    "runs_per_side_by_experiment": dict(sorted(runs.items(), key=lambda kv: -kv[1])),
    "actual_min_runs_per_side_by_experiment": dict(sorted(actual_runs.items(), key=lambda kv: -kv[1])),
    "declared_runs_differ_from_actual": declared_vs_actual,
    "parity_set": dict(sizes),
    "experiment_keys": dict(exp_keys.most_common()),
    "metric_row_keys": dict(row_keys.most_common()),
    "run_list_keys": dict(runlist_keys.most_common()),
    "run_list_lengths": {str(k): v for k, v in sorted(runlist_len.items())},
    "run_fields_not_lists": nonlist,
    "run_lists_with_non_numeric_entries": nonnumeric,
}
with open(os.path.join(out, "inventory.json"), "w") as fh:
    json.dump(res, fh, indent=1)

print(f"files {res['n_files']} | experiments {n_exp} | metric rows {n_rows} | rows with a run list {rows_with_runs}")
print("runs per side, by experiment (declared field):", res["runs_per_side_by_experiment"])
print("runs per side, by experiment (actual list lengths, min over rows/sides):", res["actual_min_runs_per_side_by_experiment"])
print(f"experiments whose declared runs differ from the lists: {len(declared_vs_actual)}")
for x in declared_vs_actual:
    print("   ", x)
print("parity set:", res["parity_set"])
print("run-list keys:", res["run_list_keys"])
print(f"run fields that are not lists: {len(nonlist)} | run lists with non-numeric entries: {len(nonnumeric)}")
for s in nonnumeric:
    print("   non-numeric:", s)
