"""Per-task outcomes for the MedAgentBench Harbor parity experiment (stdlib only).

Usage:  python -I medagentbench.py <download_dir> <out_dir>

<download_dir> mirrors adapters/medagentbench/ of the Hugging Face dataset
harborframework/parity-experiments (only results_collection/ is needed).
Experiment: medagentbench-parity-agent@1.0.0 + openai/gpt-4o-mini, 3 runs x
300 tasks, metric "Success Rate", BINARY rewards (1 = completedCorrect).

Harbor side: results_collection/result_harbor_trial<N>.json, a Harbor
job-level result.json.  Per-task rewards live in
    stats.evals[<eval name>].reward_stats.reward = {"<reward>": [trial names]}
Trial names carry a 7-character suffix ("task7_14__d2JUKUm"), which is
stripped (regex "__[A-Za-z0-9]+$") to give task_id = "task<C>_<M>".
result_harbor_terminus2_trial1.json (Terminus-2 agent, one run, 49.00%) is a
different experiment that is not in the snapshot and is deliberately skipped.

Original side: results_collection/result_original_trial<N>.json, the official
MedAgentBench overall.json: custom["raw_results"] is a list of 300 entries
{index, status, result, history}; reward = 1.0 iff status == "completedCorrect"
(custom["success rate"] is the mean of that).  Entries carry only a positional
"index" (0..299) into the official test_data_v2.json, whose ids are ordered
task1_1..task1_30, task2_1..task2_30, ..., task10_1..task10_30, so
    task_id = "task{index // 30 + 1}_{index % 30 + 1}".
This mapping was checked before use: each block of 30 indices holds one
question template, the ten templates are the MedAgentBench task categories
1..10 in order, and under this mapping per-task agreement with the Harbor side
(0.97-0.99) equals the run-to-run agreement within either side (a
within-category shuffle gives ~0.83).  run = N from the file name.
Output: <out_dir>/original.csv and <out_dir>/harbor.csv (run,task_id,reward).
"""
import csv
import json
import os
import re
import sys

TRIAL_SUFFIX = re.compile(r"__[A-Za-z0-9]+$")
TASK_ID = re.compile(r"task(\d+)_(\d+)")


def harbor_rows(path, run):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    rows = []
    for ev in data["stats"]["evals"].values():
        for reward, names in ev["reward_stats"]["reward"].items():
            rows += [(run, TRIAL_SUFFIX.sub("", n), float(reward)) for n in names]
        assert not ev.get("exception_stats"), (path, ev["exception_stats"])
        published = ev["metrics"][0]["mean"]
    assert len(rows) == data["n_total_trials"] == 300, (path, len(rows))
    assert abs(sum(r for _, _, r in rows) / len(rows) - published) < 1e-9, path
    return rows


def original_rows(path, run):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    entries = data["custom"]["raw_results"]
    assert sorted(e["index"] for e in entries) == list(range(300)), path
    assert {e["status"] for e in entries} <= {"completedCorrect",
                                              "completedIncorrect"}, path
    rows = [(run, f"task{e['index'] // 30 + 1}_{e['index'] % 30 + 1}",
             float(e["status"] == "completedCorrect")) for e in entries]
    published = data["custom"]["success rate"]
    assert abs(sum(r for _, _, r in rows) / len(rows) - published) < 1e-9, path
    return rows


def write_csv(path, rows):
    keys = [(r, t) for r, t, _ in rows]
    assert len(keys) == len(set(keys)), "duplicate (run, task_id)"
    rows.sort(key=lambda r: (r[0],) + tuple(map(int, TASK_ID.match(r[1]).groups())))
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["run", "task_id", "reward"])
        w.writerows(rows)


def main(download_dir, out_dir):
    rc = os.path.join(download_dir, "results_collection")
    os.makedirs(out_dir, exist_ok=True)
    parsers = {"original": original_rows, "harbor": harbor_rows}
    sides = {"original": [], "harbor": []}
    for fn in sorted(os.listdir(rc)):
        m = re.fullmatch(r"result_(original|harbor)_trial(\d+)\.json", fn)
        if not m:
            print(f"skipping {fn}")
            continue
        side, run = m.group(1), int(m.group(2))
        rows = parsers[side](os.path.join(rc, fn), run)
        vals = [x for _, _, x in rows]
        print(f"{side} run {run}: n_tasks={len(vals)} "
              f"mean={sum(vals) / len(vals):.6f}")
        sides[side] += rows
    tasks = {s: {t for _, t, _ in rows} for s, rows in sides.items()}
    assert tasks["original"] == tasks["harbor"], "task ids differ across sides"
    print(f"tasks in common: {len(tasks['original'])}")
    for side, rows in sides.items():
        if rows:
            write_csv(os.path.join(out_dir, f"{side}.csv"), rows)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
