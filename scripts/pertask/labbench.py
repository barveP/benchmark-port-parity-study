"""Per-task outcomes for the LAB-Bench FigQA parity experiment (HF adapters/labbench).

Usage: python -I labbench.py <download_dir> <out_dir>
<download_dir> is the local mirror of adapters/labbench/; only results_collection/
is read. Stdlib only; nothing in <download_dir> is executed. Experiment: agent codex@0.71.0, model gpt-5-codex,
181 FigQA tasks x 3 trials per side. A fourth Harbor trial (mean 0.392) exists in
results_collection but is not in the snapshot JSON, so it is excluded (see HARBOR_RUNS).

Both sides are Harbor job-level result.json files:
results_collection/result_{original,harbor}_trial<k>.json -> stats.evals[<name>]
with reward_stats.reward = {"<reward>": [ids...]} and exception_stats =
{<error type>: [ids...]}. Rewards are "0.0" / "1.0" (exact letter match).

Harbor side (eval codex__gpt-5-codex__labbench): ids are Harbor trial names
"figqa-NNNN__<7-char suffix>"; the suffix after "__" is stripped. All 181 tasks
are in reward_stats; AgentTimeoutError trials are listed in exception_stats and
also carry reward 0.0 in reward_stats, so metrics[0].mean is a mean over 181.

Original side (eval codex__labbench, LAB-Bench's own codex runner): ids are
"run_NNNN" (0001..0181). reward_stats lists only the answered ("sure") runs; runs
with no parseable answer appear only under exception_stats (NoAnswer /
ParseError) and are scored 0 here, which reproduces the published
metrics[0].accuracy = correct / 181 exactly. The one "unsure" run (trial 2,
run_0095) is already in the "0.0" bucket.

Task ids: original "run_NNNN" is rewritten to "figqa-NNNN" so both CSVs share a
key. The mapping was checked by hand on HF: original_parity/*/run_NNNN/prompt.txt
and harbor_parity/*/figqa-NNNN__*/agent/codex.txt pose the same question for
NNNN = 0003, 0100, 0181, and run numbering is identical across the three
original artifact folders.

Outputs <out_dir>/original.csv and <out_dir>/harbor.csv with columns
run,task_id,reward (run = trial number).
"""
import csv
import json
import os
import re
import sys

ORIGINAL_RUNS = (1, 2, 3)
HARBOR_RUNS = (1, 2, 3)  # trial 4 is in results_collection but not in the snapshot


def load_eval(path):
    with open(path) as f:
        evals = json.load(f)["stats"]["evals"]
    if len(evals) != 1:
        sys.exit(f"{path}: expected one eval, found {list(evals)}")
    (name, ev), = evals.items()
    return name, ev


def harbor_rewards(path):
    """{figqa-NNNN: reward}; trial suffix stripped; timeouts are already scored 0."""
    name, ev = load_eval(path)
    out = {}
    for reward, ids in ev["reward_stats"]["reward"].items():
        for tid in ids:
            base = tid.split("__", 1)[0]
            if base in out:
                sys.exit(f"{path}: duplicate task id {base}")
            out[base] = float(reward)
    errored = [t.split("__", 1)[0] for ids in ev["exception_stats"].values() for t in ids]
    if any(t not in out for t in errored):
        sys.exit(f"{path}: some errored trials are absent from reward_stats")
    if abs(sum(out.values()) / len(out) - ev["metrics"][0]["mean"]) > 1e-9:
        sys.exit(f"{path}: reconstructed mean != published metrics mean")
    return name, out


def original_rewards(path):
    """{figqa-NNNN: reward}; unanswered runs (exception_stats only) scored 0."""
    name, ev = load_eval(path)
    out = {}
    for reward, ids in ev["reward_stats"]["reward"].items():
        for tid in ids:
            out[rename(tid, path)] = float(reward)
    for err, ids in ev["exception_stats"].items():
        for tid in ids:
            tid = rename(tid, path)
            if tid in out:
                sys.exit(f"{path}: {tid} is both scored and in exception_stats[{err}]")
            out[tid] = 0.0
    if abs(sum(out.values()) / len(out) - ev["metrics"][0]["accuracy"]) > 1e-9:
        sys.exit(f"{path}: reconstructed accuracy != published accuracy")
    return name, out


def rename(tid, path):
    m = re.fullmatch(r"run_(\d{4})", tid)
    if not m:
        sys.exit(f"{path}: unexpected original task id {tid!r}")
    return f"figqa-{m.group(1)}"


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
    for side, runs, reader in (("original", ORIGINAL_RUNS, original_rewards),
                               ("harbor", HARBOR_RUNS, harbor_rewards)):
        rows, ids_by_run = [], {}
        for k in runs:
            p = os.path.join(rc, f"result_{side}_trial{k}.json")
            if not os.path.exists(p):
                print(f"  WARNING missing {p}")
                continue
            name, rewards = reader(p)
            if len(rewards) != load_eval(p)[1]["n_trials"]:
                print(f"  WARNING {os.path.basename(p)}: {len(rewards)} ids vs n_trials")
            bad = {t: r for t, r in rewards.items() if not 0 <= r <= 1}
            if bad:
                sys.exit(f"{p}: rewards outside [0,1]: {bad}")
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
