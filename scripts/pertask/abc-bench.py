#!/usr/bin/env python3
"""Per-task outcomes for the abc-bench parity experiment (codex@0.118.0, openai/gpt-5-mini).

Usage: python -I abc-bench.py <download_dir> <out_dir>

<download_dir> is the local copy of adapters/abc-bench/ from the Hugging Face dataset
harborframework/parity-experiments (only results_collection/ is needed). Writes
<out_dir>/original.csv and <out_dir>/harbor.csv with columns run,task_id,reward.

Formats (both sides share one sanitized layout, written by the adapter author):
  results_collection/result_<side>_trial<N>.json
    { "side": "original"|"harbor", "round": N, "agent": ..., "model": ...,
      "results": [ {"task_id": str, "trial_name": str, "reward": 0|1,
                    "solved": bool, "raw_status": str}, ... ],
      "summary": {"solved": int, "total": int, "solve_rate_pct": float} }
  Original side = Terminal-Bench results.json is_resolved (null/parse_error -> 0).
  Harbor side   = verifier_result.rewards.reward (errored / no_reward -> 0).

Task ids: the "task_id" field is used verbatim. The benchmark's own ids contain a
double underscore (task_<repo>__<feature>); that is NOT a Harbor trial suffix, so
nothing is stripped. The Harbor trial suffix lives in the separate "trial_name"
field and is ignored. run = the trial number N from the file name.
"""
import csv
import json
import os
import re
import sys

NAME_RE = re.compile(r"^result_(original|harbor)_trial(\d+)\.json$")


def find_result_files(download_dir):
    """Return {side: [(run, path), ...]} from results_collection/ (or download_dir itself)."""
    for d in (os.path.join(download_dir, "results_collection"), download_dir):
        found = {"original": [], "harbor": []}
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            m = NAME_RE.match(name)
            if m:
                found[m.group(1)].append((int(m.group(2)), os.path.join(d, name)))
        if any(found.values()):
            return found
    sys.exit(f"no result_<side>_trial<N>.json files under {download_dir}")


def parse_file(path):
    """Yield (task_id, reward) for one trial file; reward coerced to float, must be 0/1."""
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    seen = set()
    for row in data["results"]:
        tid = row["task_id"]
        reward = float(row["reward"])
        if tid in seen:
            sys.exit(f"duplicate task_id {tid!r} in {path}")
        if reward not in (0.0, 1.0):
            sys.exit(f"non-binary reward {reward!r} for {tid!r} in {path}")
        if bool(row.get("solved", reward == 1.0)) != (reward == 1.0):
            sys.exit(f"reward/solved disagree for {tid!r} in {path}")
        seen.add(tid)
        yield tid, reward


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    download_dir, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    files = find_result_files(download_dir)
    for side, runs in files.items():
        if not runs:
            print(f"{side}: no files, skipping")
            continue
        out_path = os.path.join(out_dir, f"{side}.csv")
        n_rows = 0
        with open(out_path, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["run", "task_id", "reward"])
            for run, path in sorted(runs):
                rows = list(parse_file(path))
                for tid, reward in rows:
                    w.writerow([run, tid, int(reward)])
                n_rows += len(rows)
                mean = sum(r for _, r in rows) / len(rows)
                print(f"{side} run {run}: {len(rows)} tasks, mean reward {mean:.4f} ({100*mean:.2f}%)")
        print(f"wrote {out_path} ({n_rows} rows)")


if __name__ == "__main__":
    main()
