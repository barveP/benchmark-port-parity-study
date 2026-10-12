"""Per-task outcomes for the BixBench parity experiment (BixbenchJupyterAgent, gpt-4o-mini,
50-task subset, 3 runs per side).

Usage: python -I bixbench.py <download_dir> <out_dir>

Original side (-> original.csv):
  <download_dir>/original_parity/eval_df.csv.gz, the BixBench postprocessing output
  (one CSV row per graded trajectory, 24 columns incl. notebooks and judge prompts).
  Columns used: problem_id (task id, e.g. "bix-60-q1"), replica (1..3 = run),
  correct ("true"/"false", the gpt-4o judge verdict) -> reward 1.0/0.0.
  The file has 147 rows; 3 (task, replica) pairs have no row at all (the agent produced
  no gradable answer).  They are written as reward 0.0 so every run has 50 tasks, which
  is how the published per-run scores (11/50, 7/50, 6/50) count them.

Harbor side (-> harbor.csv):
  <download_dir>/harbor_parity/2026-01-02__00-19-07/<trial>/result.json, one per trial
  (150 = 50 tasks x n_attempts 3).  task_id = result["task_name"], identical to the trial
  name with its random "__<suffix>" stripped.  reward = verifier_result.rewards.reward;
  trials with exception_info and no verifier result (11: RewardFileNotFoundError,
  NbcliError, APIError) are written as 0.0, as the adapter README and the published
  per-run scores (6/50, 10/50, 9/50) treat them.
  The job stores no attempt index, so run k = the k-th trial of each task ordered by
  started_at (same rule reproduces the published per-run scores).  The job-level
  results_collection/result_harbor.json is cross-checked against the per-trial rewards.

results_collection/result_harbor_cli.json (codex + gpt-5-mini, single run, no original
side) is a different experiment and is not written.
"""
import csv
import gzip
import json
import os
import re
import sys
from collections import defaultdict

HARBOR_JOB = "2026-01-02__00-19-07"
N_RUNS = 3


def task_key(tid):
    return tuple(int(x) for x in re.findall(r"\d+", tid))


def original_rows(download_dir):
    csv.field_size_limit(10**9)
    path = os.path.join(download_dir, "original_parity", "eval_df.csv.gz")
    got = {}
    with gzip.open(path, "rt", newline="") as fh:
        for row in csv.DictReader(fh):
            key = (int(row["replica"]), row["problem_id"])
            assert key not in got, f"duplicate row {key}"
            got[key] = 1.0 if row["correct"].strip().lower() == "true" else 0.0
    tasks = sorted({t for _, t in got}, key=task_key)
    rows = []
    for run in range(1, N_RUNS + 1):
        for t in tasks:
            if (run, t) not in got:
                print(f"original: no row for run {run} task {t}; written as 0.0")
            rows.append((run, t, got.get((run, t), 0.0)))
    return rows


def harbor_rows(download_dir):
    jobdir = os.path.join(download_dir, "harbor_parity", HARBOR_JOB)
    per_task = defaultdict(list)
    for trial in sorted(os.listdir(jobdir)):
        path = os.path.join(jobdir, trial, "result.json")
        if not os.path.isfile(path):
            continue
        with open(path) as fh:
            r = json.load(fh)
        assert r["trial_name"] == trial and trial.split("__", 1)[0] == r["task_name"]
        vr = r.get("verifier_result")
        if vr is None:
            exc = (r.get("exception_info") or {}).get("exception_type")
            print(f"harbor: {trial} has no verifier result ({exc}); written as 0.0")
            reward = 0.0
        else:
            reward = float(vr["rewards"]["reward"])
        per_task[r["task_name"]].append((r["started_at"], trial, reward))
    rows, by_trial = [], {}
    for task, trials in per_task.items():
        assert len(trials) == N_RUNS, (task, len(trials))
        for run, (_, trial, reward) in enumerate(sorted(trials), 1):
            rows.append((run, task, reward))
            by_trial[trial] = reward
    # cross-check against the job-level summary in results_collection
    with open(os.path.join(download_dir, "results_collection", "result_harbor.json")) as fh:
        job = json.load(fh)
    for ev in job["stats"]["evals"].values():
        for reward, names in ev["reward_stats"]["reward"].items():
            for name in names:
                assert by_trial[name] == float(reward), name
    return rows


def write(rows, path):
    rows.sort(key=lambda r: (r[0], task_key(r[1])))
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["run", "task_id", "reward"])
        w.writerows(rows)
    for run in sorted({r[0] for r in rows}):
        rr = [r[2] for r in rows if r[0] == run]
        print(f"{os.path.basename(path)} run {run}: n_tasks={len(rr)} mean={sum(rr) / len(rr):.4f}")


def main(download_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    write(original_rows(download_dir), os.path.join(out_dir, "original.csv"))
    write(harbor_rows(download_dir), os.path.join(out_dir, "harbor.csv"))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
