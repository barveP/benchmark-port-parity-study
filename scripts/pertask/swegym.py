"""Per-task outcomes for the SWE-Gym Lite parity files on Hugging Face
(adapters/swegym in harborframework/parity-experiments; snapshot adapter
``swegym``).

Usage: python -I swegym.py <download_dir> <out_dir>

<download_dir> mirrors adapters/swegym/; only results_collection/ is read.
Stdlib only; nothing in <download_dir> is executed.

WHAT THE FILES ARE.  The HF folder (PR #60, merged 2026-01-14) holds ONE run
per model for openhands + {gpt-5-mini, gpt-5-nano}, dated 2026-01: Harbor
jobs over the 183-task swegym-lite dataset of that time, and the OpenHands
"run_1" outputs with 206 / 196 evaluated instances.  The results_collection/
files are byte-identical to harbor_parity/<job>/result.json and
original_parity/<run_1>/output.swebench_eval.jsonl.  The snapshot JSON
describes a later 2026-04 re-run (230 tasks x 2 runs) whose files are NOT
on HF: only gpt-5-mini run 1 reproduces (original 74/206 = 35.92 exactly,
harbor 66/183 = 36.07 vs published 36.08); the gpt-5-nano means (13.27 /
14.84) equal the HF README but none of the published nano runs.
Layout (bfcl/devopsgym style; the model that validates is the primary pair):
    original.csv / harbor.csv                          openhands + gpt-5-mini
    original__gpt-5-nano.csv / harbor__gpt-5-nano.csv  openhands + gpt-5-nano
Every file has run = 1 only.

ORIGINAL SIDE: results_collection/original_openhands_<model>_result.jsonl is
OpenHands' SWE-bench-style output.swebench_eval.jsonl: one JSON object per
evaluated instance with "instance_id" and test_result.report =
{"resolved": bool, "empty_generation", "failed_apply_patch", "error_eval",
"test_timeout"}.  task_id = instance_id verbatim (e.g. "getmoto__moto-5286",
"Project-MONAI__MONAI-1121"); reward = 1.0 if report.resolved is true else
0.0.  Instances without an output row (24 / 34 of the 230) are absent, as in
the published resolve rate (resolved / rows).

HARBOR SIDE: results_collection/harbor_openhands_<model>_result.json is a
Harbor job-level result.json: stats.evals["openhands__swegym-lite"]
.reward_stats.reward = {"1.0": [trial names], "0.0": [...]} plus
exception_stats = {<error>: [trial names]}.  Trial names are
"<task name>__<7-char suffix>" (task names are < 32 chars, so never cut);
the suffix after "__" is stripped.  Trials listed only under
exception_stats (no reward: one VerifierTimeoutError for mini; that plus an
AgentSetupTimeoutError and an AgentTimeoutError for nano) are written as
0.0, which reproduces metrics[0].mean (= resolved / stats.n_trials).  One
nano trial (project-monai__monai-2061, cancelled per job.log) is in no list
and is omitted.  Harbor task names are the SWE-Gym instance ids
lower-cased ("project-monai__monai-1121"); harbor.csv restores the original
casing through the "<owner>__<repo>" prefixes seen in the original files
(only Project-MONAI__MONAI has upper case), so both files join on task_id.
"""
import csv
import json
import os
import re
import sys

MODELS = [("gpt-5-mini", ""), ("gpt-5-nano", "__gpt-5-nano")]
EVAL = "openhands__swegym-lite"
TRIAL_SUFFIX = re.compile(r"__[A-Za-z0-9]{7}$")


def split_id(task_id):
    """'Project-MONAI__MONAI-1121' -> ('Project-MONAI__MONAI', '1121')."""
    prefix, num = task_id.rsplit("-", 1)
    assert num.isdigit() and "__" in prefix, task_id
    return prefix, num


def read_original(path):
    """{instance_id: reward} from an OpenHands output.swebench_eval.jsonl."""
    rewards = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            row = json.loads(line)
            task = row["instance_id"]
            assert task not in rewards, f"duplicate {task} in {path}"
            report = row["test_result"].get("report") or {}
            rewards[task] = 1.0 if report.get("resolved") is True else 0.0
    return rewards


def read_harbor(path):
    """{lower-case task name: reward} from a Harbor job-level result.json."""
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    ev = d["stats"]["evals"][EVAL]
    rewards = {}
    for reward, names in ev["reward_stats"]["reward"].items():
        for name in names:
            task = TRIAL_SUFFIX.sub("", name)
            assert len(task) < 32 and task not in rewards, (task, path)
            rewards[task] = float(reward)
    for names in ev["exception_stats"].values():
        for name in names:
            rewards.setdefault(TRIAL_SUFFIX.sub("", name), 0.0)
    n = d["stats"]["n_trials"]
    assert len(rewards) == n, (len(rewards), n, path)
    assert abs(sum(rewards.values()) / n - ev["metrics"][0]["mean"]) < 1e-9, path
    return rewards


def write(path, rewards):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["run", "task_id", "reward"])
        w.writerows((1, t, r) for t, r in sorted(rewards.items()))
    n, k = len(rewards), int(sum(rewards.values()))
    print(f"{os.path.basename(path)}: {n} tasks, {k} resolved, {100 * k / n:.2f}%")


def main(download_dir, out_dir):
    rc = os.path.join(download_dir, "results_collection")
    originals = {m: read_original(os.path.join(rc, f"original_openhands_{m}_result.jsonl"))
                 for m, _ in MODELS}
    case = {}  # lower-cased '<owner>__<repo>' -> casing used by SWE-Gym
    for rewards in originals.values():
        for task in rewards:
            prefix = split_id(task)[0]
            assert case.setdefault(prefix.lower(), prefix) == prefix, prefix
    os.makedirs(out_dir, exist_ok=True)
    for model, tag in MODELS:
        original = originals[model]
        harbor = {}
        for task, r in read_harbor(os.path.join(rc, f"harbor_openhands_{model}_result.json")).items():
            prefix, num = split_id(task)
            assert prefix in case, f"unknown repo prefix {prefix}"
            harbor[f"{case[prefix]}-{num}"] = r
        assert len(harbor) == len(set(harbor)), model
        write(os.path.join(out_dir, f"original{tag}.csv"), original)
        write(os.path.join(out_dir, f"harbor{tag}.csv"), harbor)
        print(f"  {model}: {len(original.keys() & harbor.keys())} tasks on both sides, "
              f"{len(original.keys() - harbor.keys())} original-only, "
              f"{len(harbor.keys() - original.keys())} harbor-only")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
