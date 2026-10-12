"""Per-task outcomes for the bird-bench Harbor parity experiment (stdlib only).

Usage:  python -I bird_bench.py <download_dir> <out_dir>

<download_dir> mirrors adapters/bird-bench/ of the Hugging Face dataset
harborframework/parity-experiments (only results_collection/ is needed).

Harbor side -- results_collection/result_harbor_trial<N>.json, one Harbor
job-level result.json per run.  Per-task rewards live in
    stats.evals[<eval name>].reward_stats.reward = {"<reward>": [trial names]}
with binary rewards "1.0"/"0.0".  Trial names look like
"california_schools__13__tZshwqB" = <db_id>__<question_id>__<7-char trial
suffix>; the trailing "__<suffix>" is stripped, so task_id =
"california_schools__13" (the Harbor task name; question_id is the BIRD dev
question index).  run = N from the file name.  Output: harbor.csv.

Original side -- results_collection/result_original_trial<N>.json are byte
copies of original_parity/gpt-5-mini-trial<N>/predict_dev.json: BIRD prediction
files {"<subset index 0..149>": "<predicted SQL>\\t----- bird -----\\t<db_id>"}.
They hold predictions only, no correctness; the only outcome data on that side
is the aggregate accuracy table in original_parity/*/result.txt.  No
original.csv is written; the script just reports what it saw.
"""
import csv
import json
import os
import re
import sys

TRIAL_SUFFIX = re.compile(r"__[A-Za-z0-9]+$")
BIRD_SEP = "\t----- bird -----\t"


def harbor_rows(path, run):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    rows = []
    for ev in data["stats"]["evals"].values():
        for reward, names in ev["reward_stats"]["reward"].items():
            for name in names:
                rows.append((run, TRIAL_SUFFIX.sub("", name), float(reward)))
    return rows


def main(download_dir, out_dir):
    rc = os.path.join(download_dir, "results_collection")
    os.makedirs(out_dir, exist_ok=True)
    harbor, originals = [], []
    for fn in sorted(os.listdir(rc)):
        m = re.fullmatch(r"result_(harbor|original)_trial(\d+)\.json", fn)
        if not m:
            continue
        side, run = m.group(1), int(m.group(2))
        if side == "harbor":
            harbor += harbor_rows(os.path.join(rc, fn), run)
        else:
            originals.append((fn, run))

    keys = [(r, t) for r, t, _ in harbor]
    assert len(keys) == len(set(keys)), "duplicate (run, task_id) on harbor side"
    harbor.sort()
    with open(os.path.join(out_dir, "harbor.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["run", "task_id", "reward"])
        w.writerows(harbor)
    runs = sorted({r for r, _, _ in harbor})
    for r in runs:
        vals = [x for rr, _, x in harbor if rr == r]
        print(f"harbor run {r}: n_tasks={len(vals)} mean={sum(vals)/len(vals):.4f}")

    for fn, run in originals:
        with open(os.path.join(rc, fn), encoding="utf-8") as fh:
            d = json.load(fh)
        is_pred = isinstance(d, dict) and d and all(
            isinstance(v, str) and BIRD_SEP in v for v in d.values())
        kind = "BIRD predict_dev.json (SQL predictions, no outcomes)" if is_pred else "UNRECOGNISED"
        print(f"original run {run}: {fn} -> {kind}, {len(d)} entries; no original.csv written")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
