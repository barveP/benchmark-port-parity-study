"""Per-task outcomes for the SWE-bench Pro parity experiments (HF adapter
folder ``adapters/swebenchpro`` in harborframework/parity-experiments;
snapshot adapter ``swebenchpro``).

Usage: python -I swebenchpro.py <download_dir> <out_dir>

<download_dir> mirrors adapters/swebenchpro/.  Stdlib only; nothing under
<download_dir> is executed.  The folder holds two experiments, both with
binary reward (1 = resolved):

    results_collection/, harbor_parity/, original_parity/
        codex@0.77.0 + gpt-5-mini-2025-08-07, 6 runs x 100 tasks (2025-12-21)
        -> original.csv / harbor.csv
    results_collection-2026-03-11/, harbor_parity-2026-03-11/, ...
        codex@0.114.0 + gpt-5.4, 4 runs x 10 tasks (2026-03-11)
        -> original__gpt-5.4.csv / harbor__gpt-5.4.csv

ORIGINAL SIDE: results_collection*/result_original_trial<N>.json is a flat
dict {instance_id: bool} (a byte copy of original_parity*/trial<N>/
eval_results.json).  task_id = the SWE-bench Pro instance id verbatim, e.g.
"instance_ansible__ansible-1c06c46c...-v0f01c69f..."; reward = 1.0 if the
bool is true else 0.0; run = N from the file name.

HARBOR SIDE: results_collection*/result_harbor_trial<N>.json is a Harbor
job-level result.json; stats.evals[<name>].reward_stats.reward =
{"0.0": [trial names], "1.0": [trial names]}.  Trial names are the task
name cut to 32 characters plus a "__<7 chars>" suffix, e.g.
"instance_future-architect__vuls-__2YHratZ", and the cut makes most names
ambiguous (6 prefixes cover ~2/3 of the tasks), so the suffix is stripped
and the full task name is read from the per-trial file
harbor_parity*/trial<N>/<trial name>/result.json ("task_name"; its
verifier_result.rewards.reward is checked against the job-level value).
Harbor task names equal the original instance ids, so both CSVs join on
task_id.  The script asserts that, and that no (run, task) repeats.

CAVEAT (reported, not fixed): Harbor run 1 of the 2025 experiment was run on
dataset "swebenchpro5", a different 100-task sample from the one used by
Harbor runs 2-6 and by all original runs ("swebenchpro7"/"swebenchpro-sample"
= the original_parity sample).  It is kept because the published run list
includes its score; drop run 1 for paired analysis.
"""
import csv
import json
import os
import re
import sys

TRIAL_SUFFIX = re.compile(r"__[A-Za-z0-9]{7}$")
TRIAL_FILE = re.compile(r"result_(original|harbor)_trial(\d+)\.json$")
EXPERIMENTS = [  # (results_collection dir, harbor_parity dir, output suffix)
    ("results_collection", "harbor_parity", ""),
    ("results_collection-2026-03-11", "harbor_parity-2026-03-11", "__gpt-5.4"),
]


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def trial_files(rc_dir, side):
    out = {}
    for name in os.listdir(rc_dir):
        m = TRIAL_FILE.match(name)
        if m and m.group(1) == side:
            out[int(m.group(2))] = os.path.join(rc_dir, name)
    return dict(sorted(out.items()))


def original_rows(rc_dir):
    rows = []
    for run, path in trial_files(rc_dir, "original").items():
        data = load(path)
        assert all(isinstance(v, bool) for v in data.values()), path
        rows += [(run, tid, 1.0 if ok else 0.0) for tid, ok in data.items()]
    return rows


def harbor_rows(rc_dir, hp_dir):
    rows = []
    for run, path in trial_files(rc_dir, "harbor").items():
        job = load(path)
        (ev,) = job["stats"]["evals"].values()
        assert not ev.get("exception_stats"), (path, ev.get("exception_stats"))
        for reward, trials in ev["reward_stats"]["reward"].items():
            for trial in trials:
                prefix = TRIAL_SUFFIX.sub("", trial)
                per = load(os.path.join(hp_dir, f"trial{run}", trial, "result.json"))
                task = per["task_name"]
                assert task[:32] == prefix and per["trial_name"] == trial, trial
                assert float(per["verifier_result"]["rewards"]["reward"]) == float(reward), trial
                rows.append((run, task, float(reward)))
    return rows


def check(rows, label):
    keys = [(r, t) for r, t, _ in rows]
    assert len(keys) == len(set(keys)), f"{label}: duplicated (run, task) pairs"
    assert all(0.0 <= x <= 1.0 for _, _, x in rows), f"{label}: reward outside [0,1]"
    by_run = {}
    for r, t, x in rows:
        by_run.setdefault(r, []).append(x)
    for r in sorted(by_run):
        print(f"  {label} run {r}: n={len(by_run[r])} mean={sum(by_run[r]) / len(by_run[r]):.4f}")


def write(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["run", "task_id", "reward"])
        w.writerows(sorted(rows))


def main(download_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    for rc, hp, suffix in EXPERIMENTS:
        rc_dir = os.path.join(download_dir, rc)
        if not os.path.isdir(rc_dir):
            print(f"skip {rc}: not downloaded")
            continue
        orig = original_rows(rc_dir)
        harb = harbor_rows(rc_dir, os.path.join(download_dir, hp))
        print(f"{rc}:")
        check(orig, "original")
        check(harb, "harbor")
        otasks = {t for _, t, _ in orig}
        for run in sorted({r for r, _, _ in harb}):
            htasks = {t for r, t, _ in harb if r == run}
            if htasks != otasks:
                print(f"  NOTE harbor run {run}: {len(htasks & otasks)} of {len(htasks)} tasks "
                      f"are in the original sample ({len(otasks)} tasks)")
        write(os.path.join(out_dir, f"original{suffix}.csv"), orig)
        write(os.path.join(out_dir, f"harbor{suffix}.csv"), harb)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
