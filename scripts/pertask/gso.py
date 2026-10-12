"""Per-task outcomes for the GSO parity experiment (HF adapter folder
``adapters/gso``, snapshot adapter ``gso``): OpenHands@1.4.0 + gpt-5.1
(high), 2 runs x 102 performance-optimisation tasks, binary reward
(Opt@1: 1 = the agent's patch passes the tests and matches the speed-up of
the human commit).

Usage: python -I gso.py <download_dir> <out_dir>

<download_dir> mirrors adapters/gso/ of the Hugging Face dataset
harborframework/parity-experiments; only results_collection/ is read.
Writes <out_dir>/original.csv and <out_dir>/harbor.csv (run,task_id,reward).

Original side -- results_collection/result_original_trial<N>.json is a GSO
evaluation report (schema_version 1): "summary" (total_instances=102,
opt_commit, score), "instance_sets" (completed_ids, passed_ids,
test_failed_ids, empty_patch_ids, opt_commit_ids, ...) and "opt_stats"
(speed-up statistics per instance that passed the tests).  task_id = the GSO
instance id verbatim, "<owner>__<repo>-<7-char commit>", e.g.
"pandas-dev__pandas-438b957".  reward = 1.0 if the id is in opt_commit_ids
else 0.0; that is the Opt@1 metric (summary.score = 100 * opt_commit /
total_instances).  The task universe is the union of every instance_sets list
over both run files (102 ids = total_instances).  Run 1 lists only the 97
instances for which the agent produced a prediction; the 5 absent ones are
written with reward 0.0, which is how the report's score counts them.

Harbor side -- results_collection/result_harbor_trial<N>.json is a Harbor
job-level result.json; stats.evals["openhands__gso"].reward_stats.reward =
{"1.0": [trial names], "0.0": [trial names]}.  Trial names look like
"gso-pandas-dev--pandas-c6cf37a__S8tHDAe": the "__<7 chars>" trial suffix is
stripped, leaving the Harbor task name "gso-<owner>--<repo>-<commit>"
truncated to 32 characters (e.g. "gso-huggingface--transformers-63").
Trials that raised (exception_stats: AgentTimeoutError,
NonZeroAgentExitCodeError) and have no reward entry are written with reward
0.0, which is how Harbor's own metrics.mean counts them (denominator
n_total_trials = 102).

Task-id pairing -- an original id "<owner>__<rest>" becomes
"gso-<owner>--<rest>" lower-cased; a Harbor name must equal that or be a
unique prefix of it (case-insensitive; 4 Pillow ids differ only by case,
"Pillow" vs "pillow").  harbor.csv uses the ORIGINAL instance id as task_id,
so both files join on task_id; the mapping is asserted one-to-one and total.
"""
import csv
import json
import os
import re
import sys

TRIAL_SUFFIX = re.compile(r"__[A-Za-z0-9]+$")


def read_original(path):
    """({instance id: reward}, set of all listed instance ids) for one run."""
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    sets = data["instance_sets"]
    listed = {i for ids in sets.values() for i in ids}
    opt = set(sets["opt_commit_ids"])
    assert opt <= listed and len(opt) == data["summary"]["opt_commit"]
    return {i: (1.0 if i in opt else 0.0) for i in listed}, listed


def read_harbor(path):
    """({harbor task name: reward}, {name: exception}) for one run."""
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    rewards, errors = {}, {}
    for ev in data["stats"]["evals"].values():
        for reward, names in ev["reward_stats"]["reward"].items():
            for name in names:
                task = TRIAL_SUFFIX.sub("", name)
                assert task not in rewards, f"duplicate task {task} in {path}"
                rewards[task] = float(reward)
        for exc, names in ev.get("exception_stats", {}).items():
            for name in names:
                errors[TRIAL_SUFFIX.sub("", name)] = exc
    for task in errors:
        rewards.setdefault(task, 0.0)  # errored trial: Harbor scores it 0
    assert len(rewards) == data["n_total_trials"], path
    return rewards, errors


def harbor_to_original(harbor_names, original_ids):
    def canon(oid):
        owner, rest = oid.split("__", 1)
        return f"gso-{owner}--{rest}".lower()

    by_canon = {canon(o): o for o in original_ids}
    assert len(by_canon) == len(original_ids), "original ids collide"
    mapping = {}
    for h in harbor_names:
        cands = [o for c, o in by_canon.items() if c.startswith(h.lower())]
        assert len(cands) == 1, f"{h!r} matches {cands}"
        mapping[h] = cands[0]
    assert len(set(mapping.values())) == len(mapping), "mapping not one-to-one"
    return mapping


def write_csv(path, rows):
    rows.sort()
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["run", "task_id", "reward"])
        w.writerows(rows)
    for run in sorted({r for r, _, _ in rows}):
        vals = [x for r, _, x in rows if r == run]
        print(f"  run {run}: n_tasks={len(vals)} n_pass={int(sum(vals))} "
              f"mean={100 * sum(vals) / len(vals):.2f}%")


def main(download_dir, out_dir):
    rc = os.path.join(download_dir, "results_collection")
    os.makedirs(out_dir, exist_ok=True)
    original, harbor, harbor_errors = {}, {}, {}
    universe = set()
    for fn in sorted(os.listdir(rc)):
        m = re.fullmatch(r"result_(original|harbor)_trial(\d+)\.json", fn)
        if not m:
            continue
        side, run = m.group(1), int(m.group(2))
        if side == "original":
            original[run], listed = read_original(os.path.join(rc, fn))
            universe |= listed
        else:
            harbor[run], harbor_errors[run] = read_harbor(os.path.join(rc, fn))

    print(f"original task universe: {len(universe)} instance ids")
    for run, d in sorted(original.items()):
        missing = sorted(universe - set(d))
        if missing:
            print(f"  run {run}: {len(missing)} ids absent from the report, "
                  f"written as 0.0: {missing}")
        for i in missing:
            d[i] = 0.0

    mapping = harbor_to_original({t for d in harbor.values() for t in d}, universe)
    assert set(mapping.values()) == universe, "harbor tasks != original tasks"

    print("original.csv")
    write_csv(os.path.join(out_dir, "original.csv"),
              [(run, i, rw) for run, d in original.items() for i, rw in d.items()])
    print("harbor.csv (task_id = original instance id)")
    write_csv(os.path.join(out_dir, "harbor.csv"),
              [(run, mapping[t], rw) for run, d in harbor.items() for t, rw in d.items()])

    print("harbor trials with an exception (reward 0.0):")
    for run, errs in sorted(harbor_errors.items()):
        for t, exc in sorted(errs.items()):
            print(f"  run {run}: {mapping[t]} ({exc})")
    print("harbor names that are truncated forms of the original id:")
    for h, o in sorted(mapping.items()):
        if len(h) < len(f"gso-{o.replace('__', '--', 1)}"):
            print(f"  {h!r} -> {o!r}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
