"""Per-task outcomes for the TheAgentCompany parity experiment (HF
adapters/theagentcompany, snapshot adapter ``theagentcompany``): agent
openhands@1.6.0, model openai/gpt-5-mini, 3 runs x 37 tasks per side (a
stratified sample of the 174-task benchmark), fractional reward in [0, 1]
("Partial Completion Score": checkpoint-based, e.g. 0.2, 0.3333, 0.5, 1.0).

Usage: python -I theagentcompany.py <download_dir> <out_dir>

<download_dir> mirrors adapters/theagentcompany/ of the Hugging Face dataset
harborframework/parity-experiments; only results_collection/ is read.  Stdlib
only; nothing in <download_dir> is executed.  Writes <out_dir>/original.csv and <out_dir>/harbor.csv (columns
run,task_id,reward).

Format (both sides, one file per run):
results_collection/result_<side>_trial<N>.json is a small JSON object
{"side": ..., "trial_num": N, "num_tasks": 37, "mean_reward": ...,
 "per_task_rewards": {"<task id>": <float>, ...}, ...}.
run = N (the trial_num field, asserted equal to the file name's N).

Task ids are the keys of per_task_rewards, i.e. the benchmark's own task
names ("admin-translate-sales-chat", "sde-close-all-prs", ...), identical on
both sides; no trial suffix is present, nothing is stripped.  Rewards are
taken verbatim (the original side stores them rounded to 4 decimals, the
Harbor side at full float precision).  The file's mean_reward is checked
against the mean of its per-task rewards.
"""
import csv
import json
import os
import re
import sys


def side_rows(rc_dir, side):
    rows = []
    for fn in sorted(os.listdir(rc_dir)):
        m = re.fullmatch(rf"result_{side}_trial(\d+)\.json", fn)
        if not m:
            continue
        run = int(m.group(1))
        with open(os.path.join(rc_dir, fn), encoding="utf-8") as fh:
            data = json.load(fh)
        assert data["side"] == side and data["trial_num"] == run, fn
        rewards = {k: float(v) for k, v in data["per_task_rewards"].items()}
        assert len(rewards) == data["num_tasks"], fn
        assert all(0.0 <= x <= 1.0 for x in rewards.values()), fn
        assert abs(sum(rewards.values()) / len(rewards) - data["mean_reward"]) < 1e-5, fn
        rows += [(run, task, x) for task, x in rewards.items()]
    return rows


def write_csv(path, rows):
    rows.sort()
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["run", "task_id", "reward"])
        w.writerows(rows)


def main(download_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    rc_dir = os.path.join(download_dir, "results_collection")
    ids = {}
    for side in ("original", "harbor"):
        rows = side_rows(rc_dir, side)
        assert rows, f"no {side} files"
        keys = [(r, t) for r, t, _ in rows]
        assert len(keys) == len(set(keys)), f"duplicate (run, task_id) on {side} side"
        ids[side] = {t for _, t, _ in rows}
        write_csv(os.path.join(out_dir, f"{side}.csv"), rows)
        for run in sorted({r for r, _, _ in rows}):
            vals = [x for r, _, x in rows if r == run]
            print(f"{side} run {run}: n_tasks={len(vals)} mean={sum(vals) / len(vals):.6f}")
    print(f"tasks: original={len(ids['original'])} harbor={len(ids['harbor'])} "
          f"common={len(ids['original'] & ids['harbor'])}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
