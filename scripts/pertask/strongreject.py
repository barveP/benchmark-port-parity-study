"""Per-task outcomes for the StrongReject parity experiment (HF adapters/strongreject).

Usage: python -I strongreject.py <download_dir> <out_dir>
<download_dir> is the local mirror of adapters/strongreject/ (results_collection/
and harbor_parity/trial{0,1,2}/<trial dir>/result.json). Stdlib only; nothing in
<download_dir> is executed. Experiment: agent codex@0.77.0, model gpt-5-nano,
150 tasks (50 prompts x 3 jailbreaks) x 3 runs per side. Metric: Defense Score
= 1 - StrongReject attack score, a fraction in {0, 1/8, ..., 1}.

Original side: results_collection/result_original_trial<k>.json (k = 1, 2, 3) is
JSONL (identical to original_parity/trial<k>/codex_gpt-5-nano_evals.json), 150
rows with category, forbidden_prompt, jailbreak, refusal, convincingness,
specificity, score. Rows come in three blocks of 50 (prefix_injection,
pap_logical_appeal, poems) with the same prompt order in every block and run.
reward = 1 - score. The files carry no explicit task id, so task_id is rebuilt
in the Harbor adapter's naming: strongreject_<category slug>_<i:04d>_<jailbreak>
with i = the prompt's position inside its jailbreak block; the script aborts
unless that id set equals the Harbor task_name set exactly.

Harbor side: the job-level results_collection/result_harbor_trial<k>.json truncates
task names to 32 chars (only 34 distinct after stripping the "__<hash>" suffix), so
per-task ids come from harbor_parity/trial<t>/<trial dir>/result.json: task_name
(full id, e.g. strongreject_violence_0002_poems) and verifier_result.rewards
.reward. Trial folders are matched to run numbers through config.job_id ==
the job-level file's "id", and every per-task reward is checked against the
job-level reward_stats.reward = {"<reward>": [trial names...]}.

Outputs <out_dir>/original.csv and <out_dir>/harbor.csv with columns
run,task_id,reward (run = 1, 2, 3).
"""
import csv
import json
import os
import re
import sys

RUNS = (1, 2, 3)
JAILBREAKS = ("prefix_injection", "pap_logical_appeal", "poems")


def slug(category):
    """'Hate, harassment and discrimination' -> 'hate_harassment_and_discrimination'."""
    return re.sub(r"[^a-z0-9-]+", "_", category.lower()).strip("_")


def read_original(path):
    """{task_id: reward} from one original-side JSONL evals file."""
    with open(path) as f:
        rows = [json.loads(line) for line in f if line.strip()]
    out, pos = {}, {}
    for r in rows:
        i = pos.get(r["jailbreak"], 0)
        pos[r["jailbreak"]] = i + 1
        tid = f"strongreject_{slug(r['category'])}_{i:04d}_{r['jailbreak']}"
        if tid in out:
            sys.exit(f"{path}: duplicate task id {tid}")
        out[tid] = 1.0 - float(r["score"])
    if set(pos) != set(JAILBREAKS) or set(pos.values()) != {50}:
        sys.exit(f"{path}: unexpected jailbreak blocks {pos}")
    return out


def job_level(path):
    """(job id, {trial name: reward}) from a Harbor job-level result.json."""
    with open(path) as f:
        job = json.load(f)
    (ev,) = job["stats"]["evals"].values()
    rewards = {}
    for reward, names in ev["reward_stats"]["reward"].items():
        for n in names:
            rewards[n] = float(reward)
    return job["id"], rewards


def read_harbor_trial(folder):
    """(job id, {task_name: reward}, {task_name: trial name}) from per-task result.json."""
    rewards, names, job_ids = {}, {}, set()
    for d in sorted(os.listdir(folder)):
        p = os.path.join(folder, d, "result.json")
        if not os.path.isfile(p):
            continue
        with open(p) as f:
            r = json.load(f)
        job_ids.add(r["config"]["job_id"])
        tid = r["task_name"]
        if tid in rewards:
            sys.exit(f"{folder}: duplicate task {tid}")
        if r.get("exception_info"):
            print(f"  note {d}: {r['exception_info'].get('exception_type')} -> reward "
                  f"{r['verifier_result']['rewards']['reward']}")
        rewards[tid] = float(r["verifier_result"]["rewards"]["reward"])
        names[tid] = r["trial_name"]
    if len(job_ids) != 1:
        sys.exit(f"{folder}: job ids {job_ids}")
    return job_ids.pop(), rewards, names


def write_csv(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["run", "task_id", "reward"])
        for run, tid, r in sorted(rows):
            w.writerow([run, tid, int(r) if r.is_integer() else r])
    by_run = {}
    for run, _, r in rows:
        by_run.setdefault(run, []).append(r)
    print(f"{os.path.basename(path)}: {len(rows)} rows, run means = " + ", ".join(
        f"run{k}: {sum(v) / len(v):.4f} (n={len(v)})" for k, v in sorted(by_run.items())))


def main(dl, out):
    os.makedirs(out, exist_ok=True)
    rc = os.path.join(dl, "results_collection")

    # Harbor: run number <- job id of results_collection/result_harbor_trial<k>.json
    run_of_job, ref = {}, {}
    for k in RUNS:
        job_id, rewards = job_level(os.path.join(rc, f"result_harbor_trial{k}.json"))
        run_of_job[job_id], ref[k] = k, rewards
    harbor_rows, harbor_ids = [], {}
    hp = os.path.join(dl, "harbor_parity")
    for t in sorted(os.listdir(hp)):
        job_id, rewards, names = read_harbor_trial(os.path.join(hp, t))
        k = run_of_job[job_id]
        if {names[i]: r for i, r in rewards.items()} != ref[k]:
            sys.exit(f"{t}: per-task rewards disagree with result_harbor_trial{k}.json")
        print(f"  harbor {t} -> run {k}: {len(rewards)} tasks agree with job-level reward_stats")
        harbor_ids[k] = set(rewards)
        harbor_rows += [(k, i, r) for i, r in rewards.items()]
    if len(set(map(frozenset, harbor_ids.values()))) != 1:
        sys.exit("harbor: task sets differ across runs")

    # Original: rebuilt ids must coincide with the Harbor task names
    orig_rows = []
    for k in RUNS:
        rewards = read_original(os.path.join(rc, f"result_original_trial{k}.json"))
        if set(rewards) != harbor_ids[1]:
            sys.exit(f"original trial{k}: rebuilt ids differ from Harbor task names: "
                     f"{sorted(set(rewards) ^ harbor_ids[1])[:5]}")
        orig_rows += [(k, i, r) for i, r in rewards.items()]

    for rows in (orig_rows, harbor_rows):
        bad = [x for x in rows if not 0 <= x[2] <= 1]
        if bad:
            sys.exit(f"rewards outside [0,1]: {bad[:5]}")
    write_csv(os.path.join(out, "original.csv"), orig_rows)
    write_csv(os.path.join(out, "harbor.csv"), harbor_rows)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
