"""Per-task outcomes for the KUMO parity experiment (HF adapters/kumo,
snapshot adapter ``kumo``): agent kumo-vanilla (upstream VanillaAgent),
model openai/gpt-5-nano, 3 runs x 212 tasks, binary reward (1 = the agent's
final predicted truth is correct).

Usage: python -I kumo.py <download_dir> <out_dir>

<download_dir> mirrors adapters/kumo/ of the Hugging Face dataset
harborframework/parity-experiments (results_collection/, original_parity/ and
a few per-trial folders of harbor_parity/).  Stdlib only; nothing in
<download_dir> is executed.  Writes <out_dir>/original.csv and
<out_dir>/harbor.csv (columns run,task_id,reward).

Task ids.  A KUMO task is a (domain, scenario, seed) triple, e.g.
AlgorithmEnv / truth_num=4+action_num=6+valid_truth_num=1 / seed 0.  The
Harbor adapter names it "<domain lower-cased>-t<truth_num>-a<action_num>-
v<valid_truth_num>-s<seed>" ("algorithmenv-t4-a6-v1-s0").  That Harbor task
name is the task_id on BOTH sides; on the original side it is built from the
file path and the "seed" field, and the two id sets are asserted equal.

Harbor side -- results_collection/result_harbor_trial<N>.json, one Harbor
job-level result.json per run (run = N).  Rewards live in
stats.evals[<eval name>].reward_stats.reward = {"1.0"/"0.0": [trial names]}.
Trial names are "<task name>__<7-char suffix>"; the suffix is stripped.
Harbor truncates the task-name part to 32 characters, so for three domains
(mineralclassificationenv, politicalmanifestoenv, virusclassificationenv)
the seed digit is cut off and seeds 0/1 collide.  For every trial that has a
per-trial folder harbor_parity/run<N>/<trial name>/result.json, the full
"task_name" from that file is used instead (its verifier_result reward is
asserted equal to the job-level one); the script requires that every
stripped name that does not parse as a full task name was resolved this way.

Original side -- results_collection/result_original_trial<N>.json holds only
the aggregate accuracy.  Per-task data is in the raw upstream outputs
original_parity/gpt-5-nano/VanillaAgent/<Domain>/<scenario>/eval_times=3.jsonl
(106 files, one per (domain, scenario)).  Each line is one seed (a task):
{"seed": k, "trajectories": [3 x {"successful": bool, "parse_error": bool,
...}], "average_correct": ..., ...}.  trajectories[j] is eval_time j, i.e.
run j+1 (the order is confirmed by the trial accuracies in
results_collection/result_original_trial<N>.json); reward = 1.0 if
"successful" else 0.0.  mean(successful) is checked against average_correct.
"""
import csv
import json
import os
import re
import sys

TRIAL_SUFFIX = re.compile(r"__[A-Za-z0-9]+$")
TASK_NAME = re.compile(r"[a-z0-9]+env-t\d+-a\d+-v\d+-s\d+")
SCENARIO = re.compile(r"truth_num=(\d+)\+action_num=(\d+)\+valid_truth_num=(\d+)")


def write_csv(path, rows):
    rows.sort()
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["run", "task_id", "reward"])
        w.writerows(rows)


def report(side, rows):
    for run in sorted({r for r, _, _ in rows}):
        vals = [x for r, _, x in rows if r == run]
        print(f"{side} run {run}: n_tasks={len(vals)} mean={sum(vals) / len(vals):.6f}")


def harbor_rows(download_dir):
    rc_dir = os.path.join(download_dir, "results_collection")
    rows, resolved = [], 0
    for fn in sorted(os.listdir(rc_dir)):
        m = re.fullmatch(r"result_harbor_trial(\d+)\.json", fn)
        if not m:
            continue
        run = int(m.group(1))
        with open(os.path.join(rc_dir, fn), encoding="utf-8") as fh:
            data = json.load(fh)
        assert data["stats"]["n_errors"] == 0, f"{fn}: n_errors != 0"
        n = 0
        for ev in data["stats"]["evals"].values():
            for reward, names in ev["reward_stats"]["reward"].items():
                for trial in names:
                    task = TRIAL_SUFFIX.sub("", trial)
                    per_trial = os.path.join(download_dir, "harbor_parity", f"run{run}", trial, "result.json")
                    if os.path.exists(per_trial):
                        with open(per_trial, encoding="utf-8") as fh:
                            tr = json.load(fh)
                        assert tr["trial_name"] == trial and tr["verifier_result"]["rewards"]["reward"] == float(reward)
                        if tr["task_name"] != task:
                            resolved += 1
                        task = tr["task_name"]
                    assert TASK_NAME.fullmatch(task), f"{fn}: unresolved truncated trial {trial}"
                    rows.append((run, task, float(reward)))
                    n += 1
        assert n == data["n_total_trials"], f"{fn}: {n} rewards vs {data['n_total_trials']} trials"
    print(f"harbor: {resolved} truncated trial names resolved from per-trial result.json")
    return rows


def original_rows(op_dir):
    rows = []
    for root, _dirs, files in os.walk(op_dir):
        if "eval_times=3.jsonl" not in files:
            continue
        scenario, domain = os.path.basename(root), os.path.basename(os.path.dirname(root))
        t, a, v = SCENARIO.fullmatch(scenario).groups()
        with open(os.path.join(root, "eval_times=3.jsonl"), encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                rec = json.loads(line)
                task = f"{domain.lower()}-t{t}-a{a}-v{v}-s{rec['seed']}"
                succ = [1.0 if tr["successful"] else 0.0 for tr in rec["trajectories"]]
                assert abs(sum(succ) / len(succ) - rec["average_correct"]) < 1e-9, task
                rows += [(j + 1, task, x) for j, x in enumerate(succ)]
    return rows


def main(download_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    harbor = harbor_rows(download_dir)
    original = original_rows(os.path.join(download_dir, "original_parity"))
    for side, rows in (("harbor", harbor), ("original", original)):
        keys = [(r, t) for r, t, _ in rows]
        assert len(keys) == len(set(keys)), f"duplicate (run, task_id) on {side} side"
    h_ids, o_ids = {t for _, t, _ in harbor}, {t for _, t, _ in original}
    assert h_ids == o_ids, f"task sets differ: {sorted(h_ids ^ o_ids)[:10]}"
    write_csv(os.path.join(out_dir, "harbor.csv"), harbor)
    write_csv(os.path.join(out_dir, "original.csv"), original)
    report("harbor", harbor)
    report("original", original)
    print(f"tasks: harbor={len(h_ids)} original={len(o_ids)} common={len(h_ids & o_ids)}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
