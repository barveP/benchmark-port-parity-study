"""Per-task outcomes for the dacode Harbor parity experiment (stdlib only).

Usage:  python -I dacode.py <download_dir> <out_dir>

<download_dir> mirrors adapters/dacode/ of the Hugging Face dataset
harborframework/parity-experiments (only results_collection/ is needed).

Both sides are Harbor job-level result.json files, one per run:
    results_collection/result_harbor_trial<N>.json
    results_collection/result_original_trial<N>.json
(the original DA-Agent runs were converted to this format upstream with the
da-code repo's scripts/convert_results.py; see the adapter's README on Hugging
Face).  Per-task rewards live in
    stats.evals[<eval name>].reward_stats.reward = {"<reward>": [trial names]}
with FRACTIONAL rewards in [0, 1] (DA-Code's per-task score).  Trials that
raised an exception (Harbor: RewardFileNotFoundError; original:
AgentDidNotFinish) are absent from reward_stats and listed only under
    stats.evals[<eval name>].exception_stats = {"<ExcName>": [trial names]};
they are recorded here with reward 0.0, which is what reproduces the
published run means (stats.evals[..].metrics[0].mean, averaged over all
n_total_trials = 479).  A trial that appears in BOTH places (one
AgentTimeoutError trial in harbor run 2 still produced a reward) keeps its
scored reward; the exception entry is ignored.

Trial names look like "dacode-data-sa-001__BnytvKz" = <task name>__<trial
suffix> (the original side uses the constant suffix "__aBaCada"); the
trailing "__<suffix>" is stripped, so task_id = "dacode-data-sa-001".
run = N from the file name.  Output: original.csv and harbor.csv.
"""
import csv
import json
import os
import re
import sys

TRIAL_SUFFIX = re.compile(r"__[A-Za-z0-9]+$")


def rows_from_result(path, run):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    rows, n_exc = [], 0
    for ev in data["stats"]["evals"].values():
        scored = set()
        for reward, names in ev["reward_stats"]["reward"].items():
            for name in names:
                rows.append((run, TRIAL_SUFFIX.sub("", name), float(reward)))
                scored.add(name)
        for exc, names in ev.get("exception_stats", {}).items():
            for name in names:
                if name in scored:
                    print(f"  note: {name} is scored and also listed under "
                          f"{exc}; keeping its scored reward")
                    continue
                rows.append((run, TRIAL_SUFFIX.sub("", name), 0.0))
                n_exc += 1
    assert len(rows) == data["n_total_trials"], (path, len(rows))
    return rows, n_exc


def write_csv(path, rows):
    keys = [(r, t) for r, t, _ in rows]
    assert len(keys) == len(set(keys)), "duplicate (run, task_id)"
    rows.sort()
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["run", "task_id", "reward"])
        w.writerows(rows)


def main(download_dir, out_dir):
    rc = os.path.join(download_dir, "results_collection")
    os.makedirs(out_dir, exist_ok=True)
    sides = {"harbor": [], "original": []}
    for fn in sorted(os.listdir(rc)):
        m = re.fullmatch(r"result_(harbor|original)_trial(\d+)\.json", fn)
        if not m:
            continue
        side, run = m.group(1), int(m.group(2))
        rows, n_exc = rows_from_result(os.path.join(rc, fn), run)
        vals = [x for _, _, x in rows]
        print(f"{side} run {run}: n_tasks={len(vals)} n_exception(->0.0)={n_exc} "
              f"mean={sum(vals) / len(vals):.6f}")
        sides[side] += rows
    for side, rows in sides.items():
        if rows:
            write_csv(os.path.join(out_dir, f"{side}.csv"), rows)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
