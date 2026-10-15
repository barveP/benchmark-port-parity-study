"""Per-task outcomes for the deveval Harbor parity experiment (stdlib only).

Usage:  python -I deveval.py <download_dir> <out_dir>

<download_dir> mirrors adapters/deveval/ of the Hugging Face dataset
harborframework/parity-experiments; only results_collection/ is read.
Both sides: 3 runs x 63 tasks (21 repos x 3 phases), binary rewards.

Original side (Terminal-Bench harness),
    results_collection/result_original_trial<N>.json =
    {"results": [{"task_id", "is_resolved": true|false|null, "failure_mode",
                  "parser_results", ...}, ...],
     "n_resolved", "n_unresolved", "resolved_ids", "unresolved_ids", "accuracy"}
reward = 1.0 if is_resolved is true else 0.0.  is_resolved is null for a few
"parse_error" trials; upstream counts them as unresolved (they sit in
unresolved_ids and accuracy == n_resolved / 63), so they get 0.0 here.
task_id = the "task_id" field verbatim, e.g. "cpp-area-calculation-unit-testing".

Harbor side, results_collection/result_harbor_trial<N>.json = Harbor job-level
result.json:
    stats.evals[<name>].reward_stats.reward   = {"<reward>": [trial names]}
    stats.evals[<name>].exception_stats       = {"<ExcName>": [trial names]}
Trial names are "<task name truncated to 32 chars>__<7-char suffix>"; the
"__<suffix>" is stripped.  Trials listed only under exception_stats
(AgentTimeoutError, RewardFileNotFoundError) get reward 0.0, which reproduces
the published means (metrics[0].mean == sum of rewards / n_total_trials == 63);
a trial listed in both places keeps its scored reward.
Because Harbor truncates task names to 32 characters, each stripped name is
mapped back to the full DevEval task id through the original side's id list
(unique 32-char prefix -> full id; 60 of the 63 tasks).  The three
python-particle-swarm-optimization-{implementation,unit-testing,
acceptance-testing} tasks share the prefix "python-particle-swarm-optimizati"
and cannot be told apart in the Harbor file; they are written as
"python-particle-swarm-optimizati#1".."#3" (numbered in trial-suffix order,
i.e. arbitrarily) so that the run means cover all 63 trials.  These pseudo-ids
carry NO task identity across runs and do not pair with the original side.
"""
import csv
import json
import os
import re
import sys
from collections import defaultdict

TRIAL_SUFFIX = re.compile(r"__[A-Za-z0-9]+$")
HARBOR_NAME_LEN = 32


def original_rows(path, run):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    rows = []
    for r in data["results"]:
        if r["is_resolved"] is None:
            print(f"  note: {r['task_id']} is_resolved=null "
                  f"(failure_mode={r['failure_mode']}) -> 0.0")
        rows.append((run, r["task_id"], 1.0 if r["is_resolved"] is True else 0.0))
    assert sum(x for _, _, x in rows) == data["n_resolved"], path
    return rows


def harbor_rows(path, run, prefix_map):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    (ev,) = data["stats"]["evals"].values()
    rewards = {}
    for reward, names in ev["reward_stats"]["reward"].items():
        for name in names:
            rewards[name] = float(reward)
    for exc, names in ev.get("exception_stats", {}).items():
        for name in names:
            if name in rewards:
                print(f"  note: {name} scored and also under {exc}; keeping reward")
            else:
                print(f"  note: {name} only under {exc} -> 0.0")
                rewards[name] = 0.0
    assert len(rewards) == data["n_total_trials"], (path, len(rewards))
    by_prefix = defaultdict(list)
    for name in sorted(rewards):
        by_prefix[TRIAL_SUFFIX.sub("", name)].append(name)
    rows = []
    for prefix, names in by_prefix.items():
        full = prefix_map.get(prefix, [prefix])
        if len(full) == 1 and len(names) == 1:
            rows.append((run, full[0], rewards[names[0]]))
        else:
            print(f"  note: prefix {prefix!r} is ambiguous ({len(names)} trials, "
                  f"{len(full)} full ids); using {prefix}#k pseudo-ids")
            for k, name in enumerate(names, 1):
                rows.append((run, f"{prefix}#{k}", rewards[name]))
    return rows


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
    files = {}
    for fn in sorted(os.listdir(rc)):
        m = re.fullmatch(r"result_(harbor|original)_trial(\d+)\.json", fn)
        if m:
            files[(m.group(1), int(m.group(2)))] = os.path.join(rc, fn)

    original = []
    for (side, run), path in sorted(files.items()):
        if side == "original":
            original += original_rows(path, run)
    prefix_map = defaultdict(list)
    for t in sorted({t for _, t, _ in original}):
        prefix_map[t[:HARBOR_NAME_LEN]].append(t)

    harbor = []
    for (side, run), path in sorted(files.items()):
        if side == "harbor":
            harbor += harbor_rows(path, run, prefix_map)

    for side, rows in (("original", original), ("harbor", harbor)):
        for run in sorted({r for r, _, _ in rows}):
            vals = [x for r, _, x in rows if r == run]
            print(f"{side} run {run}: n_tasks={len(vals)} "
                  f"mean={sum(vals) / len(vals):.6f}")
        if rows:
            write_csv(os.path.join(out_dir, f"{side}.csv"), rows)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
