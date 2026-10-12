#!/usr/bin/env python3
"""Per-task outcomes for the ARC-AGI-2 parity experiment (codex, gpt-5.2, 6 runs).

Usage: python -I arc_agi_2.py <download_dir> <out_dir> [--per-puzzle]

Reads <download_dir>/results_collection/result_{original,harbor}_trial<N>.json
(run = N, in numeric order) and writes <out_dir>/original.csv and
<out_dir>/harbor.csv with columns run,task_id,reward.

Task unit. One row per ARC test pair, 167 per run, task_id = "<puzzle>_<pair>"
(e.g. "0934a4d8_0"), which is exactly the Harbor task name; reward is 0/1
(pass@2: solved by at least one of two attempts). ARC-AGI-2's official score,
and the run scores published for this experiment, are the mean over the 120
puzzles of the fraction of each puzzle's test pairs solved; --per-puzzle emits
that view instead (task_id = puzzle id, fractional reward).

Original side: each file is a JSON list of 167 entries, one per test pair.
An entry is {"attempt_1": A, "attempt_2": A} with A = {"answer": grid,
"metadata": {..., "task_id": "<puzzle>", "pair_index": int}, "correct": bool}
or null (one attempt in trial 4 is null and counts as not correct). task_id is
metadata.task_id + "_" + metadata.pair_index.

Harbor side: each file is a Harbor job-level result.json. Trial names live in
stats.evals[<only eval>].reward_stats.reward = {"0.0": [...], "1.0": [...]}.
A trial name is "<puzzle>_<pair>__<suffix>"; the suffix after "__" is stripped.
Every task has two trials (n_attempts: 2); reward = max over them. The files'
own metrics[0].pass_at_2_rate is not used (it disagrees with reward_stats in
trials 1, 2 and 4).
"""
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path


def trial_files(download_dir, side):
    files = Path(download_dir, "results_collection").glob(f"result_{side}_trial*.json")
    return sorted(files, key=lambda p: int(re.search(r"trial(\d+)", p.name).group(1)))


def parse_original(path):
    rows = {}
    for entry in json.loads(path.read_text()):
        attempts = [entry.get("attempt_1"), entry.get("attempt_2")]
        meta = next(a for a in attempts if a)["metadata"]
        task_id = f"{meta['task_id']}_{meta['pair_index']}"
        assert task_id not in rows, (path.name, task_id)
        rows[task_id] = float(any(a and a.get("correct") for a in attempts))
    return rows


def parse_harbor(path):
    job = json.loads(path.read_text())
    (ev,) = job["stats"]["evals"].values()
    per_task = defaultdict(list)
    for reward, names in ev["reward_stats"]["reward"].items():
        for name in names:
            per_task[name.split("__", 1)[0]].append(float(reward))
    counts = sorted({len(v) for v in per_task.values()})
    if counts != [2]:
        print(f"  warning: {path.name} has {counts} trials per task, expected [2]")
    return {task_id: max(v) for task_id, v in per_task.items()}


def per_puzzle(rows):
    by_puzzle = defaultdict(list)
    for task_id, reward in rows.items():
        by_puzzle[task_id.rsplit("_", 1)[0]].append(reward)
    return {p: sum(v) / len(v) for p, v in by_puzzle.items()}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    download_dir, out_dir = Path(args[0]), Path(args[1])
    out_dir.mkdir(parents=True, exist_ok=True)
    for side, parse in (("original", parse_original), ("harbor", parse_harbor)):
        files = trial_files(download_dir, side)
        if not files:
            print(f"{side}: no files found")
            continue
        with open(out_dir / f"{side}.csv", "w", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["run", "task_id", "reward"])
            for run, path in enumerate(files, 1):
                rows = parse(path)
                if "--per-puzzle" in sys.argv:
                    rows = per_puzzle(rows)
                for task_id in sorted(rows):
                    writer.writerow([run, task_id, f"{rows[task_id]:g}"])
                mean = 100 * sum(rows.values()) / len(rows)
                print(f"{side} run {run} ({path.name}): {len(rows)} tasks, mean {mean:.2f}%")


if __name__ == "__main__":
    main()
