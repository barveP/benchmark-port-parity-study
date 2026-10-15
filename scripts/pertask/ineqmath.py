"""Per-task outcomes for the IneqMath parity experiment (HF adapters/ineqmath).

Usage: python -I ineqmath.py <download_dir> <out_dir>
<download_dir> is the local mirror of adapters/ineqmath/ (results_collection/).
Stdlib only; nothing in <download_dir> is executed. Experiment: agent codex@0.77.0, model gpt-4o-mini (2024-07-18),
100 tasks (IneqMath dev subset) x 3 trials per side.

Harbor side: results_collection/result_harbor_trial<k>.json is a Harbor job-level
result.json: stats.evals["codex__gpt-4o-mini__ineqmath"].reward_stats.reward =
{"0.0": [ids], "1.0": [ids]}, one file per run (k = 1, 2, 3). Ids are Harbor trial
names "<data_id>__<7-char suffix>", e.g. "61__KJBSvqa"; the suffix after "__" is
stripped, so task_id = the IneqMath dev data_id "0".."99".

Original side: results_collection/result_original_trial<k>.json is a JSON list whose
item 0 is the aggregate scores.json block ({"dev": {"all": {"total", "correct",
"wrong", "accuracy", ...}}}) and items 1..100 are the per-problem records of the
original pipeline's results.json (data_id, problem, answer, type, prompt, response,
success, error). "success"/"error" only say whether a response was obtained (all
True / None); there is no per-task correctness field, and the LLM-judge verdicts
were not uploaded (original_parity/<trial>/raw/<id>.json and .md carry the same
fields; scores.json is the aggregate). So no original.csv is written: the script
only prints the aggregate correct counts. It aborts if a verdict-like field appears,
so that a later upload with per-task verdicts is noticed rather than silently ignored.

Outputs <out_dir>/harbor.csv with columns run,task_id,reward (run = trial number).
"""
import csv
import json
import os
import sys

RUNS = (1, 2, 3)
VERDICT_KEYS = {"correct", "is_correct", "judge", "judgement", "judgment", "score",
                "reward", "label", "result", "extracted_answer", "pred", "prediction"}


def harbor_rewards(path):
    """Return (eval name, {task_id: reward}) from a Harbor job-level result.json."""
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
            tid = tid.split("__", 1)[0]  # drop the Harbor trial suffix
            if tid in out:
                sys.exit(f"{path}: duplicate task id {tid}")
            out[tid] = r
    if len(out) != ev["n_trials"]:
        print(f"  WARNING {os.path.basename(path)}: {len(out)} ids vs n_trials={ev['n_trials']}")
    return name, out


def original_check(path):
    """Report the aggregate block and confirm the records carry no per-task verdict."""
    with open(path) as f:
        data = json.load(f)
    agg, recs = data[0]["dev"]["all"], data[1:]
    found = sorted({k for r in recs for k in r} & VERDICT_KEYS)
    if found:
        sys.exit(f"{path}: per-task verdict field(s) {found} present; "
                 "per-task scoring is not implemented for this layout")
    n_resp = sum(1 for r in recs if r.get("success") and r.get("response"))
    ids = [r["data_id"] for r in recs]
    print(f"  {os.path.basename(path)}: {len(recs)} records ({len(set(ids))} unique data_id), "
          f"{n_resp} with a response, aggregate correct={agg['correct']}/{agg['total']} "
          f"({agg['accuracy']}%), no per-task verdict field")


def write_csv(path, rows):
    def key(x):
        return (x[0], (0, int(x[1])) if x[1].isdigit() else (1, x[1]))
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["run", "task_id", "reward"])
        for run, tid, r in sorted(rows, key=key):
            w.writerow([run, tid, int(r) if r.is_integer() else r])
    by_run = {}
    for run, _, r in rows:
        by_run.setdefault(run, []).append(r)
    print(f"{os.path.basename(path)}: {len(rows)} rows, run means % = " + ", ".join(
        f"run{k}: {100 * sum(v) / len(v):.2f} (n={len(v)})" for k, v in sorted(by_run.items())))


def main(dl, out):
    os.makedirs(out, exist_ok=True)
    rc = os.path.join(dl, "results_collection")
    for k in RUNS:
        p = os.path.join(rc, f"result_original_trial{k}.json")
        if os.path.exists(p):
            original_check(p)
        else:
            print(f"  WARNING missing {p}")
    print("original: aggregate only; nothing written")
    rows, ids_by_run = [], {}
    for k in RUNS:
        p = os.path.join(rc, f"result_harbor_trial{k}.json")
        if not os.path.exists(p):
            print(f"  WARNING missing {p}")
            continue
        name, rewards = harbor_rewards(p)
        print(f"  harbor trial{k}: {len(rewards)} tasks from eval {name}")
        ids_by_run[k] = set(rewards)
        rows += [(k, t, r) for t, r in rewards.items()]
    if not rows:
        print("harbor: no per-task data; nothing written")
        return
    if len(set(map(frozenset, ids_by_run.values()))) != 1:
        print("  WARNING harbor: task sets differ across runs")
    write_csv(os.path.join(out, "harbor.csv"), rows)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
