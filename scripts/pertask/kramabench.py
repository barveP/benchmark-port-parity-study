"""Per-task outcomes for the KramaBench Harbor parity experiment (stdlib only).

Usage:  python -I kramabench.py <download_dir> <out_dir>

<download_dir> mirrors adapters/kramabench/ of the Hugging Face dataset
harborframework/parity-experiments (only results_collection/ is needed).
Experiment: OpenHands@1.1.0 + claude-sonnet-4-5, 3 runs x 104 tasks, metric
"Mean Reward" with FRACTIONAL rewards in [0, 1] (KramaBench per-task score:
0/1 accuracy, 1/(1+RAE) for approximate numerics, F1 for lists).

Both sides are Harbor job-level result.json files, one per run:
    results_collection/result_harbor_trial<N>.json
    results_collection/result_original_trial<N>.json
(the original KramaBench runs were converted upstream with the parity fork's
convert_to_harbor_results.py; see the adapter's README on Hugging Face).
Per-task rewards live in
    stats.evals[<eval name>].reward_stats.reward = {"<reward>": [trial names]}

Trial names: the original side uses the bare task name
("kramabench-wildfire-hard-6"); the Harbor side appends a 7-character trial
suffix ("kramabench-wildfire-hard-6__ySjj9CA"), which is stripped (regex
"__[A-Za-z0-9]+$"), so task_id = "kramabench-<domain>-<easy|hard>-<n>" on
both sides and the files join on task_id.  run = N from the file name.

Exceptions: trials listed under stats.evals[..].exception_stats that also
have a reward entry (AgentTimeoutError) keep that reward.  One Harbor trial
(run 2, kramabench-archeology-easy-6, AgentSetupTimeoutError) has no reward
entry; it is written with reward 0.0, which is how the published run mean
(metrics[0].mean = sum of rewards / n_total_trials = 104) counts it.
Output: <out_dir>/original.csv and <out_dir>/harbor.csv (run,task_id,reward).
"""
import csv
import json
import os
import re
import sys

TRIAL_SUFFIX = re.compile(r"__[A-Za-z0-9]+$")


def rows_from_result(path, run):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    rows, scored = [], set()
    for ev in data["stats"]["evals"].values():
        for reward, names in ev["reward_stats"]["reward"].items():
            for name in names:
                rows.append((run, TRIAL_SUFFIX.sub("", name), float(reward)))
                scored.add(name)
        for exc, names in ev.get("exception_stats", {}).items():
            for name in names:
                if name not in scored:
                    print(f"  note: {name} ({exc}) has no reward entry; "
                          f"written as 0.0")
                    rows.append((run, TRIAL_SUFFIX.sub("", name), 0.0))
        published = ev["metrics"][0]["mean"]
    assert len(rows) == data["n_total_trials"], (path, len(rows))
    assert all(0.0 <= r <= 1.0 for _, _, r in rows), path
    mean = sum(r for _, _, r in rows) / len(rows)
    assert abs(mean - published) < 1e-9, (path, mean, published)
    return rows


def write_csv(path, rows):
    keys = [(r, t) for r, t, _ in rows]
    assert len(keys) == len(set(keys)), "duplicate (run, task_id)"
    rows.sort()
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["run", "task_id", "reward"])
        w.writerows(rows)


def main(download_dir, out_dir):
    rc = os.path.join(download_dir, "results_collection")
    os.makedirs(out_dir, exist_ok=True)
    sides = {"original": [], "harbor": []}
    for fn in sorted(os.listdir(rc)):
        m = re.fullmatch(r"result_(original|harbor)_trial(\d+)\.json", fn)
        if not m:
            continue
        side, run = m.group(1), int(m.group(2))
        rows = rows_from_result(os.path.join(rc, fn), run)
        vals = [x for _, _, x in rows]
        print(f"{side} run {run}: n_tasks={len(vals)} "
              f"mean={sum(vals) / len(vals):.6f}")
        sides[side] += rows
    tasks = {s: {t for _, t, _ in rows} for s, rows in sides.items()}
    assert tasks["original"] == tasks["harbor"], "task ids differ across sides"
    print(f"tasks in common: {len(tasks['original'])}")
    for side, rows in sides.items():
        if rows:
            write_csv(os.path.join(out_dir, f"{side}.csv"), rows)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
