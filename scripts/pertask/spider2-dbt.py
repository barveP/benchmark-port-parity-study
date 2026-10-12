"""Per-task outcomes for the spider2-dbt Harbor parity experiment (stdlib only).

Usage:  python -I spider2-dbt.py <download_dir> <out_dir>

<download_dir> mirrors adapters/spider2-dbt/ of the Hugging Face dataset
harborframework/parity-experiments: results_collection/ (both sides) plus
original_parity/gpt-5-mini-trial<N>/results_metadata.jsonl (task universe).

Harbor side -- results_collection/result_harbor_trial<N>.json: Harbor
job-level result.json, per-task rewards in
    stats.evals[<eval name>].reward_stats.reward = {"1.0": [...], "0.0": [...]}
(the eval name is "spider-agent-dbt__spider2" in trial 1 and
"spider-agent-dbt__spider2-dbt" in trials 2-3; every eval is read).  Trial
names look like "airport001__DLBm4i5"; the trailing "__<suffix>" is stripped,
so task_id = "airport001" (the Spider2-DBT instance_id).  64 tasks per run,
run = N from the file name.  Output: harbor.csv.

Original side -- results_collection/result_original_test<N>.log: console
capture of the upstream Spider2 evaluate.py run (a tqdm progress bar, one
printed {'instance_id': ...} dict per PASSED instance, then the passed
instance_ids one per line, then a final "<accuracy> <n_passed> <n_total>"
line such as "0.1764... 12 68").  Only passes are listed, so the task universe
comes from original_parity/gpt-5-mini-trial<N>/results_metadata.jsonl (one
{"instance_id": ...} record per evaluated instance, 68 per trial); reward = 1
if the instance_id is in the log's passed list, else 0.  The 4 instances the
Harbor port excluded (upstream data bugs) are dropped so both sides cover the
same 64 tasks; they are named on stderr (none of them ever passed).
Output: original.csv.
"""
import csv
import json
import os
import re
import sys

TRIAL_SUFFIX = re.compile(r"__[A-Za-z0-9]+$")
SUMMARY = re.compile(r"([0-9.]+)\s+(\d+)\s+(\d+)")
INSTANCE = re.compile(r"'instance_id': '([^']+)'")


def harbor_rows(path, run):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    rows = []
    for ev in data["stats"]["evals"].values():
        for reward, names in ev["reward_stats"]["reward"].items():
            for name in names:
                rows.append((run, TRIAL_SUFFIX.sub("", name), float(reward)))
    return rows


def passed_ids(log_path):
    """(passed instance_ids, n_total) from the tail of an evaluate.py log."""
    with open(log_path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    lines = [ln.strip() for ln in re.split(r"[\r\n]+", text) if ln.strip()]
    for i in range(len(lines) - 1, -1, -1):
        m = SUMMARY.fullmatch(lines[i])
        if m:
            break
    else:
        raise ValueError(f"no '<acc> <n_pass> <n_total>' line in {log_path}")
    n_pass, n_total = int(m.group(2)), int(m.group(3))
    passed = lines[i - n_pass:i]
    assert set(passed) == set(INSTANCE.findall(text)), "passed list != printed dicts"
    return passed, n_total


def universe(download_dir, run):
    path = os.path.join(download_dir, "original_parity",
                        f"gpt-5-mini-trial{run}", "results_metadata.jsonl")
    with open(path, encoding="utf-8") as fh:
        return [json.loads(ln)["instance_id"] for ln in fh if ln.strip()]


def write(out_dir, name, rows):
    keys = [(r, t) for r, t, _ in rows]
    assert len(keys) == len(set(keys)), f"duplicate (run, task_id) in {name}"
    rows.sort()
    with open(os.path.join(out_dir, name), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["run", "task_id", "reward"])
        w.writerows(rows)
    for r in sorted({r for r, _, _ in rows}):
        vals = [x for rr, _, x in rows if rr == r]
        print(f"{name} run {r}: n_tasks={len(vals)} mean={sum(vals)/len(vals):.4f}")


def main(download_dir, out_dir):
    rc = os.path.join(download_dir, "results_collection")
    os.makedirs(out_dir, exist_ok=True)
    harbor, original = [], []
    for fn in sorted(os.listdir(rc)):
        m = re.fullmatch(r"result_harbor_trial(\d+)\.json", fn)
        if m:
            harbor += harbor_rows(os.path.join(rc, fn), int(m.group(1)))
    harbor_tasks = {t for _, t, _ in harbor}
    for fn in sorted(os.listdir(rc)):
        m = re.fullmatch(r"result_original_test(\d+)\.log", fn)
        if not m:
            continue
        run = int(m.group(1))
        passed, n_total = passed_ids(os.path.join(rc, fn))
        tasks = universe(download_dir, run)
        assert len(tasks) == n_total and set(passed) <= set(tasks)
        keep = harbor_tasks or set(tasks)
        dropped = sorted(set(tasks) - keep)
        print(f"original run {run}: {len(passed)}/{n_total} passed in log; "
              f"dropping {len(dropped)} tasks absent from Harbor set: {dropped}",
              file=sys.stderr)
        original += [(run, t, float(t in passed)) for t in tasks if t in keep]
    if harbor:
        write(out_dir, "harbor.csv", harbor)
    if original:
        write(out_dir, "original.csv", original)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
