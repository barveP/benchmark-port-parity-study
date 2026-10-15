"""Per-task parity outcomes for the autocodebench adapter (HF harborframework/parity-experiments).

Usage: python -I autocodebench.py <download_dir> <out_dir>
  <download_dir> is the local mirror of adapters/autocodebench/; writes original.csv and harbor.csv
  (columns run,task_id,reward) into <out_dir>.

Original side ("TB adapter", Terminal-Bench run of the adapter):
  results_collection/result_original_trial{1,2,3}.json, one file per run (run = the trial number in
  the file name). Each file is a Terminal-Bench results.json: {"results": [{"task_id": "php_006",
  "is_resolved": bool, ...}, ...], "resolved_ids": [...], "unresolved_ids": [...], "accuracy": ...}.
  task_id is taken verbatim; reward = 1.0 if is_resolved else 0.0.

Harbor side: one Harbor job (harbor_parity/<job>/) with n_attempts=3, so all 600 trials are pooled in
  the job-level result.json (stats.evals[...].reward_stats.reward = {"1.0": [ids], "0.0": [ids]}) and
  the attempt index is not recorded there. The script therefore reads the per-trial files
  harbor_parity/<job>/<task>__<suffix>/result.json ({"task_name", "trial_name", "started_at",
  "verifier_result": {"rewards": {"reward": x}}, "exception_info"}), groups them by task_name, sorts
  each task's trials by started_at and calls them run 1, 2, 3 (the adapter's README defines "Trial k"
  as the k-th attempt of every task). task_id = task_name, i.e. the trial name with the "__<suffix>"
  stripped.
  The per-trial rewards are cross-checked against the pooled job-level lists; a trial without a
  verifier reward gets 0.0 and is reported.
"""
import csv
import glob
import json
import os
import sys


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def original_rows(ddir):
    files = sorted(glob.glob(os.path.join(ddir, "results_collection", "result_original_trial*.json")),
                   key=lambda p: int(p.rsplit("trial", 1)[1].split(".")[0]))
    rows = []
    for path in files:
        run = int(path.rsplit("trial", 1)[1].split(".")[0])
        data = read_json(path)
        for r in data["results"]:
            rows.append((run, r["task_id"], 1.0 if r["is_resolved"] else 0.0))
        n_ok = sum(1 for r in data["results"] if r["is_resolved"])
        print(f"original run {run}: {len(data['results'])} tasks, {n_ok} resolved "
              f"(file accuracy={data.get('accuracy')}, n_resolved={data.get('n_resolved')})")
    return rows


def harbor_rows(ddir):
    trial_files = sorted(glob.glob(os.path.join(ddir, "harbor_parity", "*", "*", "result.json")))
    if not trial_files:
        sys.exit("no per-trial harbor_parity/<job>/<trial>/result.json files; the pooled job-level "
                 "result.json does not record the attempt index, so runs cannot be assigned")
    by_task = {}
    missing = []
    for path in trial_files:
        t = read_json(path)
        reward = (t.get("verifier_result") or {}).get("rewards", {}).get("reward")
        if reward is None:
            missing.append(t["trial_name"])
            reward = 0.0
        by_task.setdefault(t["task_name"], []).append((t["started_at"], t["trial_name"], float(reward)))
    rows = []
    for task, trials in sorted(by_task.items()):
        trials.sort()
        for run, (_, _, reward) in enumerate(trials, start=1):
            rows.append((run, task, reward))
    n_att = sorted({len(v) for v in by_task.values()})
    print(f"harbor: {len(trial_files)} trials, {len(by_task)} tasks, attempts per task {n_att}, "
          f"{len(missing)} trials without a verifier reward {missing[:5]}")
    # cross-check against the pooled job-level reward lists (ids carry a __suffix; strip it)
    job_files = glob.glob(os.path.join(ddir, "harbor_parity", "*", "result.json")) or \
        glob.glob(os.path.join(ddir, "results_collection", "result_harbor.json"))
    if job_files:
        pooled = {}
        for ev in read_json(job_files[0])["stats"]["evals"].values():
            for val, ids in ev["reward_stats"]["reward"].items():
                for i in ids:
                    pooled[i] = float(val)
        mine = {name: r for trials in by_task.values() for _, name, r in trials}
        bad = [k for k in mine if pooled.get(k) != mine[k]]
        print(f"harbor cross-check vs pooled job result: {len(mine)} trials, {len(bad)} disagree {bad[:5]}")
    return rows


def write_csv(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["run", "task_id", "reward"])
        w.writerows(rows)
    print(f"wrote {path}: {len(rows)} rows")


def main():
    ddir, odir = sys.argv[1], sys.argv[2]
    os.makedirs(odir, exist_ok=True)
    write_csv(os.path.join(odir, "original.csv"), original_rows(ddir))
    write_csv(os.path.join(odir, "harbor.csv"), harbor_rows(ddir))


if __name__ == "__main__":
    main()
