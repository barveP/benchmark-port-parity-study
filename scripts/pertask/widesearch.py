"""Per-task outcomes for the WideSearch parity experiment (stdlib only).

Usage:  python -I widesearch.py <download_dir> <out_dir>

<download_dir> mirrors adapters/widesearch/ of the Hugging Face dataset
harborframework/parity-experiments; only results_collection/ is read.
Experiment: claude-code@2.1.98 with claude-haiku-4-5-20251001, 3 runs a side,
200 tasks (100 ws-en + 100 ws-zh).  Published metric: Mean Item F1.

Both sides use the same flat format, results_collection/result_<side>_run<N>.json:
    {"widesearch-ws-en-001": {"score", "precision_by_row", "recall_by_row",
                              "f1_by_row", "precision_by_item", "recall_by_item",
                              "f1_by_item", ["msg"]}, ...}
The Harbor files are NOT the usual Harbor job-level result.json; they are
already keyed by task name, so no trial suffix needs stripping.  task_id is the
dict key exactly as written (the Harbor task name, e.g. "widesearch-ws-zh-069",
= "widesearch-" + the original WideSearch query id).  reward = f1_by_item, a
fraction in [0, 1] (the "score" field is a binary whole-table exact match and
is not the published metric).  Harbor-side tasks whose agent errored
("msg": "AgentSetupTimeout or error") carry only f1_by_item = 0 and are kept as
reward 0, which is how the published run means were computed.  run = N from
the file name.  Output: original.csv and harbor.csv.
"""
import csv
import json
import os
import re
import sys


def rows_from(path, run, label):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    rows = []
    for task_id, rec in data.items():
        reward = float(rec["f1_by_item"])
        assert 0.0 <= reward <= 1.0, (label, run, task_id, reward)
        if "score" not in rec:
            print(f"{label} run {run}: {task_id} has no metrics, "
                  f"msg={rec.get('msg')!r}, kept with reward {reward}")
        rows.append((run, task_id, reward))
    return rows


def write_csv(rows, path, label):
    keys = [(r, t) for r, t, _ in rows]
    assert len(keys) == len(set(keys)), f"duplicate (run, task_id) on {label} side"
    rows.sort(key=lambda r: (r[0], r[1]))
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["run", "task_id", "reward"])
        w.writerows(rows)
    for run in sorted({r for r, _, _ in rows}):
        vals = [x for rr, _, x in rows if rr == run]
        print(f"{label} run {run}: n_tasks={len(vals)} mean={sum(vals) / len(vals):.4f}")


def main(download_dir, out_dir):
    rc = os.path.join(download_dir, "results_collection")
    os.makedirs(out_dir, exist_ok=True)
    sides = {"harbor": [], "original": []}
    for fn in sorted(os.listdir(rc)):
        m = re.fullmatch(r"result_(harbor|original)_run(\d+)\.json", fn)
        if m:
            side, run = m.group(1), int(m.group(2))
            sides[side] += rows_from(os.path.join(rc, fn), run, side)
    for side, rows in sides.items():
        if rows:
            write_csv(rows, os.path.join(out_dir, f"{side}.csv"), side)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
