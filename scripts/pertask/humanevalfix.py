"""Per-task outcomes for the humanevalfix parity experiments (openhands@v0.60.0; two models).

Usage: python -I humanevalfix.py <download_dir> <out_dir>

<download_dir> mirrors adapters/humanevalfix/ of the Hugging Face dataset
harborframework/parity-experiments.  Writes <out_dir>/original.csv and <out_dir>/harbor.csv
(columns run,task_id,reward).  Both sides: 6 runs x 164 tasks, binary reward.  The run number
is the "trial<k>" token of the HF file/folder name on BOTH sides, and on both sides runs 1-3 are
gpt-5-mini and runs 4-6 are gpt-4o-mini (the snapshot JSON lists these as two experiments with 3
trials each; the per-run model is read from the files and printed).

Original side -- results_collection/result_original_trial<k>.json is an OpenHands output.jsonl
  (one JSON record per line, 164 lines).  reward = test_result.result["pass@1"] (0.0/1.0).  A few
  records hit an infrastructure failure (container exited, connection reset) and have
  test_result == {} with an "error" string; they get reward 0.0, which reproduces the published
  passes/164 scores.  task_id = the "instance_id" field verbatim, the HumanEvalPack id "Python/<n>".

Harbor side -- harbor_parity/result_harbor_trial<k>/result.json is the Harbor job-level result
  (the results_collection/result_harbor_trial<k>.json copies are 0-byte files and are skipped).
  Rewards live in stats.evals[<eval name>].reward_stats.reward = {"<reward>": [trial names]}.
  Trial names look like "python-84__RAF3htv": the "__<suffix>" trial id is stripped, leaving the
  Harbor task name "python-84", which is then renamed to the HumanEvalPack id "Python/84" so the
  two sides share one key.  Trials listed only under exception_stats would get 0.0 (there are none).
"""
import csv
import json
import os
import re
import sys


def original_rows(download_dir):
    rc = os.path.join(download_dir, "results_collection")
    rows = []
    for fn in sorted(os.listdir(rc)):
        m = re.match(r"result_original_trial(\d+)\.json$", fn)
        if not m:
            continue
        run = int(m.group(1))
        n_missing, models = 0, set()
        with open(os.path.join(rc, fn), encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                res = (rec.get("test_result") or {}).get("result")
                if isinstance(res, dict) and "pass@1" in res:
                    reward = float(res["pass@1"])
                else:
                    reward = 0.0
                    n_missing += 1
                rows.append((run, rec["instance_id"], reward))
                models.add(((rec.get("metadata") or {}).get("llm_config") or {}).get("model"))
        print(f"original run {run}: model={sorted(map(str, models))} records_without_result={n_missing}")
    return rows


def harbor_rows(download_dir):
    hp = os.path.join(download_dir, "harbor_parity")
    rows = []
    for d in sorted(os.listdir(hp)):
        m = re.match(r"result_harbor_trial(\d+)$", d)
        p = os.path.join(hp, d, "result.json")
        if not m or not os.path.isfile(p):
            continue
        run = int(m.group(1))
        with open(p) as fh:
            data = json.load(fh)
        for name, ev in data["stats"]["evals"].items():
            print(f"harbor run {run}: eval={name} n_trials={ev['n_trials']} n_errors={ev['n_errors']}")
            seen = set()
            for reward, names in ev["reward_stats"]["reward"].items():
                for tname in names:
                    rows.append((run, task_id_from_trial_name(tname), float(reward)))
                    seen.add(tname)
            for names in ev.get("exception_stats", {}).values():
                for tname in names:
                    if tname not in seen:
                        rows.append((run, task_id_from_trial_name(tname), 0.0))
    return rows


def task_id_from_trial_name(tname):
    task = tname.split("__", 1)[0]  # strip the per-trial "__<suffix>"
    m = re.match(r"python-(\d+)$", task)
    return f"Python/{m.group(1)}" if m else task


def write(rows, path):
    rows.sort(key=lambda r: (r[0], int(r[1].rsplit("/", 1)[-1])))
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["run", "task_id", "reward"])
        w.writerows(rows)
    for run in sorted({r[0] for r in rows}):
        rr = [r[2] for r in rows if r[0] == run]
        print(f"{os.path.basename(path)} run {run}: n_tasks={len(rr)} mean={sum(rr) / len(rr):.4f}")


def main(download_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    write(original_rows(download_dir), os.path.join(out_dir, "original.csv"))
    write(harbor_rows(download_dir), os.path.join(out_dir, "harbor.csv"))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
