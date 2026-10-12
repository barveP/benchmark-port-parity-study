"""Per-task outcomes for the ds1000 parity experiment (codex@0.77.0, gpt-5.1-codex).

Usage: python -I ds1000.py <download_dir> <out_dir>

Original side (written to <out_dir>/original.csv):
  <download_dir>/original_parity/gpt-5.1-codex-round<k>-results.jsonl, one JSONL file per run,
  1000 records each with fields task_idx (int, the DS-1000 problem index 0..999), correct (bool),
  status, library, perturbation_type, output, gold_label, pred_label.  reward = 1.0 if correct
  else 0.0; task_id = str(task_idx); run = <k> from the file name.

Harbor side (written to <out_dir>/harbor.csv):
  <download_dir>/results_collection/result_harbor_trial<k>.json, one job-level Harbor result.json
  per run.  Rewards live in stats.evals[<eval name>].reward_stats.reward = {"<reward>": [trial
  names...]}.  Trial names look like "698__Pu9Nxzm"; the "__<suffix>" trial id is stripped and the
  task_id recorded is the Harbor task name "698", which is the same DS-1000 problem index used on
  the original side.  Run numbers come from the "trial<k>" token in the file name.  The oracle
  file is ignored.
"""
import csv
import json
import os
import re
import sys


def original_rows(download_dir):
    od = os.path.join(download_dir, "original_parity")
    rows = []
    for fn in sorted(os.listdir(od)):
        m = re.match(r"gpt-5\.1-codex-round(\d+)-results\.jsonl$", fn)
        if not m:
            continue
        run = int(m.group(1))
        with open(os.path.join(od, fn), encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                rows.append((run, str(rec["task_idx"]), 1.0 if rec["correct"] else 0.0))
    return rows


def harbor_rows(download_dir):
    rc = os.path.join(download_dir, "results_collection")
    rows = []
    for fn in sorted(os.listdir(rc)):
        m = re.match(r"result_harbor_trial(\d+)\.json$", fn)
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


def write(rows, path):
    rows.sort(key=lambda r: (r[0], int(r[1])))
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["run", "task_id", "reward"])
        w.writerows(rows)
    for run in sorted({r[0] for r in rows}):
        rr = [r[2] for r in rows if r[0] == run]
        print(f"{os.path.basename(path)} run {run}: n_tasks={len(rr)} mean={sum(rr)/len(rr):.4f}")


def main(download_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    write(original_rows(download_dir), os.path.join(out_dir, "original.csv"))
    write(harbor_rows(download_dir), os.path.join(out_dir, "harbor.csv"))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
