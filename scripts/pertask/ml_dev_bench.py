"""Per-task outcomes for the ml_dev_bench Harbor parity experiment (stdlib only).

Usage:  python -I ml_dev_bench.py <download_dir> <out_dir>

<download_dir> mirrors adapters/ml_dev_bench/ of the Hugging Face dataset
harborframework/parity-experiments.  Experiment: openhands@1.4.0 + gpt-5-mini,
3 runs x 33 tasks, metric "task success rate (%)", BINARY rewards (0/1).

Both sides are Harbor job-level result.json files, one per run:
    results_collection/result_original_trial_<N>.json  (converted upstream from
        the original harness's per-task eval_result*.json files)
    results_collection/result_harbor_trial_<N>.json
with per-task rewards in
    stats.evals[<eval>].reward_stats.reward = {"<reward>": [trial names]}.
A trial listed under exception_stats with no reward entry (one RuntimeError
trial in each of Harbor runs 2 and 3) is written as reward 0.0, which is how
the published run mean (metrics[0].mean = sum of rewards / n_total_trials)
counts it.

Task ids.  The original side lists the bare benchmark task name
("channel_vit_implementation_easy").  Harbor trial names are
"ml_dev_bench_" + task name, TRUNCATED to 32 characters, plus a 7-character
trial suffix ("ml_dev_bench_channel_vit_impleme__Ex6igtf").  The suffix is
stripped (regex "__[A-Za-z0-9]+$") and the stem is mapped back to the full
task name: directly when exactly one task name matches the stem, otherwise
(stems channel_vit_impleme = 3 tasks, full_train_workflow = 2 tasks) via the
per-task file harbor_parity/ml_dev_bench_openhands_parity_r<N>/<trial>/
result.json, whose "task_name" field holds the full name.  The
"ml_dev_bench_" prefix is then dropped, so task_id = bare benchmark task
name on both sides and the files join on task_id.  run = N from the file
name.  (One Harbor run-1 folder, mla_implementation_hidden_tests__VJ2hA8b,
was renamed to the untruncated name on upload; the trial_name inside its
result.json is still the truncated one, so only the trial suffix is matched.)
Every (run, task) cell on both sides is also cross-checked against
results_collection/task_level_comparison.csv (True/False per run).
Output: <out_dir>/original.csv and <out_dir>/harbor.csv (run,task_id,reward).
"""
import csv
import json
import os
import re
import sys

PREFIX = "ml_dev_bench_"
TRIAL_SUFFIX = re.compile(r"__[A-Za-z0-9]+$")
HARBOR_RUN_DIR = "harbor_parity/ml_dev_bench_openhands_parity_r{run}"


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def trial_rewards(path):
    """{trial name: reward} from one job-level result.json; no entry -> 0.0."""
    data = load(path)
    (ev,) = data["stats"]["evals"].values()
    rewards = {}
    for reward, names in ev["reward_stats"]["reward"].items():
        for name in names:
            assert name not in rewards, (path, name)
            rewards[name] = float(reward)
    for exc, names in ev.get("exception_stats", {}).items():
        for name in names:
            if name not in rewards:
                print(f"  note: {name} ({exc}) has no reward entry; "
                      f"written as 0.0")
                rewards[name] = 0.0
    assert len(rewards) == data["n_total_trials"], (path, len(rewards))
    assert set(rewards.values()) <= {0.0, 1.0}, path
    mean = sum(rewards.values()) / len(rewards)
    assert abs(mean - ev["metrics"][0]["mean"]) < 1e-9, (path, mean)
    return rewards


def harbor_task(download_dir, run, trial, reward, tasks):
    """Map a (truncated) Harbor trial name back to the bare task name."""
    stem = TRIAL_SUFFIX.sub("", trial)
    per_task = os.path.join(download_dir, HARBOR_RUN_DIR.format(run=run),
                            trial, "result.json")
    if os.path.exists(per_task):
        d = load(per_task)
        assert d["trial_name"].endswith(trial[len(stem):]), (per_task, trial)
        assert d["task_name"].startswith(stem), (per_task, stem)
        r = ((d.get("verifier_result") or {}).get("rewards") or {}).get("reward")
        assert (0.0 if r is None else float(r)) == reward, (per_task, r, reward)
        return d["task_name"][len(PREFIX):]
    cands = [t for t in tasks if (PREFIX + t)[:32] == stem or PREFIX + t == stem]
    assert len(cands) == 1, (trial, cands)
    return cands[0]


def write_csv(path, rows):
    rows.sort()
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["run", "task_id", "reward"])
        w.writerows(rows)


def main(download_dir, out_dir):
    rc = os.path.join(download_dir, "results_collection")
    os.makedirs(out_dir, exist_ok=True)
    runs = {"original": {}, "harbor": {}}
    for fn in sorted(os.listdir(rc)):
        m = re.fullmatch(r"result_(original|harbor)_trial_(\d+)\.json", fn)
        if m:
            runs[m.group(1)][int(m.group(2))] = trial_rewards(os.path.join(rc, fn))
    tasks = sorted(next(iter(runs["original"].values())))
    assert all(set(r) == set(tasks) for r in runs["original"].values())

    rows = {"original": [], "harbor": []}
    for run, rw in sorted(runs["original"].items()):
        rows["original"] += [(run, t, x) for t, x in rw.items()]
    for run, rw in sorted(runs["harbor"].items()):
        rows["harbor"] += [(run, harbor_task(download_dir, run, tr, x, tasks), x)
                           for tr, x in rw.items()]

    with open(os.path.join(rc, "task_level_comparison.csv"), newline="") as fh:
        comp = {r["task"]: r for r in csv.DictReader(fh)}
    assert set(comp) == set(tasks), "comparison csv task set differs"
    for side, rs in rows.items():
        for run, t, x in rs:
            assert comp[t][f"{side}_trial_{run}_success"] == str(bool(x)), (side, run, t)
        keys = [(r, t) for r, t, _ in rs]
        assert len(keys) == len(set(keys)), f"duplicate (run, task_id) on {side}"
        assert {t for _, t in keys} == set(tasks), f"task set differs on {side}"
        for run in sorted(runs[side]):
            vals = [x for r, _, x in rs if r == run]
            print(f"{side} run {run}: n_tasks={len(vals)} "
                  f"mean={sum(vals) / len(vals):.6f}")
        write_csv(os.path.join(out_dir, f"{side}.csv"), rs)
    print(f"tasks in common: {len(tasks)}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
