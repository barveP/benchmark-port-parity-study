"""Per-task outcomes for the LawBench parity experiment (HF adapters/lawbench).

Usage: python -I lawbench.py <download_dir> <out_dir>
<download_dir> is the local mirror of adapters/lawbench/ (results_collection/ and
original_parity/). Stdlib only.
Experiment: agent qwen-code@0.6.0, model glm-4.7, 120 tasks x 3 trials per side.
A "task" is one 25-question chunk of one LawBench scenario under one prompt type
(20 scenarios x 3 chunks x {zero-shot, one-shot}); its reward is the chunk's mean
score in [0, 1] (fractional, not 0/1).

Harbor side: results_collection/result_harbor_trial<k>.json, the Harbor job-level
result.json: stats.evals["qwen-coder__lawbench"].reward_stats.reward =
{"<reward>": [trial names...]}, one file per run. Trial names are
"<task name>__<7-char suffix>", e.g. "lawbench-1-2-1-zero-shot__h3Cw88c"; the
suffix after "__" is stripped, so task_id = the Harbor task name
"lawbench-<scenario>-<chunk>-<prompt>" (as listed in config.yaml).

Original side: original_parity/result_origin_trial<k>.json, the summary written
by LawBench's qwen_code/run_qwen_code_baseline.py: by_prompt[<prompt>]
.individual_chunk_scores = {"<scenario>-<chunk>": score} (60 per prompt type).
There is no single id field, so task_id is composed as
"lawbench-<scenario>-<chunk>-<prompt>" to match the Harbor task names. The
file's own overall_average is checked against the mean of the 120 chunk scores.

Outputs <out_dir>/original.csv and <out_dir>/harbor.csv with columns
run,task_id,reward (run = trial number).
"""
import csv
import json
import os
import sys

RUNS = (1, 2, 3)
PROMPTS = ("zero-shot", "one-shot")


def harbor_rewards(path):
    """{task_id: reward} from a Harbor job-level result.json (suffix stripped)."""
    with open(path) as f:
        evals = json.load(f)["stats"]["evals"]
    if len(evals) != 1:
        sys.exit(f"{path}: expected one eval, found {list(evals)}")
    (_, ev), = evals.items()
    out = {}
    for reward, ids in ev["reward_stats"]["reward"].items():
        for tid in ids:
            tid = tid.split("__", 1)[0]
            if tid in out:
                sys.exit(f"{path}: duplicate task id {tid}")
            out[tid] = float(reward)
    if len(out) != ev["n_trials"]:
        print(f"  WARNING {os.path.basename(path)}: {len(out)} ids vs n_trials={ev['n_trials']}")
    return out


def original_rewards(path):
    """{task_id: reward} from a LawBench baseline-runner summary JSON."""
    with open(path) as f:
        d = json.load(f)
    out = {}
    for prompt in PROMPTS:
        for chunk, score in d["by_prompt"][prompt]["individual_chunk_scores"].items():
            tid = f"lawbench-{chunk}-{prompt}"
            if tid in out:
                sys.exit(f"{path}: duplicate task id {tid}")
            out[tid] = float(score)
    mean = sum(out.values()) / len(out)
    if abs(mean - d["overall_average"]) > 1e-6:
        print(f"  WARNING {os.path.basename(path)}: chunk mean {mean:.6f} != overall_average {d['overall_average']:.6f}")
    return out


def write_csv(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["run", "task_id", "reward"])
        for run, tid, r in sorted(rows):
            w.writerow([run, tid, int(r) if r.is_integer() else r])
    by_run = {}
    for run, _, r in rows:
        by_run.setdefault(run, []).append(r)
    print(f"{os.path.basename(path)}: {len(rows)} rows, run means % = " + ", ".join(
        f"run{k}: {100 * sum(v) / len(v):.2f} (n={len(v)})" for k, v in sorted(by_run.items())))


def main(dl, out):
    os.makedirs(out, exist_ok=True)
    sides = (
        ("original", os.path.join(dl, "original_parity", "result_origin_trial{}.json"), original_rewards),
        ("harbor", os.path.join(dl, "results_collection", "result_harbor_trial{}.json"), harbor_rewards),
    )
    ids_by_side = {}
    for side, pattern, reader in sides:
        rows, ids_by_run = [], {}
        for k in RUNS:
            p = pattern.format(k)
            if not os.path.exists(p):
                print(f"  WARNING missing {p}")
                continue
            rewards = reader(p)
            bad = {t: r for t, r in rewards.items() if not 0 <= r <= 1}
            if bad:
                sys.exit(f"{p}: rewards outside [0,1]: {bad}")
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
