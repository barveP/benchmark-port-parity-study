"""Per-task outcomes for the SimpleQA parity experiment (HF adapters/simpleqa).

Usage: python -I simpleqa.py <download_dir> <out_dir>
<download_dir> is the local mirror of adapters/simpleqa/ (results_collection/).
Stdlib only; nothing in <download_dir> is executed. Experiment: agent claude-code@2.1.32, model claude-opus-4-6,
50 tasks x 3 trials per side.

Both sides in results_collection/ use the Harbor job-level result.json layout:
result_{original,harbor}_trial<k>.json  ->  stats.evals["claude-code__simpleqa"]
.reward_stats.reward = {"<reward>": [task ids...]}, one file per run (k = 1, 2, 3).
Rewards are "0.0" / "1.0" (LLM-judge CORRECT vs not; no partial credit). The
"original" side was itself run as a Harbor job over the simple-evals Harbor
adapter (speed1313/simple-evals-harbor-adapter), so both sides share the layout.

Task ids: both sides list Harbor trial names "simpleqa-<index>__<7-char suffix>",
e.g. "simpleqa-29__Op0xLJL" (original) / "simpleqa-29__5KodLwn" (harbor). The
suffix after "__" is stripped on BOTH sides, so both CSVs use task_id =
"simpleqa-<index>" with index 0..49 (the first 50 SimpleQA questions).

Errored trials: a trial listed in exception_stats but absent from reward_stats
(Harbor trial 3: simpleqa-3 and simpleqa-7, RuntimeError) has no recorded
reward. Harbor's own metrics.mean divides by n_total_trials (47/50 = 0.94 for
that file), i.e. it scores such trials as 0, so this parser writes reward 0 for
them (printed as a NOTE) to reproduce the published run scores. Trials that
errored but still carry a reward (AgentTimeoutError -> 0.0) are taken as is.

Outputs <out_dir>/original.csv and <out_dir>/harbor.csv with columns
run,task_id,reward (run = trial number).
"""
import csv
import json
import os
import sys

RUNS = (1, 2, 3)


def read_rewards(path):
    """Return (eval name, {task_id: reward}) from a Harbor-style job result.json."""
    with open(path) as f:
        evals = json.load(f)["stats"]["evals"]
    if len(evals) != 1:
        sys.exit(f"{path}: expected one eval, found {list(evals)}")
    (name, ev), = evals.items()
    out = {}
    for reward, ids in ev["reward_stats"]["reward"].items():
        r = float(reward)
        if not 0 <= r <= 1:
            sys.exit(f"{path}: reward {r} outside [0,1]")
        for tid in ids:
            tid = tid.split("__", 1)[0]
            if tid in out:
                sys.exit(f"{path}: duplicate task id {tid}")
            out[tid] = r
    if len(out) != ev["n_trials"]:
        print(f"  WARNING {os.path.basename(path)}: {len(out)} ids vs n_trials={ev['n_trials']}")
    for exc, ids in ev.get("exception_stats", {}).items():
        for tid in ids:
            tid = tid.split("__", 1)[0]
            if tid not in out:  # errored with no reward: Harbor scores it as 0
                out[tid] = 0.0
                print(f"  NOTE {os.path.basename(path)}: {tid} {exc} without reward -> 0")
            else:
                print(f"  NOTE {os.path.basename(path)}: {tid} {exc} with reward {out[tid]}")
    return name, out


def task_index(tid):
    return int(tid.rsplit("-", 1)[1])


def write_csv(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["run", "task_id", "reward"])
        for run, tid, r in sorted(rows, key=lambda x: (x[0], task_index(x[1]))):
            w.writerow([run, tid, int(r) if r.is_integer() else r])
    by_run = {}
    for run, _, r in rows:
        by_run.setdefault(run, []).append(r)
    print(f"{os.path.basename(path)}: {len(rows)} rows, run means % = " + ", ".join(
        f"run{k}: {100 * sum(v) / len(v):.2f} (n={len(v)})" for k, v in sorted(by_run.items())))


def main(dl, out):
    os.makedirs(out, exist_ok=True)
    rc = os.path.join(dl, "results_collection")
    for side in ("original", "harbor"):
        rows, ids_by_run = [], {}
        for k in RUNS:
            p = os.path.join(rc, f"result_{side}_trial{k}.json")
            if not os.path.exists(p):
                print(f"  WARNING missing {p}")
                continue
            name, rewards = read_rewards(p)
            print(f"  {side} trial{k}: eval {name}, {len(rewards)} tasks")
            ids_by_run[k] = set(rewards)
            rows += [(k, t, r) for t, r in rewards.items()]
        if not rows:
            print(f"{side}: no per-task data; nothing written")
            continue
        if len(set(map(frozenset, ids_by_run.values()))) != 1:
            print(f"  WARNING {side}: task sets differ across runs")
        write_csv(os.path.join(out, f"{side}.csv"), rows)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
