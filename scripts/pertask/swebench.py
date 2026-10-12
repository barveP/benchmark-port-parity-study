"""Per-task outcomes for the SWE-bench Verified parity experiment (HF adapter
folder ``adapters/swebench``, snapshot adapter ``swebench``):
mini-swe-agent@2.1.0 + openai/gpt-5-mini, SWE-bench leaderboard (Docent
export, 1 run x 500 tasks) vs Harbor on Daytona (3 runs x 499 tasks),
binary reward (1 = resolved).  This is the fifth experiment in
data/raw/harbor_parity/swebench.json; the four older terminal-bench
experiments in that file have no files in the HF folder.

Usage: python -I swebench.py <download_dir> <out_dir>

<download_dir> mirrors adapters/swebench/ of the Hugging Face dataset
harborframework/parity-experiments; only results_collection/ is read.
Writes <out_dir>/original.csv and <out_dir>/harbor.csv (run,task_id,reward).

Original side -- results_collection/result_original_trial1.json is a
normalised leaderboard summary: "task_results" is a list of 500 dicts
{agent_run_id, instance_id, mini_version, resolved (0/1), exit_status,
cost}.  task_id = instance_id verbatim (e.g. "django__django-11532");
reward = float(resolved).  All 500 tasks are written, run = 1.

Harbor side -- results_collection/result_harbor_trial<N>.json (N = 1..3)
is a Harbor job-level result.json; stats.evals[<name>].reward_stats.reward
= {"1.0": [trial names], "0.0": [trial names]}.  Trial names look like
"sympy__sympy-22914__Pb7RUAd": the trailing "__<7 chars>" trial suffix is
stripped, leaving the SWE-bench instance id, so both CSVs join on task_id.
Each run scores 499 tasks: "scikit-learn__scikit-learn-14710" never got a
reward (CancelledError in runs 1-2, VerifierTimeoutError in run 3; it is
listed under exception_stats only) and is omitted, as in the published
499-task comparison.  Tasks listed under AgentTimeoutError still carry a
reward in the reward dict and are kept with that reward.
"""
import csv
import json
import os
import re
import sys

RUNS = (1, 2, 3)
TRIAL_SUFFIX = re.compile(r"__[A-Za-z0-9]+$")


def read_original(path):
    """[(task_id, reward)] from the normalised leaderboard summary."""
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    rows = [(r["instance_id"], float(r["resolved"])) for r in d["task_results"]]
    ids = [t for t, _ in rows]
    assert len(ids) == len(set(ids)) == d["found_count"], path
    assert all(r in (0.0, 1.0) for _, r in rows), path
    return rows


def read_harbor(path):
    """[(task_id, reward)] from a Harbor job-level result.json."""
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    rewards = {}
    for ev in d["stats"]["evals"].values():
        for reward, names in ev["reward_stats"]["reward"].items():
            for name in names:
                task = TRIAL_SUFFIX.sub("", name)
                assert task not in rewards, f"duplicate task {task} in {path}"
                rewards[task] = float(reward)
        assert len(rewards) == ev["n_trials"], path
    return sorted(rewards.items())


def main(download_dir, out_dir):
    rc = os.path.join(download_dir, "results_collection")
    original = [(1, t, r) for t, r in
                read_original(os.path.join(rc, "result_original_trial1.json"))]
    harbor = [(run, t, r) for run in RUNS for t, r in
              read_harbor(os.path.join(rc, f"result_harbor_trial{run}.json"))]
    orig_ids = {t for _, t, _ in original}
    for run in RUNS:
        ids = {t for r, t, _ in harbor if r == run}
        assert ids <= orig_ids, (run, ids - orig_ids)
        print(f"harbor run {run}: {len(ids)} tasks; missing vs original: "
              f"{sorted(orig_ids - ids)}")
    os.makedirs(out_dir, exist_ok=True)
    for fname, rows in (("original.csv", original), ("harbor.csv", harbor)):
        with open(os.path.join(out_dir, fname), "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["run", "task_id", "reward"])
            w.writerows(sorted(rows))
        print(f"{fname}: {len(rows)} rows")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
