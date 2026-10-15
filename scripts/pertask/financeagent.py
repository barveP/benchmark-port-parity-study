"""Per-task outcomes for the FinanceAgent parity experiment (HF adapters/financeagent).

Usage: python -I financeagent.py <download_dir> <out_dir>
<download_dir> mirrors adapters/financeagent/: results_collection/ plus
harbor_parity/trial1/<task>__<suffix>/verifier/judgment.json for the 50 tasks.
Stdlib only; nothing in <download_dir> is executed.

Harbor side (results_collection/result_harbor_trial<k>.json, one per run): a Harbor
job-level result.json; stats.evals[<name>].reward_stats.reward maps a reward value
("0.0" / "1.0") to a list of trial names "<task>__<suffix>" ("financeagent-0__o7jR57x").
The suffix after "__" is stripped, so task_id = "financeagent-<n>", n = 0..49.

Original side (results_collection/result_original_trial<k>.json, one per run):
{"summary": {total, correct, incorrect, accuracy},
 "details": [{question, ground_truth, prediction, judgment, explanation}, ...]}
reward = 1 if judgment == "CORRECT" else 0 (the only other value is "INCORRECT").
These files carry no task identifier, and the question order differs between runs,
so every row is given the Harbor task whose verifier/judgment.json "question" equals
its "question" after collapsing whitespace and lowercasing (runs differ by trailing
spaces). A question that appears twice in one run keeps its first occurrence and is
reported; the per-run means printed here count distinct tasks only.

Output: <out_dir>/original.csv and harbor.csv with columns run,task_id,reward.
"""
import csv
import glob
import json
import os
import re
import sys

RUNS = (1, 2, 3)


def norm(q):
    return re.sub(r"\s+", " ", q).strip().lower()


def task_num(tid):
    return int(tid.rsplit("-", 1)[1])


def write_csv(path, rows):
    rows = sorted(rows, key=lambda x: (x[0], task_num(x[1])))
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["run", "task_id", "reward"])
        w.writerows(rows)
    by_run = {}
    for run, _, r in rows:
        by_run.setdefault(run, []).append(r)
    print(f"{os.path.basename(path)}: {len(rows)} rows, run means % = "
          + ", ".join(f"run{k}: {100 * sum(v) / len(v):.2f} (n={len(v)})"
                      for k, v in sorted(by_run.items())))


def question_map(dl):
    """normalized question -> Harbor task name, from the Harbor verifier judgments."""
    m = {}
    pattern = os.path.join(dl, "harbor_parity", "trial*", "*__*", "verifier", "judgment.json")
    for p in sorted(glob.glob(pattern)):
        task = p.split(os.sep)[-3].split("__", 1)[0]
        with open(p) as f:
            q = norm(json.load(f)["question"])
        if m.get(q, task) != task:
            print(f"  WARNING question of {task} also belongs to {m[q]}")
        m[q] = task
    print(f"question map: {len(m)} questions -> {len(set(m.values()))} Harbor tasks")
    return m


def harbor_rows(rc, run):
    p = os.path.join(rc, f"result_harbor_trial{run}.json")
    if not os.path.exists(p):
        return None
    with open(p) as f:
        evals = json.load(f)["stats"]["evals"]
    if len(evals) != 1:
        print(f"  WARNING run{run}: {len(evals)} evals in the Harbor result")
    rows = []
    for ev in evals.values():
        for reward, names in ev["reward_stats"]["reward"].items():
            rows += [(run, n.split("__", 1)[0], int(float(reward))) for n in names]
    tasks = [t for _, t, _ in rows]
    if len(tasks) != len(set(tasks)):
        print(f"  WARNING run{run}: duplicated Harbor task ids")
    return rows


def original_rows(rc, run, qmap):
    p = os.path.join(rc, f"result_original_trial{run}.json")
    if not os.path.exists(p):
        return None
    with open(p) as f:
        d = json.load(f)
    rows, seen = [], {}
    for x in d["details"]:
        task = qmap.get(norm(x["question"]))
        if task is None:
            print(f"  WARNING run{run}: no Harbor task for {x['question'][:60]!r}; skipped")
            continue
        if x["judgment"] not in ("CORRECT", "INCORRECT"):
            print(f"  WARNING run{run} {task}: judgment {x['judgment']!r} treated as 0")
        r = 1 if x["judgment"] == "CORRECT" else 0
        if task in seen:
            print(f"  note: run{run} {task} appears twice (rewards {seen[task]}, {r}); "
                  "first kept")
            continue
        seen[task] = r
        rows.append((run, task, r))
    s = d["summary"]
    n_correct = sum(1 for x in d["details"] if x["judgment"] == "CORRECT")
    if (s["total"], s["correct"]) != (len(d["details"]), n_correct):
        print(f"  WARNING run{run}: summary {s} vs counted {n_correct}/{len(d['details'])}")
    print(f"  run{run}: published summary accuracy {s['accuracy']} over {s['total']} rows; "
          f"{len(rows)} distinct tasks")
    return rows


def main(dl, out):
    rc = os.path.join(dl, "results_collection")
    os.makedirs(out, exist_ok=True)
    qmap = question_map(dl)
    tasks = set(qmap.values())
    for side, fn in (("harbor", lambda run: harbor_rows(rc, run)),
                     ("original", lambda run: original_rows(rc, run, qmap))):
        rows = []
        for run in RUNS:
            r = fn(run)
            if r is None:
                print(f"  no {side} file for run{run}")
                continue
            rows += r
            missing = sorted(tasks - {t for _, t, _ in r}, key=task_num)
            extra = sorted({t for _, t, _ in r} - tasks, key=task_num)
            if missing or extra:
                print(f"  note: {side} run{run} missing {missing}, unknown {extra}")
        if rows:
            write_csv(os.path.join(out, f"{side}.csv"), rows)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
