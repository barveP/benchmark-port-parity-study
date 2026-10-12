"""Per-task outcomes for the LLM-SRBench parity experiment (HF adapters/llmsr-bench).

Usage: python -I llmsr_bench.py <download_dir> <out_dir>
<download_dir> is the local mirror of adapters/llmsr-bench/ (results_collection/).
Stdlib only; nothing in <download_dir> is executed.
Experiment: agent llmsr_llmdirect@0.3.0 (LLM-direct symbolic regression), model
gpt-4o-mini-2024-07-18; 115 tasks (23 per dataset x 5 datasets, sampled from the
240-task benchmark with task-seed 42) x 3 trials per side.

Both sides use the same custom summary format, one file per run:
results_collection/result_<harbor|original>_trial<k>.json (NOT the Harbor
job-level stats.evals layout):
  {"trials": [{"trial": k, "seed": k-1, "tasks": [
      {"dataset": "bio_pop_growth" | "chem_react" | "lsrtransform" | "matsci" | "phys_osc",
       "problem": "<benchmark id, e.g. BPG0, CRK3, I.11.19_2_0, MatSci7, PO12>",
       "metrics": {"r2", "mse", "nmse", "ood_r2", "ood_mse", "ood_nmse"}}, ...]}]}

Reward = metrics["r2"], the in-distribution test-split R^2 (the published headline
metric). nmse == 1 - r2 for every task, so NMSE carries no extra information.
R^2 is fractional and may be slightly negative (worse than predicting the mean);
it is recorded UNCLIPPED because the published run means are unclipped means of
these values. The published failure filter (r2 <= -100 or nmse >= 1e9) is applied
here as well; it drops nothing in the released files. OOD metrics (None for 23
tasks) are ignored.

task_id = "<dataset>/<problem>", the two identifier fields exactly as they appear
in the files (problem ids happen to be unique on their own; the pair is the
benchmark's identifier and is identical on both sides). The Harbor task
directories are a lossy lowercase rendering of the same pair
("llmsr-bench-<dataset>-<problem lowercased, dots to dashes>__<suffix>") and are
not used.

Outputs <out_dir>/original.csv and <out_dir>/harbor.csv with columns
run,task_id,reward (run = the "trial" number stored in the file).
"""
import csv
import json
import os
import sys

RUNS = (1, 2, 3)
R2_FAIL, NMSE_FAIL = -100.0, 1e9  # published failure filter


def trial_rewards(path):
    """(trial number, {task_id: r2}) from one results_collection trial file."""
    with open(path) as f:
        trials = json.load(f)["trials"]
    if len(trials) != 1:
        sys.exit(f"{path}: expected one trial, found {len(trials)}")
    t = trials[0]
    out, dropped = {}, []
    for task in t["tasks"]:
        tid = f"{task['dataset']}/{task['problem']}"
        if tid in out:
            sys.exit(f"{path}: duplicate task id {tid}")
        r2, nmse = float(task["metrics"]["r2"]), float(task["metrics"]["nmse"])
        if r2 <= R2_FAIL or nmse >= NMSE_FAIL:
            dropped.append(tid)
            continue
        out[tid] = r2
    if dropped:
        print(f"  WARNING {os.path.basename(path)}: {len(dropped)} failed tasks dropped: {dropped[:5]}")
    return t["trial"], out


def write_csv(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["run", "task_id", "reward"])
        for run, tid, r in sorted(rows):
            w.writerow([run, tid, int(r) if r.is_integer() else r])
    by_run = {}
    for run, _, r in rows:
        by_run.setdefault(run, []).append(r)
    print(f"{os.path.basename(path)}: {len(rows)} rows, run mean R2 = " + ", ".join(
        f"run{k}: {sum(v) / len(v):.4f} (n={len(v)})" for k, v in sorted(by_run.items())))


def main(dl, out):
    os.makedirs(out, exist_ok=True)
    ids_by_side = {}
    for side in ("original", "harbor"):
        rows, ids_by_run = [], {}
        for k in RUNS:
            p = os.path.join(dl, "results_collection", f"result_{side}_trial{k}.json")
            if not os.path.exists(p):
                print(f"  WARNING missing {p}")
                continue
            trial, rewards = trial_rewards(p)
            if trial != k:
                print(f"  WARNING {os.path.basename(p)}: file says trial {trial}, using run {k}")
            neg = sorted((r, t) for t, r in rewards.items() if not 0 <= r <= 1)
            if neg:
                print(f"  NOTE {os.path.basename(p)}: {len(neg)} R2 values outside [0,1], min {neg[0][0]:.4f} ({neg[0][1]})")
            ids_by_run[k] = set(rewards)
            rows += [(k, t, r) for t, r in rewards.items()]
        if not rows:
            print(f"{side}: no per-task data; nothing written")
            continue
        if len(set(map(frozenset, ids_by_run.values()))) != 1:
            print(f"  WARNING {side}: task sets differ across runs")
        ids_by_side[side] = set.union(*ids_by_run.values())
        write_csv(os.path.join(out, f"{side}.csv"), rows)
    if len(ids_by_side) == 2:
        o, h = ids_by_side["original"], ids_by_side["harbor"]
        print(f"task ids: original {len(o)}, harbor {len(h)}, common {len(o & h)}")
        if o != h:
            print(f"  WARNING only-original {sorted(o - h)[:5]} only-harbor {sorted(h - o)[:5]}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
