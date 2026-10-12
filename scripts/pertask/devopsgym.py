"""Per-task outcomes for the DevOps-Gym parity files on Hugging Face
(adapters/devopsgym in harborframework/parity-experiments; snapshot adapter
``devopsgym``).

Usage: python -I devopsgym.py <download_dir> <out_dir>

<download_dir> mirrors adapters/devopsgym/: results_collection/ (read for all
rewards) and, optionally, harbor_parity/<job>/<trial>/result.json for the
trials whose names Harbor truncated (see below).  Stdlib only; nothing in
<download_dir> is executed.

WHAT THE FILES ARE.  The HF folder holds three (agent, model) experiments,
each a SINGLE run over a 46-task subset, dated 2026-01-02..09, all with the
codex agent (config.json / run_metadata.json say so, also for claude-haiku).
They are NOT the 50-task, 5/3-run experiments of March 2026 listed in the
snapshot JSON, so run means will not match the published run lists.
Following the bfcl layout, the first snapshot experiment is the primary pair:
    original.csv / harbor.csv                          codex + gpt-5-nano
    original__gpt-5-mini.csv / harbor__gpt-5-mini.csv  codex + gpt-5-mini
    original__claude-haiku-4-5.csv / harbor__...csv    codex + claude-haiku-4-5
Every file has run = 1 only.

ORIGINAL SIDE (terminal-bench harness): results_collection/tbench*.json is a
terminal-bench results.json: {"results": [{"task_id", "is_resolved",
"failure_mode", ...}], "resolved_ids", "unresolved_ids", "accuracy"}.
task_id is taken verbatim (e.g. "build__new_bugswarm__wmixvideo-nfe-44649171033",
"codegen__spotbugs__spotbugs-2516"); reward = 1.0 if is_resolved is True else
0.0.  is_resolved is null for trials that failed before verification
(failure_mode unknown_agent_error / test_timeout); the published accuracy
counts them as failures (n_resolved / 46) and so does this script.  The
script checks that against resolved_ids and accuracy.

HARBOR SIDE: results_collection/harbor_*.json is a Harbor job-level
result.json; stats.evals["codex__DevOpsGym_subset"].reward_stats.reward =
{"1.0": [trial names], "0.0": [trial names]}; trials under exception_stats
have no reward and are written as 0.0 (Harbor's metrics.mean divides by
n_total_trials = 46).  Trial names are "<task name cut to 32 chars>__<7-char
suffix>"; the suffix is stripped.  The 32-char cut makes 6 prefixes ambiguous
(2-3 tasks each, 13 trials per job), so for those the per-trial file
harbor_parity/<job>/<trial name>/result.json is read for its full "task_name"
(only that field is used; its reward field is stale in some copies).  Harbor
task names use single underscores in the build_/monitor_ families
("build_new_bugswarm_wmixvideo-nfe-44649171033") and double in codegen__/
testgen__; after collapsing "__" to "_" each Harbor name equals, or is a
unique prefix of, exactly one original task_id, and the script asserts the
mapping is a bijection onto the 46 original ids.  harbor.csv therefore uses
the ORIGINAL task_id, so the two files join on task_id.
"""
import csv
import glob
import json
import os
import re
import sys

TRIAL_SUFFIX = re.compile(r"__[A-Za-z0-9]{7}$")
EVAL = "codex__DevOpsGym_subset"
EXPERIMENTS = [  # (harbor job file, original tbench file, output suffix)
    ("harbor_devops-codex-gpt-5-nano_result.json", "tbench-devOps-codex-gpt-5-nano_results.json", ""),
    ("harbor_devops-codex-gpt-5-mini_result.json", "tbench-devOps-codex-gpt-5-mini_results.json", "__gpt-5-mini"),
    ("harbor_codex-claude-haiku-4-5_result.json", "tbench_devops-codex-claude-haiku-4-5_result.json", "__claude-haiku-4-5"),
]


def norm(name):
    return re.sub(r"_+", "_", name)


def read_original(path):
    """{task_id: reward} from a terminal-bench results.json, with checks."""
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    out = {r["task_id"]: (1.0 if r["is_resolved"] is True else 0.0) for r in data["results"]}
    assert len(out) == len(data["results"]), f"duplicate task_id in {path}"
    assert {t for t, v in out.items() if v == 1.0} == set(data["resolved_ids"])
    assert abs(sum(out.values()) / len(out) - data["accuracy"]) < 1e-9
    nulls = [r["task_id"] for r in data["results"] if r["is_resolved"] is None]
    return out, nulls


def read_harbor(path):
    """({trial name: reward}, {trial name: exception}) from a job-level result.json."""
    with open(path, encoding="utf-8") as fh:
        ev = json.load(fh)["stats"]["evals"][EVAL]
    rewards = {n: float(rw) for rw, names in ev["reward_stats"]["reward"].items() for n in names}
    errors = {n: exc for exc, names in ev.get("exception_stats", {}).items() for n in names}
    for n in errors:
        rewards.setdefault(n, 0.0)
    return rewards, errors


def harbor_task_name(download_dir, trial):
    """Full task name from the per-trial result.json if downloaded, else the truncated name."""
    hits = glob.glob(os.path.join(download_dir, "harbor_parity", "*", trial, "result.json"))
    if hits:
        with open(hits[0], encoding="utf-8") as fh:
            return json.load(fh)["task_name"], True
    return TRIAL_SUFFIX.sub("", trial), False


def map_to_original(download_dir, trials, originals):
    """{trial name: original task_id}; asserts a bijection onto the original ids."""
    by_norm = {norm(o): o for o in originals}
    mapping = {}
    for trial in trials:
        name, full = harbor_task_name(download_dir, trial)
        n = norm(name)
        cands = [o for k, o in by_norm.items() if (k == n if full else k.startswith(n))]
        assert len(cands) == 1, f"{trial}: {len(cands)} candidates for {name!r} (full={full})"
        mapping[trial] = cands[0]
    assert sorted(mapping.values()) == sorted(originals), "harbor trials do not map 1:1 onto original ids"
    return mapping


def write_csv(path, rows):
    rows.sort()
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["run", "task_id", "reward"])
        w.writerows(rows)
    vals = [x for _, _, x in rows]
    print(f"  {os.path.basename(path)}: n_tasks={len(vals)} n_pass={int(sum(vals))} mean={sum(vals) / len(vals):.4f}")


def main(download_dir, out_dir):
    rc = os.path.join(download_dir, "results_collection")
    os.makedirs(out_dir, exist_ok=True)
    for hfile, ofile, suffix in EXPERIMENTS:
        print(f"== {hfile} vs {ofile} -> *{suffix}.csv (run 1)")
        original, nulls = read_original(os.path.join(rc, ofile))
        rewards, errors = read_harbor(os.path.join(rc, hfile))
        mapping = map_to_original(download_dir, sorted(rewards), sorted(original))
        write_csv(os.path.join(out_dir, f"original{suffix}.csv"), [(1, t, rw) for t, rw in original.items()])
        write_csv(os.path.join(out_dir, f"harbor{suffix}.csv"), [(1, mapping[n], rw) for n, rw in rewards.items()])
        print(f"  original is_resolved=null (written 0.0): {len(nulls)}: {nulls}")
        print(f"  harbor exception trials (written 0.0): {[(mapping[n], e) for n, e in errors.items()]}")
        n_full = sum(1 for n in rewards if harbor_task_name(download_dir, n)[1])
        print(f"  harbor trials resolved via per-trial result.json: {n_full}; by unique prefix: {len(rewards) - n_full}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
