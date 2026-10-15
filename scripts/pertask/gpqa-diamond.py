"""Per-task outcomes for the GPQA Diamond parity experiment (HF adapters/gpqa-diamond).

Usage: python -I gpqa-diamond.py <download_dir> <out_dir>
<download_dir> is the local mirror of adapters/gpqa-diamond/ (results_collection/
and, optionally, original_parity/*.csv). Stdlib only.
Experiment: agent codex, model gpt-5.2, 198 tasks x 3 trials per side.

Both sides in results_collection/ use the Harbor job-level result.json layout:
result_{original,harbor}_trial<k>.json  ->  stats.evals[<eval name>].reward_stats
.reward = {"<reward>": [task ids...]}, one file per run (k = 1, 2, 3). Rewards are
"0.0" / "1.0" (exact letter match, no partial credit).

Task ids: the original files list ids as the plain GPQA Diamond row index
"0".."197"; the Harbor files list Harbor trial names "<index>__<7-char suffix>",
e.g. "135__nn6ZbnP". The suffix after "__" is stripped, so both CSVs use the same
task_id = the row index. Original-side ids are cross-checked, when
original_parity/original-parity-trial<k>.csv is present, against that CSV's
"Question id" and "Correct" (True/False) columns, which are the original
benchmark's own per-question output; any disagreement aborts the run.

Outputs <out_dir>/original.csv and <out_dir>/harbor.csv with columns
run,task_id,reward (run = trial number).
"""
import csv
import json
import os
import sys

RUNS = (1, 2, 3)


def read_rewards(path, strip_suffix):
    """Return {task_id: reward} from a Harbor-style job result.json."""
    with open(path) as f:
        evals = json.load(f)["stats"]["evals"]
    if len(evals) != 1:
        sys.exit(f"{path}: expected one eval, found {list(evals)}")
    (name, ev), = evals.items()
    out = {}
    for reward, ids in ev["reward_stats"]["reward"].items():
        r = float(reward)
        for tid in ids:
            if strip_suffix:
                tid = tid.split("__", 1)[0]
            if tid in out:
                sys.exit(f"{path}: duplicate task id {tid}")
            out[tid] = r
    if len(out) != ev["n_trials"]:
        print(f"  WARNING {os.path.basename(path)}: {len(out)} ids vs n_trials={ev['n_trials']}")
    return name, out


def original_csv(path):
    """{Question id: 1/0} from the original benchmark's per-question CSV."""
    out = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            val = row["Correct"].strip()
            if val not in ("True", "False"):
                sys.exit(f"{path}: unexpected Correct value {val!r}")
            out[row["Question id"].strip()] = 1.0 if val == "True" else 0.0
    return out


def write_csv(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["run", "task_id", "reward"])
        for run, tid, r in sorted(rows, key=lambda x: (x[0], int(x[1]))):
            w.writerow([run, tid, int(r) if r.is_integer() else r])
    by_run = {}
    for run, _, r in rows:
        by_run.setdefault(run, []).append(r)
    print(f"{os.path.basename(path)}: {len(rows)} rows, run means % = " + ", ".join(
        f"run{k}: {100 * sum(v) / len(v):.2f} (n={len(v)})" for k, v in sorted(by_run.items())))


def main(dl, out):
    os.makedirs(out, exist_ok=True)
    rc = os.path.join(dl, "results_collection")
    for side, strip in (("original", False), ("harbor", True)):
        rows, ids_by_run = [], {}
        for k in RUNS:
            p = os.path.join(rc, f"result_{side}_trial{k}.json")
            if not os.path.exists(p):
                print(f"  WARNING missing {p}")
                continue
            name, rewards = read_rewards(p, strip)
            bad = {t: r for t, r in rewards.items() if not 0 <= r <= 1}
            if bad:
                sys.exit(f"{p}: rewards outside [0,1]: {bad}")
            if side == "original":
                cp = os.path.join(dl, "original_parity", f"original-parity-trial{k}.csv")
                if os.path.exists(cp):
                    ref = original_csv(cp)
                    if ref != rewards:
                        diff = {t for t in set(ref) | set(rewards) if ref.get(t) != rewards.get(t)}
                        sys.exit(f"trial {k}: results_collection disagrees with CSV on {sorted(diff)}")
                    print(f"  original trial{k}: {len(ref)} rows in CSV agree with results_collection ({name})")
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
