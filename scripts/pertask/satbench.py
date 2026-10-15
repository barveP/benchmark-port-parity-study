"""Per-task outcomes for the SATBench parity experiment (HF adapters/satbench).

Usage: python -I satbench.py <download_dir> <out_dir>
<download_dir> is the local mirror of adapters/satbench/ (results_collection/ and
original_parity/ are read). Stdlib only.
Experiment: agent codex@0.77.0, model gpt-5-nano-2025-08-07, 100 tasks sampled
from 2100 x 3 runs per side, metric accuracy (SAT/UNSAT label match).

Original side: original_parity/codex_eval_results<k>.jsonl (k = 1..3), one JSON
object per line with keys task_idx, gold_label, pred_label, correct, output.
reward = 1 if correct is true else 0 (pred_label null = unparseable answer = 0).
task_id = task_idx, which is the 0..99 position inside the 100-task parity
sample, NOT the index into the full 2100-task dataset.

Harbor side: results_collection/result_harbor_trial<k>.json, Harbor job-level
layout stats.evals["codex__satbench"].reward_stats.reward = {"1.0"|"0.0":
[trial names]}. Trial names are "<dataset index>__<7-char suffix>", e.g.
"500__ea36jLL"; the suffix after "__" is stripped, so task_id = the index into
the full 2100-task dataset (e.g. "500"). Each run's mean is checked against the
file's own metrics[0].mean.

The two id spaces therefore do not overlap (original 0..99 vs Harbor dataset
indices); pairing them needs the parity sample list from the SATBench repo
(evaluate_codex.py --parity), which is not in the HF folder.

Outputs <out_dir>/original.csv and <out_dir>/harbor.csv, columns run,task_id,reward.
"""
import csv
import json
import os
import sys

RUNS = (1, 2, 3)


def read_original(path):
    """{task_idx: 0/1} from one original-side JSONL file."""
    out = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            d = json.loads(line)
            tid = str(d["task_idx"])
            if tid in out:
                sys.exit(f"{path}: duplicate task_idx {tid}")
            if not isinstance(d["correct"], bool):
                sys.exit(f"{path}: non-boolean 'correct' for task {tid}")
            out[tid] = int(d["correct"])
    return out


def read_harbor(path):
    """{dataset index: reward} from a Harbor job-level result.json."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    (name, ev), = data["stats"]["evals"].items()
    if ev.get("n_errors") or ev.get("exception_stats"):
        print(f"  WARNING {os.path.basename(path)}: errors={ev.get('n_errors')} "
              f"exceptions={ev.get('exception_stats')}")
    out = {}
    for reward, names in ev["reward_stats"]["reward"].items():
        r = float(reward)
        if not 0 <= r <= 1:
            sys.exit(f"{path}: reward {r} outside [0,1]")
        for n in names:
            tid = n.split("__", 1)[0]  # strip the per-trial suffix
            if tid in out:
                sys.exit(f"{path}: duplicate task id {tid}")
            out[tid] = int(r) if r.is_integer() else r
    if len(out) != data["n_total_trials"]:
        print(f"  WARNING {os.path.basename(path)}: {len(out)} ids vs "
              f"n_total_trials={data['n_total_trials']}")
    mean = sum(out.values()) / len(out)
    if abs(mean - ev["metrics"][0]["mean"]) > 1e-9:
        sys.exit(f"{path}: recomputed mean {mean} != metrics mean {ev['metrics'][0]['mean']}")
    return out


def write_csv(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["run", "task_id", "reward"])
        for run, tid, r in sorted(rows, key=lambda x: (x[0], int(x[1]))):
            w.writerow([run, tid, r])
    by_run = {}
    for run, _, r in rows:
        by_run.setdefault(run, []).append(r)
    print(f"{os.path.basename(path)}: {len(rows)} rows, run means % = " + ", ".join(
        f"run{k}: {100 * sum(v) / len(v):.2f} (n={len(v)})" for k, v in sorted(by_run.items())))


def main(dl, out):
    os.makedirs(out, exist_ok=True)
    sides = {
        "original": (os.path.join(dl, "original_parity", "codex_eval_results{}.jsonl"), read_original),
        "harbor": (os.path.join(dl, "results_collection", "result_harbor_trial{}.json"), read_harbor),
    }
    ids_by_side = {}
    for side, (pattern, reader) in sides.items():
        rows, ids_by_run = [], {}
        for k in RUNS:
            p = pattern.format(k)
            if not os.path.exists(p):
                print(f"  WARNING missing {p}")
                continue
            rewards = reader(p)
            print(f"  {side} run{k}: {len(rewards)} tasks")
            ids_by_run[k] = frozenset(rewards)
            rows += [(k, t, r) for t, r in rewards.items()]
        if not rows:
            print(f"{side}: no per-task data; nothing written")
            continue
        if len(set(ids_by_run.values())) != 1:
            print(f"  WARNING {side}: task sets differ across runs")
        ids_by_side[side] = set().union(*ids_by_run.values())
        write_csv(os.path.join(out, f"{side}.csv"), rows)
    if len(ids_by_side) == 2:
        common = ids_by_side["original"] & ids_by_side["harbor"]
        print(f"tasks: original {len(ids_by_side['original'])}, harbor "
              f"{len(ids_by_side['harbor'])}, common {len(common)} "
              "(id spaces differ: parity-sample position vs dataset index)")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
