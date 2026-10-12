#!/usr/bin/env python3
"""Per-task outcomes for the deepsynth parity experiment (claude-code@2.1.73, anthropic/claude-haiku-4-5-20251001).

Usage: python -I deepsynth.py <download_dir> <out_dir>

<download_dir> is the local copy of adapters/deepsynth/ from the Hugging Face dataset
harborframework/parity-experiments (only results_collection/ is needed). Writes
<out_dir>/original.csv and <out_dir>/harbor.csv with columns run,task_id,reward.
Rewards are F1 scores in [0, 1] (fractional, not binary). result_oracle_trial1.json is ignored.
run = the trial number N from the file name.

Original side: results_collection/result_original_trial<N>.json
    { "n_tasks": 40, "parse_errors": int, "judge_upgrades": 0, "mean_score": float,
      "per_task": [ {"question_number": "3", "f1": float, "score": float,
                     "status": "ok"|"parse_error"|"missing"}, ... ] }
  reward  = "score" (F1 after the LLM-judge fallback; judge_upgrades is 0, so score == f1).
  task_id = "question_number" verbatim (a decimal string such as "3" or "79").

Harbor side: results_collection/result_harbor_trial<N>.json = Harbor job-level result.json
    { "n_total_trials": 40, "stats": { "evals": { "<agent>__deepsynth": {
          "reward_stats": {"reward": {"<reward>": ["<question>__<trial suffix>", ...]}},
          "exception_stats": {"<ExceptionName>": ["<question>__<trial suffix>", ...]},
          "metrics": [{"mean": float}] }}}}
  reward  = the reward_stats key parsed as float.
  task_id = the trial name with the Harbor trial suffix after "__" stripped
            ("11__b8uhXyb" -> "11"), which makes ids match the original side.
  Trials that raised NonZeroAgentExitCodeError (trial 2: 10 tasks, trial 3: 5 tasks) have no
  reward_stats entry; they are taken from exception_stats and given reward 0.0, which is how
  Harbor's own metrics.mean (= sum of rewards / n_total_trials) counts them. AgentTimeoutError
  trials already appear in reward_stats with 0.0. The reconstructed mean is checked against
  metrics.mean (Harbor) / mean_score (original) and the script aborts on disagreement.
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


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def parse_original(path):
    """Return ({task_id: reward}, file's own mean) for one original trial file."""
    data = load(path)
    rows = {}
    for row in data["per_task"]:
        tid = str(row["question_number"])
        if tid in rows:
            sys.exit(f"duplicate question_number {tid!r} in {path}")
        rows[tid] = float(row["score"])
    if len(rows) != data["n_tasks"]:
        sys.exit(f"{path}: {len(rows)} per_task rows but n_tasks={data['n_tasks']}")
    return rows, float(data["mean_score"])


def parse_harbor(path):
    """Return ({task_id: reward}, Harbor's own mean) for one Harbor job-level result.json."""
    data = load(path)
    evals = data["stats"]["evals"]
    if len(evals) != 1:
        sys.exit(f"{path}: expected exactly one eval, found {sorted(evals)}")
    (ev,) = evals.values()
    rows = {}
    for key, names in ev["reward_stats"]["reward"].items():
        for name in names:
            tid = name.split("__", 1)[0]
            if tid in rows:
                sys.exit(f"duplicate task {tid!r} ({name}) in {path}")
            rows[tid] = float(key)
    filled = []
    for names in ev.get("exception_stats", {}).values():
        for name in names:
            tid = name.split("__", 1)[0]
            if tid not in rows:
                rows[tid] = 0.0
                filled.append(tid)
    if filled:
        print(f"  {os.path.basename(path)}: {len(filled)} errored trials with no reward "
              f"entry filled with 0.0: {sorted(filled, key=int)}")
    if len(rows) != data["n_total_trials"]:
        sys.exit(f"{path}: {len(rows)} tasks but n_total_trials={data['n_total_trials']}")
    return rows, float(ev["metrics"][0]["mean"])


PARSERS = {"original": parse_original, "harbor": parse_harbor}


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    download_dir, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    for side, runs in find_result_files(download_dir).items():
        if not runs:
            print(f"{side}: no files, skipping")
            continue
        out_path = os.path.join(out_dir, f"{side}.csv")
        n_rows = 0
        with open(out_path, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["run", "task_id", "reward"])
            for run, path in sorted(runs):
                rows, file_mean = PARSERS[side](path)
                bad = {t: r for t, r in rows.items() if not 0.0 <= r <= 1.0}
                if bad:
                    sys.exit(f"{path}: rewards outside [0, 1]: {bad}")
                mean = sum(rows.values()) / len(rows)
                if abs(mean - file_mean) > 5e-4:
                    sys.exit(f"{path}: reconstructed mean {mean:.6f} != file mean {file_mean:.6f}")
                for tid in sorted(rows, key=lambda t: (len(t), t)):
                    w.writerow([run, tid, rows[tid]])
                n_rows += len(rows)
                print(f"{side} run {run}: {len(rows)} tasks, mean reward {mean:.4f} "
                      f"(file says {file_mean:.4f})")
        print(f"wrote {out_path} ({n_rows} rows)")


if __name__ == "__main__":
    main()
