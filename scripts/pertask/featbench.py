"""Per-task outcomes for the FeatBench parity experiment (HF adapter folder
``adapters/featbench``, snapshot adapter ``featbench``): trae-agent@0.1.0 on
156 feature-implementation tasks, binary reward (1 = every FAIL_TO_PASS and
PASS_TO_PASS test passes, the "resolved" of resolved_rate).

Usage: python -I featbench.py <download_dir> <out_dir>

<download_dir> mirrors adapters/featbench/ of the Hugging Face dataset
harborframework/parity-experiments: results_collection/ plus, for the
ambiguously truncated Harbor trials only (see below),
harbor_parity/<job>/<run>/<trial>/result.json.  Stdlib only; nothing in
<download_dir> is executed.

Original side -- results_collection/original__<model>__<YYYYMMDD-HHMMSS>.json
is the FeatBench harness output (all original runs use trae-agent): a JSON list
of 156 per-instance records {agent, model, instance_id, success_f2p,
success_p2p, success, patch, passed/expected_f2p/p2p_tests}; a record whose
agent run crashed has {agent, model, instance_id, success: false, error}
instead.  task_id = instance_id verbatim ("conan-io__conan-17507");
reward = 1 if success is true else 0, so crashed records are failures, which is
how the published resolved_rate (passes / 156) counts them.  Runs are numbered
in timestamp order of the files present.

Harbor side -- results_collection/harbor__<agent>-<model>__<date>__<time>.json
is a Harbor job-level result.json: stats.evals["<agent>__<model>__featbench"]
.reward_stats.reward = {"1.0": [trial names], "0.0": [trial names]} and
.exception_stats = {<exception>: [trial names]}.  A trial name is the task name
TRUNCATED TO 32 CHARACTERS plus a "__<7 alphanumerics>" trial suffix; the
suffix is stripped and a truncated name is restored to the full instance_id by
unique prefix match against the original ids.  Two prefixes are ambiguous
("koxudaxi__datamodel-code-generat" covers 8 instances,
"modelcontextprotocol__python-sdk" 2); those trials are resolved from the full
task_name in harbor_parity/featbench-<agent>-<model>/<date>__<time>/<trial>/
result.json, whose verifier reward is also cross-checked.  Trials that raised
and have no reward entry are written with reward 0.0, matching Harbor's own
metrics.mean (denominator n_total_trials = 156).  Runs are numbered in date
order of the files.

Outputs (columns run,task_id,reward): original.csv / harbor.csv are the parity
pair for trae-agent + gpt-5-mini; any other experiment in the folder goes to
original__<tag>.csv / harbor__<tag>.csv with the HF file tag ("trae-deepseek-v3.2",
"codex-gpt-5-mini").
"""
import csv
import json
import os
import re
import sys

PRIMARY = "trae-gpt-5-mini"
TRIAL_SUFFIX = re.compile(r"__[A-Za-z0-9]{7}$")
TRUNC = 32  # Harbor truncates task names to this many characters in trial names


def read_original(path):
    """({instance_id: reward}, [crashed instance ids]) from one harness result file."""
    with open(path, encoding="utf-8") as fh:
        recs = json.load(fh)
    rewards = {r["instance_id"]: float(r["success"] is True) for r in recs}
    assert len(rewards) == len(recs), f"duplicate instance_id in {path}"
    return rewards, [r["instance_id"] for r in recs if "error" in r]


def read_harbor(path):
    """({trial name: reward}, {trial name: exception}) from a Harbor job result.json."""
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    (ev,) = data["stats"]["evals"].values()
    rewards = {n: float(r) for r, names in ev["reward_stats"]["reward"].items() for n in names}
    errors = {n: exc for exc, names in ev.get("exception_stats", {}).items() for n in names}
    for n in errors:
        rewards.setdefault(n, 0.0)  # raised before it was scored: Harbor counts it as 0
    assert len(rewards) == data["n_total_trials"], path
    assert abs(sum(rewards.values()) / len(rewards) - ev["metrics"][0]["mean"]) < 1e-9, path
    return rewards, errors


