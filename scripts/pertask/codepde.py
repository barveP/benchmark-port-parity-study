"""Per-task outcomes for the codepde parity experiments.

Usage: python -I codepde.py <download_dir> <out_dir>

The benchmark has 5 tasks, one per PDE family: codepde-advection, codepde-burgers,
codepde-cns1d, codepde-darcy, codepde-reacdiff1d.  A task passes when the solver's
nRMSE over the family's 100 test instances is < 0.05 (the threshold printed by the
Harbor verifier, "Success threshold: 0.05"; the original CodePDE evaluator only
prints nRMSE and defines no threshold itself).

Harbor side (written to <out_dir>/harbor.csv; terminus-2, claude-haiku-4-5, 8 attempts):
  <download_dir>/results_collection/result_harbor_trial<k>.json, one per-trial Harbor
  result.json (40 files = 5 tasks x 8 attempts; the <k> is NOT the attempt number).
  task_id = the file's "task_name" (the trial_name "codepde-darcy__s8GoNMQ" carries a
  "__<suffix>" trial id, which is dropped).  reward = verifier_result.rewards.reward;
  trials that ended in an exception (VerifierTimeoutError, verifier_result null) count
  as 0.0, which matches harbor_parity/<trial>/verifier/reward.txt when present.  The
  job ran its 8 attempts as sequential sweeps over the 5 tasks, so run = rank of the
  trial's "started_at" within its task (1..8).

Original side (written to <out_dir>/original.csv; CodePDE scaffolding, o4-mini, 32 rounds):
  <download_dir>/original_parity/codepde-<pde>/test_results.csv with columns
  round,nRMSE,elapsed_time,convergence_rate,num_trial and rows round=0..31.  nRMSE is a
  float or "failed"/"nan"/"inf".  task_id = the folder name; run = round + 1;
  reward = 1.0 if nRMSE parses to a finite value < 0.05 else 0.0.
"""
import csv
import json
import math
import os
import sys

NRMSE_PASS_THRESHOLD = 0.05


def harbor_rows(download_dir):
    rc = os.path.join(download_dir, "results_collection")
    trials = []
    for fn in sorted(os.listdir(rc)):
        if not (fn.startswith("result_harbor_trial") and fn.endswith(".json")):
            continue
        with open(os.path.join(rc, fn)) as fh:
            d = json.load(fh)
        vr = d.get("verifier_result")
        reward = 0.0 if vr is None else float(vr["rewards"]["reward"])
        trials.append((d["task_name"], d["started_at"], d["trial_name"], reward))
    rows = []
    for task in sorted({t[0] for t in trials}):
        mine = sorted(t for t in trials if t[0] == task)  # sort by started_at
        for run, (_, _, _, reward) in enumerate(mine, start=1):
            rows.append((run, task, reward))
    return rows


def original_rows(download_dir):
    op = os.path.join(download_dir, "original_parity")
    rows = []
    for task in sorted(os.listdir(op)):
        path = os.path.join(op, task, "test_results.csv")
        if not os.path.isfile(path):
            continue
        with open(path, newline="") as fh:
            for rec in csv.DictReader(fh):
                try:
                    nrmse = float(rec["nRMSE"])
                except ValueError:  # "failed"
                    nrmse = math.inf
                ok = math.isfinite(nrmse) and nrmse < NRMSE_PASS_THRESHOLD
                rows.append((int(rec["round"]) + 1, task, 1.0 if ok else 0.0))
    return rows


def write(rows, path, label):
    rows.sort()
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["run", "task_id", "reward"])
        w.writerows(rows)
    for run in sorted({r[0] for r in rows}):
        rr = [r[2] for r in rows if r[0] == run]
        print(f"{label} run {run}: n_tasks={len(rr)} mean={sum(rr)/len(rr):.4f}")


def main(download_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    write(harbor_rows(download_dir), os.path.join(out_dir, "harbor.csv"), "harbor")
    write(original_rows(download_dir), os.path.join(out_dir, "original.csv"), "original")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
