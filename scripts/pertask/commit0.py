#!/usr/bin/env python3
"""Per-task outcomes for the commit0 parity experiment (aider, openai/gpt-5-mini, lite split).

Usage: python -I commit0.py <download_dir> <out_dir>

<download_dir> is the local copy of adapters/commit0/ from the Hugging Face dataset
harborframework/parity-experiments (only results_collection/ is needed). Writes
<out_dir>/harbor.csv with columns run,task_id,reward. No original.csv is written:
original_parity/<trial>/<repo>/<module>/ holds only aider.log and .aider.chat.history.md
(agent transcripts, run_tests: false) and no evaluation output, so the original side has
no recoverable per-task rewards.

Harbor format: results_collection/result_harbor_trial<N>.json is a Harbor job-level
result.json:
  stats.evals[<eval name>].reward_stats.reward = { "<reward>": [trial ids...] }
  stats.evals[<eval name>].exception_stats     = { "<ErrorType>": [trial ids...] }
  stats.evals[<eval name>].metrics[0].mean     = sum(rewards) / n_total_trials
Rewards are fractional pass rates in [0, 1]. Trials that errored (RewardFileNotFoundError,
VerifierTimeoutError, AgentTimeoutError without a reward) appear only in exception_stats;
they are recorded with reward 0, which is how the job-level mean counts them (the sum of
listed rewards divided by n_total_trials reproduces metrics[0].mean exactly).
result_oracle_trial.json (oracle run) is ignored.

Task ids: Harbor trial ids look like "commit0__babel__MRZHphT"; the trailing "__<7 chars>"
trial suffix is stripped, leaving the task name "commit0__babel". run = N from the file name.
"""
import csv
import json
import os
import re
import sys

NAME_RE = re.compile(r"^result_harbor_trial(\d+)\.json$")
SUFFIX_RE = re.compile(r"^(.*)__[A-Za-z0-9]{7}$")


def task_id(trial_id):
    m = SUFFIX_RE.match(trial_id)
    if not m:
        sys.exit(f"trial id without a __suffix: {trial_id!r}")
    return m.group(1)


def parse_file(path):
    """Return {task_id: reward} for one Harbor job result.json, errored trials as 0."""
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    evals = data["stats"]["evals"]
    if len(evals) != 1:
        sys.exit(f"expected one eval in {path}, found {list(evals)}")
    ev = next(iter(evals.values()))
    rewards = {}
    for value, ids in ev["reward_stats"]["reward"].items():
        r = float(value)
        if not 0.0 <= r <= 1.0:
            sys.exit(f"reward {r} outside [0,1] in {path}")
        for tid in ids:
            t = task_id(tid)
            if t in rewards:
                sys.exit(f"duplicate task {t!r} in {path}")
            rewards[t] = r
    for ids in ev.get("exception_stats", {}).values():
        for tid in ids:
            rewards.setdefault(task_id(tid), 0.0)
    n_total = data["n_total_trials"]
    if len(rewards) != n_total:
        sys.exit(f"{path}: {len(rewards)} tasks recovered but n_total_trials={n_total}")
    mean = sum(rewards.values()) / n_total
    published = ev["metrics"][0]["mean"]
    if abs(mean - published) > 1e-9:
        sys.exit(f"{path}: recomputed mean {mean} != metrics mean {published}")
    return rewards, mean


def main(download_dir, out_dir):
    rc = os.path.join(download_dir, "results_collection")
    if not os.path.isdir(rc):
        rc = download_dir
    runs = []
    for name in sorted(os.listdir(rc)):
        m = NAME_RE.match(name)
        if m:
            runs.append((int(m.group(1)), os.path.join(rc, name)))
    if not runs:
        sys.exit(f"no result_harbor_trial<N>.json under {rc}")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "harbor.csv")
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["run", "task_id", "reward"])
        for run, path in runs:
            rewards, mean = parse_file(path)
            for t in sorted(rewards):
                w.writerow([run, t, repr(rewards[t])])
            print(f"harbor run {run}: {len(rewards)} tasks, mean reward {mean:.6f} ({path})")
    print(f"wrote {out}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
