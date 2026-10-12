"""Per-task outcomes for the livecodebench parity experiment (claude-code@2.0.32, claude-haiku-4-5,
TB adapter vs Harbor adapter, 100 tasks of release_v6, 4 runs per side).

Usage: python -I livecodebench.py <download_dir> <out_dir>

<download_dir> mirrors adapters/livecodebench/ of the Hugging Face dataset
harborframework/parity-experiments.  Writes <out_dir>/original.csv and <out_dir>/harbor.csv
(columns run,task_id,reward).  Both sides: 4 runs x 100 tasks, binary reward.  The run number is
the trailing integer of the HF file name (result_original_trail<k>.json -- sic, "trail" -- and
result_harbor_trial<k>.json).  The 100 task ids are the same on both sides: LiveCodeBench
question ids such as "abc333_a", "arc195_c", "3608", "1873_d".

Original side (terminal-bench adapter) -- results_collection/result_original_trail<k>.json is a
  terminal-bench job results file: {"results": [{task_id, is_resolved, failure_mode,
  parser_results, ...}], n_resolved, resolved_ids, unresolved_ids, accuracy}.
  reward = 1.0 if is_resolved is true else 0.0.  is_resolved is null for trials whose verifier
  timed out or whose output could not be parsed (failure_mode test_timeout / parse_error); these
  are counted as unresolved, exactly as the file's own accuracy = n_resolved / 100 does.
  task_id = the "task_id" field verbatim (no trial suffix on this side).

Harbor side -- results_collection/result_harbor_trial<k>.json is the Harbor job-level result.
  Rewards live in stats.evals[<eval name>].reward_stats.reward = {"<reward>": [trial names]}.
  Trial names look like "abc333_a__d3XHriC": the "__<suffix>" trial id is stripped.  Trials that
  appear only under exception_stats (VerifierTimeoutError / AgentTimeoutError, 24-29 per run) get
  reward 0.0, which reproduces the file's own metrics mean = (# reward 1.0) / 100.  A few
  AgentTimeoutError trials also appear under reward 0.0; the reward value wins (it is 0 anyway).
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
        m = re.match(r"result_original_tr[ai]+l(\d+)\.json$", fn)
        if not m:
            continue
        run = int(m.group(1))
        with open(os.path.join(rc, fn), encoding="utf-8") as fh:
            data = json.load(fh)
        n_null = 0
        for rec in data["results"]:
            resolved = rec.get("is_resolved")
            n_null += resolved is None
            rows.append((run, rec["task_id"], 1.0 if resolved is True else 0.0))
        print(f"original run {run}: n_results={len(data['results'])} is_resolved_null={n_null} "
              f"file_accuracy={data.get('accuracy')}")
    return rows


def harbor_rows(download_dir):
    rc = os.path.join(download_dir, "results_collection")
    rows = []
    for fn in sorted(os.listdir(rc)):
        m = re.match(r"result_harbor_trial(\d+)\.json$", fn)
        if not m:
            continue
        run = int(m.group(1))
        with open(os.path.join(rc, fn), encoding="utf-8") as fh:
            data = json.load(fh)
        for name, ev in data["stats"]["evals"].items():
            print(f"harbor run {run}: eval={name} n_trials={ev['n_trials']} n_errors={ev['n_errors']} "
                  f"file_mean={ev['metrics'][0].get('mean')}")
            seen = set()
            for reward, names in ev["reward_stats"]["reward"].items():
                for tname in names:
                    rows.append((run, task_id_from_trial_name(tname), float(reward)))
                    seen.add(tname)
            for names in ev.get("exception_stats", {}).values():
                for tname in names:
                    if tname not in seen:
                        rows.append((run, task_id_from_trial_name(tname), 0.0))
                        seen.add(tname)
    return rows


def task_id_from_trial_name(tname):
    return tname.split("__", 1)[0]  # strip the per-trial "__<suffix>"


def write(rows, path):
    rows.sort(key=lambda r: (r[0], r[1]))
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["run", "task_id", "reward"])
        w.writerows(rows)
    for run in sorted({r[0] for r in rows}):
        rr = [r[2] for r in rows if r[0] == run]
        ids = [r[1] for r in rows if r[0] == run]
        print(f"{os.path.basename(path)} run {run}: n_tasks={len(rr)} unique_ids={len(set(ids))} "
              f"mean={sum(rr) / len(rr):.4f}")


def main(download_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    write(original_rows(download_dir), os.path.join(out_dir, "original.csv"))
    write(harbor_rows(download_dir), os.path.join(out_dir, "harbor.csv"))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
