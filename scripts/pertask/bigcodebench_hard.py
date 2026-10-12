"""Per-task outcomes for the bigcodebench_hard parity experiment (codex, gpt-5-mini).

Usage: python -I bigcodebench_hard.py <download_dir> <out_dir>

Harbor side (written to <out_dir>/harbor.csv):
  <download_dir>/results_collection/result_harbor_trial<k>_<timestamp>.json, one job-level
  Harbor result.json per run.  Rewards live in
  stats.evals[<eval name>].reward_stats.reward = {"<reward>": [trial names...]}.
  Trial names look like "bigcodebench_17__ofVf932"; the "__<suffix>" trial id is stripped and
  the task_id recorded is the Harbor task name, e.g. "bigcodebench_17".  Run numbers come from
  the "trial<k>" token in the file name.  The oracle file is ignored.

Original side: <download_dir>/original_parity/ contains only a BigCodeBench solutions JSONL
  (task_id, solution, raw_solution) with no pass/fail information, so no original.csv is written.
"""
import csv
import json
import os
import re
import sys


def harbor_rows(download_dir):
    rc = os.path.join(download_dir, "results_collection")
    rows = []
    for fn in sorted(os.listdir(rc)):
        m = re.match(r"result_harbor_trial(\d+)_.*\.json$", fn)
        if not m:
            continue
        run = int(m.group(1))
        with open(os.path.join(rc, fn)) as fh:
            data = json.load(fh)
        for ev in data["stats"]["evals"].values():
            for reward, names in ev["reward_stats"]["reward"].items():
                for name in names:
                    rows.append((run, name.split("__", 1)[0], float(reward)))
    return rows


def main(download_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    rows = harbor_rows(download_dir)
    rows.sort(key=lambda r: (r[0], int(r[1].rsplit("_", 1)[-1])))
    with open(os.path.join(out_dir, "harbor.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["run", "task_id", "reward"])
        w.writerows(rows)
    runs = sorted({r[0] for r in rows})
    for run in runs:
        rr = [r[2] for r in rows if r[0] == run]
        print(f"harbor run {run}: n_tasks={len(rr)} mean={sum(rr)/len(rr):.4f}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
