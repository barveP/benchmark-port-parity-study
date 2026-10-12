"""Per-task outcomes for the usaco parity experiment (claude-code@v2.0.34, claude-haiku-4-5-20251001,
304 USACO problems, 3 runs per side).  Only the HARBOR side has per-task data.

Usage: python -I usaco.py <download_dir> <out_dir>

<download_dir> mirrors adapters/usaco/ of the Hugging Face dataset harborframework/parity-experiments.
Writes <out_dir>/harbor.csv (columns run,task_id,reward; binary reward).  original.csv is NOT written:
the original side has no per-task outcomes in the public files (see below).

Harbor side -- results_collection/result_harbor_trial<k>.json (k = 1,2,3 = run) is the Harbor job-level
  result.  Rewards live in stats.evals[<eval name>].reward_stats.reward = {"<reward>": [trial names]}.
  Trial names look like "1069__HN7Kdkw" (USACO problem id + "__" + random trial suffix); the "__<suffix>"
  is stripped, so task_id is the numeric USACO problem id as a string ("1069").  A trial that appears only
  under exception_stats (run 2: one RewardFileNotFoundError, task 1327) gets reward 0.0; this reproduces
  the file's own metrics mean = (# reward 1.0) / 304.  Run 2's four AgentTimeoutError trials are also listed
  under reward 0.0, so the reward entry is used for them.

Original side -- results_collection/result_original_trial<k>.json holds only the aggregate
  stats.evals[...].metrics[0].mean (0.395 / 0.405 / 0.410) with no task list.  original_parity/trial{1,2}/
  contains one directory per task id, each holding only 0.py (the model's generated solution source), plus
  args.txt; no judge output, so per-task pass/fail is not recoverable from the published files.  The script
  reports this and skips original.csv.
"""
import csv
import json
import os
import re
import sys


def task_id_from_trial_name(tname):
    return tname.split("__", 1)[0]  # strip the per-trial "__<suffix>"


def harbor_rows(download_dir):
    rc = os.path.join(download_dir, "results_collection")
    rows = []
    for fn in sorted(os.listdir(rc)):
        m = re.match(r"result_harbor_trial(\d+)\.json$", fn)
        if not m:
            continue
        run = int(m.group(1))
        with open(os.path.join(rc, fn), encoding="utf-8") as fh:
            data = json.load(fh)
        for name, ev in data["stats"]["evals"].items():
            print(f"harbor run {run}: eval={name} n_trials={ev['n_trials']} n_errors={ev['n_errors']} "
                  f"file_mean={ev['metrics'][0].get('mean')}")
            seen = set()
            for reward, names in ev["reward_stats"]["reward"].items():
                for tname in names:
                    rows.append((run, task_id_from_trial_name(tname), float(reward)))
                    seen.add(tname)
            for exc, names in ev.get("exception_stats", {}).items():
                for tname in names:
                    if tname not in seen:
                        print(f"harbor run {run}: {tname} only in exception_stats ({exc}) -> reward 0.0")
                        rows.append((run, task_id_from_trial_name(tname), 0.0))
                        seen.add(tname)
    return rows


def check_original(download_dir):
    """The original side only ships aggregate means; say so instead of writing original.csv."""
    rc = os.path.join(download_dir, "results_collection")
    for fn in sorted(os.listdir(rc)):
        m = re.match(r"result_original_trial(\d+)\.json$", fn)
        if not m:
            continue
        with open(os.path.join(rc, fn), encoding="utf-8") as fh:
            data = json.load(fh)
        for name, ev in data["stats"]["evals"].items():
            has_tasks = bool(ev.get("reward_stats", {}).get("reward"))
            print(f"original run {m.group(1)}: eval={name} n_trials={ev['n_trials']} "
                  f"file_mean={ev['metrics'][0].get('mean')} per_task_data={has_tasks}")
    print("original side: aggregate means only; original_parity/trial*/<id>/0.py are solution sources, "
          "not judgments -> original.csv not written")


def write(rows, path):
    rows.sort(key=lambda r: (r[0], r[1]))
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["run", "task_id", "reward"])
        w.writerows(rows)
    for run in sorted({r[0] for r in rows}):
        rr = [r[2] for r in rows if r[0] == run]
        ids = [r[1] for r in rows if r[0] == run]
        print(f"{os.path.basename(path)} run {run}: n_tasks={len(rr)} unique_ids={len(set(ids))} "
              f"mean={sum(rr) / len(rr):.4f}")


def main(download_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    check_original(download_dir)
    write(harbor_rows(download_dir), os.path.join(out_dir, "harbor.csv"))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
