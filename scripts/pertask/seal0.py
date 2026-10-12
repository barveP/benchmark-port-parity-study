"""Per-task outcomes for the seal0 (SealQA seal_0) parity experiment (stdlib only).

Usage:  python -I seal0.py <download_dir> <out_dir>

<download_dir> mirrors adapters/seal0/ of the Hugging Face dataset
harborframework/parity-experiments; only results_collection/ is read.
Experiment: claude-code (2.1.81 / 2.1.86) with claude-haiku-4-5, 3 runs a side.

Harbor side -- results_collection/result_harbor_trial<N>.json, one Harbor
job-level result.json per run.  Per-task rewards live in
    stats.evals[<eval name>].reward_stats.reward = {"<reward>": [trial names]}
with binary rewards "1.0"/"0.0".  Trial names look like "61__m3swGMn" =
<task name>__<7-char trial suffix>; the "__<suffix>" is stripped, so task_id is
the Harbor task name "61", i.e. the 0-based index of the question in the
seal_0 subset (datasets/seal0/<N>).  Tasks that errored (exception_stats) have
no reward entry and are not written; they are listed on stdout.  A task that
timed out but still got a 0.0 reward is kept.  run = N from the file name.
Output: harbor.csv.

Original side -- results_collection/result_original_trial<N>.json are the
original harness's scored_results.json:
    {"accuracy", "correct", "total",
     "results": [{"idx", "question", "expected", "predicted",
                  "correct": bool, "judge", "verdict"}, ...]}
task_id = str(idx) (0-based question index, same numbering as the Harbor task
names; verified on task 0 via the Harbor verifier's "Expected:" line), reward =
1.0 if correct else 0.0.  run = N from the file name.  Output: original.csv.
"""
import csv
import json
import os
import re
import sys

TRIAL_SUFFIX = re.compile(r"__[A-Za-z0-9]+$")


def harbor_rows(path, run):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    rows, errored = [], []
    for ev in data["stats"]["evals"].values():
        for reward, names in ev["reward_stats"]["reward"].items():
            for name in names:
                rows.append((run, TRIAL_SUFFIX.sub("", name), float(reward)))
        for exc, names in ev.get("exception_stats", {}).items():
            errored += [(TRIAL_SUFFIX.sub("", n), exc) for n in names]
    scored = {t for _, t, _ in rows}
    dropped = [(t, e) for t, e in errored if t not in scored]
    if dropped:
        print(f"harbor run {run}: errored, no reward, excluded: {dropped}")
    return rows


def original_rows(path, run):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    rows = [(run, str(r["idx"]), 1.0 if r["correct"] is True else 0.0)
            for r in data["results"]]
    print(f"original run {run}: file says correct={data['correct']}/{data['total']} "
          f"accuracy={data['accuracy']:.4f}")
    return rows


def write_csv(rows, path, label):
    keys = [(r, t) for r, t, _ in rows]
    assert len(keys) == len(set(keys)), f"duplicate (run, task_id) on {label} side"
    rows.sort(key=lambda r: (r[0], int(r[1])))
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["run", "task_id", "reward"])
        w.writerows(rows)
    for run in sorted({r for r, _, _ in rows}):
        vals = [x for rr, _, x in rows if rr == run]
        print(f"{label} run {run}: n_tasks={len(vals)} mean={sum(vals) / len(vals):.4f}")


def main(download_dir, out_dir):
    rc = os.path.join(download_dir, "results_collection")
    os.makedirs(out_dir, exist_ok=True)
    harbor, original = [], []
    for fn in sorted(os.listdir(rc)):
        m = re.fullmatch(r"result_(harbor|original)_trial(\d+)\.json", fn)
        if not m:
            continue
        side, run = m.group(1), int(m.group(2))
        if side == "harbor":
            harbor += harbor_rows(os.path.join(rc, fn), run)
        else:
            original += original_rows(os.path.join(rc, fn), run)
    if harbor:
        write_csv(harbor, os.path.join(out_dir, "harbor.csv"), "harbor")
    if original:
        write_csv(original, os.path.join(out_dir, "original.csv"), "original")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
