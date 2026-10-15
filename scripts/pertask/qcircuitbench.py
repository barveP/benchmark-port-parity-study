"""Per-task outcomes for the QCircuitBench parity experiment (HF adapters/qcircuitbench).

Usage: python -I qcircuitbench.py <download_dir> <out_dir>
<download_dir> is the local mirror of adapters/qcircuitbench/ (only
results_collection/ is read). Stdlib only.
Experiment: agent codex@0.76.0, model gpt-5.2, 28 tasks x 3 trials per side.

Both sides use the Harbor job-level result.json layout:
results_collection/result_{original,harbor}_trial<k>.json ->
stats.evals["codex__qcircuitbench"].reward_stats.reward = {"<reward>": [ids...]},
one file per run (k = 1, 2, 3). Rewards are fractional in [0, 1] ("Mean Semantic
Score": 1.0 for full success, proportional partial credit otherwise).

Task ids. The original files list the bare algorithm name, e.g. "clifford_2".
The Harbor files list Harbor trial names "<task name>__<7-char suffix>" where the
task name is "<algorithm>-n<qubits>" (e.g. "clifford_2-n5") truncated to 32
characters, so "generalized_simon_multi_oracle-n" and
"generalized_simon_ternary_oracle" appear without (part of) the qubit tail. To
give both sides the same key, Harbor ids are reduced to the algorithm name: the
"__<suffix>" is stripped, then a trailing "-n<digits>" (digits possibly empty)
is removed. The resulting 28 names are checked to equal the original side's set.

Caveats recorded by the parser (printed as warnings, not corrected):
- result_original_trial2.json lists only 26 ids (phase_estimation and qae are
  absent) although n_trials says 28; those two tasks get no row for run 2.
- The stored metrics[0].mean of original trials 2 and 3 does not equal the mean
  of the listed rewards (0.6433 vs 0.6378; 0.6233 vs 0.6240).
- Harbor trial 2 has one AgentTimeoutError (phase_estimation-n8); it is listed
  with reward 0.0 and kept as such.
- original_parity/result_original_trial2/<task>/metrics.json (result_score) is
  NOT used: it disagrees with the summary on six tasks and its mean (0.610 over
  27 scored tasks) reproduces neither the stored nor the published run score.

Outputs <out_dir>/original.csv and <out_dir>/harbor.csv with columns
run,task_id,reward (run = trial number from the file name).
"""
import csv
import json
import os
import re
import sys

RUNS = (1, 2, 3)
EVAL = "codex__qcircuitbench"


def harbor_task_id(trial_name):
    """'clifford_2-n5__EMHMb7e' -> 'clifford_2'; 'generalized_simon_multi_oracle-n__x' -> '...oracle'."""
    return re.sub(r"-n\d*$", "", trial_name.split("__", 1)[0])


def read_rewards(path, normalize):
    """Return {task_id: reward} from a Harbor-style job result.json."""
    with open(path) as f:
        evals = json.load(f)["stats"]["evals"]
    if list(evals) != [EVAL]:
        sys.exit(f"{path}: expected eval {EVAL!r}, found {list(evals)}")
    ev = evals[EVAL]
    out = {}
    for reward, ids in ev["reward_stats"]["reward"].items():
        r = float(reward)
        if not 0.0 <= r <= 1.0:
            sys.exit(f"{path}: reward {r} outside [0, 1]")
        for tid in ids:
            tid = normalize(tid)
            if tid in out:
                sys.exit(f"{path}: duplicate task id {tid}")
            out[tid] = r
    name = os.path.basename(path)
    if len(out) != ev["n_trials"]:
        print(f"  WARNING {name}: {len(out)} ids listed vs n_trials={ev['n_trials']}")
    if ev.get("n_errors"):
        print(f"  WARNING {name}: n_errors={ev['n_errors']} {ev.get('exception_stats')}")
    stored = ev["metrics"][0]["mean"]
    listed = sum(out.values()) / len(out)
    if abs(stored - listed) > 1e-9:
        print(f"  WARNING {name}: stored mean {stored:.5f} != mean of listed rewards {listed:.5f}")
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
    rc = os.path.join(dl, "results_collection")
    tasks = {}
    for side, normalize in (("original", str), ("harbor", harbor_task_id)):
        rows = []
        for k in RUNS:
            path = os.path.join(rc, f"result_{side}_trial{k}.json")
            per_task = read_rewards(path, normalize)
            tasks.setdefault(side, set()).update(per_task)
            rows += [(k, tid, r) for tid, r in per_task.items()]
        write_csv(os.path.join(out, f"{side}.csv"), rows)
    if tasks["original"] != tasks["harbor"]:
        sys.exit(f"task id sets differ: {tasks['original'] ^ tasks['harbor']}")
    print(f"{len(tasks['original'])} task ids common to both sides")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__.strip().splitlines()[2])
    main(sys.argv[1], sys.argv[2])
