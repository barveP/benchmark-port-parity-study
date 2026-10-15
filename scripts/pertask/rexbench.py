"""Per-task outcomes for the RExBench Harbor parity experiment (stdlib only).

Usage:  python -I rexbench.py <download_dir> <out_dir>

<download_dir> mirrors adapters/rexbench/ of the Hugging Face dataset
harborframework/parity-experiments; only results_collection/ is read.
Experiment: OpenHands@1.4.0 + anthropic/claude-sonnet-4-5, 3 runs x 12 tasks,
metric "Final Success Rate" (Harbor: pass rate), BINARY rewards 0/1.

Original side, results_collection/result_original_trial<N>.json (the RExBench
evaluator's own output):
    {"tasks": {<task>: {"default": {"success": bool, "details": {...}}}},
     "summary": {"overall": {"default": {"success_rate", "success_count",
                                         "total_tasks"}}}}
reward = 1.0 if success else 0.0; task_id = the "tasks" key verbatim
("cogs", "othello", "entity-tracking-multimodal", ...).

Harbor side, results_collection/result_harbor_trial<N>.json = Harbor job-level
result.json:
    stats.evals[<name>].reward_stats.reward = {"<reward>": [trial names]}
Trial names are "rexbench-<task name truncated to 32 chars>__<7-char suffix>".
To join with the original side the "__<suffix>" is stripped, then the
"rexbench-" prefix, and a name that is not an original task id is restored by
unique-prefix match against the original id list (this affects exactly one
task: "rexbench-entity-tracking-multimo" -> "entity-tracking-multimodal").
No exception_stats entries exist; every trial has a reward.  run = N from
the file name (matches the published harbor_runs order 16.67/58.33/50.00).

Output: <out_dir>/original.csv and <out_dir>/harbor.csv (run,task_id,reward).
Each file is checked against its own embedded mean (summary success_rate / 100
on the original side, metrics[0].mean on the Harbor side).
"""
import csv
import json
import os
import re
import sys

TRIAL_SUFFIX = re.compile(r"__[A-Za-z0-9]+$")
PREFIX = "rexbench-"


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def original_rows(path, run):
    data = load(path)
    rows = [(run, task, 1.0 if entry["default"]["success"] else 0.0)
            for task, entry in data["tasks"].items()]
    summ = data["summary"]["overall"]["default"]
    assert len(rows) == summ["total_tasks"], (path, len(rows))
    assert sum(r for _, _, r in rows) == summ["success_count"], path
    assert abs(sum(r for _, _, r in rows) / len(rows)
               - summ["success_rate"] / 100) < 1e-9, path
    return rows


def restore(name, task_ids):
    """Map a suffix-stripped, de-prefixed Harbor trial name to an original id."""
    if name in task_ids:
        return name
    hits = [t for t in task_ids if t.startswith(name)]
    assert len(hits) == 1, f"ambiguous or unknown truncated name {name!r}: {hits}"
    print(f"  note: restored truncated Harbor name {name!r} -> {hits[0]!r}")
    return hits[0]


def harbor_rows(path, run, task_ids):
    data = load(path)
    rows = []
    for ev in data["stats"]["evals"].values():
        assert not ev.get("exception_stats"), (path, ev.get("exception_stats"))
        for reward, names in ev["reward_stats"]["reward"].items():
            for name in names:
                name = TRIAL_SUFFIX.sub("", name)
                assert name.startswith(PREFIX), name
                rows.append((run, restore(name[len(PREFIX):], task_ids),
                             float(reward)))
        published = ev["metrics"][0]["mean"]
    assert len(rows) == data["n_total_trials"], (path, len(rows))
    assert abs(sum(r for _, _, r in rows) / len(rows) - published) < 1e-9, path
    return rows


def write_csv(path, rows):
    keys = [(r, t) for r, t, _ in rows]
    assert len(keys) == len(set(keys)), "duplicate (run, task_id)"
    assert all(r in (0.0, 1.0) for _, _, r in rows), "non-binary reward"
    rows.sort()
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["run", "task_id", "reward"])
        w.writerows(rows)


def main(download_dir, out_dir):
    rc = os.path.join(download_dir, "results_collection")
    os.makedirs(out_dir, exist_ok=True)
    files = {"original": {}, "harbor": {}}
    for fn in sorted(os.listdir(rc)):
        m = re.fullmatch(r"result_(original|harbor)_trial(\d+)\.json", fn)
        if m:
            files[m.group(1)][int(m.group(2))] = os.path.join(rc, fn)

    sides = {"original": [], "harbor": []}
    for run, path in sorted(files["original"].items()):
        sides["original"] += original_rows(path, run)
    task_ids = sorted({t for _, t, _ in sides["original"]})
    for run, path in sorted(files["harbor"].items()):
        sides["harbor"] += harbor_rows(path, run, task_ids)

    for side, rows in sides.items():
        for run in sorted({r for r, _, _ in rows}):
            vals = [x for r, _, x in rows if r == run]
            print(f"{side} run {run}: n_tasks={len(vals)} "
                  f"mean={100 * sum(vals) / len(vals):.2f}%")
    tasks = {s: {t for _, t, _ in rows} for s, rows in sides.items()}
    assert tasks["original"] == tasks["harbor"], "task ids differ across sides"
    print(f"tasks in common: {len(tasks['original'])}")
    for side, rows in sides.items():
        if rows:
            write_csv(os.path.join(out_dir, f"{side}.csv"), rows)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