def resolve(trial, reward, originals, run_dir):
    """Full task id for a Harbor trial name, or None if it cannot be restored."""
    slug = TRIAL_SUFFIX.sub("", trial)
    if len(slug) < TRUNC or slug in originals and not any(o != slug and o.startswith(slug) for o in originals):
        return slug
    cands = [o for o in originals if o.startswith(slug)]
    if len(cands) == 1:
        return cands[0]
    rj = os.path.join(run_dir, trial, "result.json")
    if not os.path.exists(rj):
        return None
    with open(rj, encoding="utf-8") as fh:
        tr = json.load(fh)
    assert tr["trial_name"] == trial, rj
    got = (tr.get("verifier_result") or {}).get("rewards", {}).get("reward", 0.0)
    assert float(got) == reward, f"reward mismatch for {trial}: job {reward} vs trial {got}"
    return tr["task_name"]


def write_csv(path, rows):
    rows.sort()
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["run", "task_id", "reward"])
        w.writerows(rows)
    print(os.path.basename(path))
    for run in sorted({r for r, _, _ in rows}):
        vals = [x for r, _, x in rows if r == run]
        print(f"  run {run}: n_tasks={len(vals)} n_pass={int(sum(vals))} mean={sum(vals) / len(vals):.4f}")


def main(download_dir, out_dir):
    rc = os.path.join(download_dir, "results_collection")
    os.makedirs(out_dir, exist_ok=True)
    original, harbor = {}, {}  # tag -> {timestamp: parsed file}
    for fn in sorted(os.listdir(rc)):
        m = re.fullmatch(r"original__(.+)__(\d{8}-\d{6})\.json", fn)
        if m:
            original.setdefault("trae-" + m.group(1), {})[m.group(2)] = read_original(os.path.join(rc, fn))
        m = re.fullmatch(r"harbor__(.+)__(\d{4}-\d{2}-\d{2}__\d{2}-\d{2}-\d{2})\.json", fn)
        if m:
            harbor.setdefault(m.group(1), {})[m.group(2)] = read_harbor(os.path.join(rc, fn))
    originals = sorted({i for runs in original.values() for d, _ in runs.values() for i in d})

    def out_name(side, tag):
        return os.path.join(out_dir, f"{side}.csv" if tag == PRIMARY else f"{side}__{tag}.csv")

    for tag, runs in sorted(original.items()):
        rows, crashed = [], []
        for run, stamp in enumerate(sorted(runs), 1):
            rewards, errs = runs[stamp]
            rows += [(run, i, r) for i, r in rewards.items()]
            crashed += [(run, i) for i in errs]
        write_csv(out_name("original", tag), rows)
        print("  crashed records (written as reward 0.0):", crashed)

    for tag, runs in sorted(harbor.items()):
        rows, unresolved, errored, truncated = [], [], [], set()
        for run, stamp in enumerate(sorted(runs), 1):
            rewards, errs = runs[stamp]
            run_dir = os.path.join(download_dir, "harbor_parity", f"featbench-{tag}", stamp)
            ids = {}
            for trial, reward in rewards.items():
                tid = resolve(trial, reward, originals, run_dir)
                if tid is None:
                    unresolved.append((run, trial))
                    tid = TRIAL_SUFFIX.sub("", trial)
                elif tid != TRIAL_SUFFIX.sub("", trial):
                    truncated.add(tid)
                assert tid not in ids, f"{tag} run {run}: task {tid} appears twice"
                ids[tid] = reward
                if trial in errs:
                    errored.append((run, tid, errs[trial], reward))
            rows += [(run, i, r) for i, r in ids.items()]
        write_csv(out_name("harbor", tag), rows)
        print("  task names restored from a 32-char truncation:", len(truncated))
        print("  trials that raised (reward as written):", errored)
        if unresolved:
            print("  UNRESOLVED truncated trial names (kept truncated):", unresolved)
        if originals:
            tasks = {i for _, i, _ in rows}
            print("  harbor tasks not in original ids:", sorted(tasks - set(originals)),
                  "| original ids not in harbor:", sorted(set(originals) - tasks))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
