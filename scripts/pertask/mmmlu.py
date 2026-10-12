"""Per-task outcomes for the MMMLU parity experiment (HF adapters/mmmlu).

Usage: python -I mmmlu.py <download_dir> <out_dir>
<download_dir> is the local mirror of adapters/mmmlu/ (only results_collection/ is
read). Stdlib only; nothing in <download_dir> is executed. Experiment: agent
codex-cli@0.69.0, model gpt-5.1-codex-mini, 150 tasks (10 per language x 15
languages) x 5 trials per side, metric accuracy.

Both sides in results_collection/ use the Harbor job-level result.json layout:
result_{original,harbor}_trial<k>.json -> stats.evals[<eval name>].reward_stats
.reward = {"<reward>": [trial names...]}, one file per run (k = 1..5). The eval
name is "codex__simple_evals" on the original side (the simple-evals output was
repackaged in Harbor's layout) and "codex__mmmlu_parity" on the Harbor side.
Rewards are "0.0" / "1.0" (exact multiple-choice letter match, no partial credit).

Task ids: on BOTH sides the trial names are "<task>__<7-char suffix>", e.g.
"mmmlu-ar-xy-00001__whc28WW"; the suffix after "__" is stripped (it differs
between sides and runs), so task_id = "mmmlu-<lang>-<5-digit index>", the Harbor
task directory name. Each run's mean is checked against the file's own
metrics[0].mean before writing.

Outputs <out_dir>/original.csv and <out_dir>/harbor.csv with columns
run,task_id,reward (run = trial number k).
"""
import csv
import json
import os
import sys

RUNS = (1, 2, 3, 4, 5)


def read_rewards(path):
    """Return (eval name, {task_id: reward}) from a Harbor-style job result.json."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    evals = data["stats"]["evals"]
    if len(evals) != 1:
        sys.exit(f"{path}: expected one eval, found {list(evals)}")
    (name, ev), = evals.items()
    if ev.get("exception_stats"):
        print(f"  WARNING {os.path.basename(path)}: exception_stats={ev['exception_stats']}")
    out = {}
    for reward, names in ev["reward_stats"]["reward"].items():
        r = float(reward)
        if not 0 <= r <= 1:
            sys.exit(f"{path}: reward {r} outside [0,1]")
        for n in names:
            tid = n.split("__", 1)[0]
            if tid in out:
                sys.exit(f"{path}: duplicate task id {tid}")
            out[tid] = r
    if len(out) != ev["n_trials"] or len(out) != data["n_total_trials"]:
        print(f"  WARNING {os.path.basename(path)}: {len(out)} ids vs n_trials={ev['n_trials']}")
    mean = sum(out.values()) / len(out)
    if abs(mean - ev["metrics"][0]["mean"]) > 1e-9:
        sys.exit(f"{path}: recomputed mean {mean} != metrics mean {ev['metrics'][0]['mean']}")
    return name, out


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
    rc = os.path.join(dl, "results_collection")
    ids_by_side = {}
    for side in ("original", "harbor"):
        rows, ids_by_run = [], {}
        for k in RUNS:
            p = os.path.join(rc, f"result_{side}_trial{k}.json")
            if not os.path.exists(p):
                print(f"  WARNING missing {p}")
                continue
            name, rewards = read_rewards(p)
            print(f"  {side} trial{k}: eval {name}, {len(rewards)} tasks")
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
              f"{len(ids_by_side['harbor'])}, common {len(common)}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
