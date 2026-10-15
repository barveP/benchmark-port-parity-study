"""Per-task outcomes for the QuixBugs parity experiment (codex@0.77.0, gpt-5-mini-2025-08-07;
Terminal-Bench adapter vs Harbor adapter, 3 runs x 80 tasks each, binary reward).

Usage: python -I quixbugs.py <download_dir> <out_dir>

<download_dir> mirrors adapters/quixbugs/ of the Hugging Face dataset
harborframework/parity-experiments.  Writes <out_dir>/original.csv and <out_dir>/harbor.csv
(columns run,task_id,reward).  The run number is the "trial<k>" token of the file name on both
sides (it is also start-time order).  The other experiment in the snapshot JSON (claude-code /
claude-3-7-sonnet, original QuixBugs vs Terminal-Bench, 5 runs) has no files on HF.

Original side -- results_collection/result_original_trial<k>.json is a Terminal-Bench run summary
  ("original" here means the Terminal-Bench adapter, i.e. tb_adapter_runs in the snapshot).
  Per task: "results": [{"task_id": ..., "is_resolved": bool, ...}, ...]; reward = 1.0 if
  is_resolved else 0.0; task_id is taken verbatim, e.g. "quixbugs-python-bitcount".

Harbor side -- results_collection/result_harbor_trial<k>.json is the Harbor job-level result with
  stats.evals[<eval name>].reward_stats.reward = {"<reward>": [trial names]}.  A trial name is
  "<task name truncated to 32 chars>__<7-char id>"; the "__<id>" suffix is stripped.  Because of
  the truncation, shortest_path_length / shortest_path_lengths (Python and Java) collapse to one
  prefix, so every prefix is expanded back to the full task name: from the per-trial file
  harbor_parity/<run>/<trial name>/result.json ("task_name"; needed only for those 4 trials
  per run) when present, otherwise by unique prefix match against the original-side task ids
  (both sides use the same "quixbugs-<lang>-<program>" ids).  An unresolvable prefix is kept
  as is and reported on stderr.
"""
import csv
import glob
import json
import os
import re
import sys

TRUNC = 32  # Harbor truncates the task-name part of a trial name to this many characters


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def trial_files(download_dir, side):
    pat = os.path.join(download_dir, "results_collection", f"result_{side}_trial*.json")
    return sorted(glob.glob(pat), key=lambda p: int(re.search(r"trial(\d+)\.json$", p).group(1)))


def original_rows(download_dir):
    rows = []
    for run, path in enumerate(trial_files(download_dir, "original"), 1):
        for r in load(path)["results"]:
            rows.append((run, r["task_id"], 1.0 if r["is_resolved"] else 0.0))
    return rows


def harbor_rows(download_dir, known_ids):
    full_name = {}  # trial name -> full task name, from the per-trial result.json files present
    for p in glob.glob(os.path.join(download_dir, "harbor_parity", "*", "*", "result.json")):
        r = load(p)
        full_name[r["trial_name"]] = r["task_name"]
    rows = []
    for run, path in enumerate(trial_files(download_dir, "harbor"), 1):
        (ev,) = load(path)["stats"]["evals"].values()
        for reward, trial_names in ev["reward_stats"]["reward"].items():
            for tn in trial_names:
                prefix = tn.split("__")[0]
                tid = full_name.get(tn)
                if tid is None:
                    cands = [k for k in known_ids if k[:TRUNC] == prefix]
                    tid = cands[0] if len(cands) == 1 else prefix
                    if len(cands) != 1:
                        print(f"warning: run {run}: {tn!r} has {len(cands)} candidates; kept {prefix!r}", file=sys.stderr)
                elif tid[:TRUNC] != prefix:
                    print(f"warning: run {run}: {tn!r} resolved to unrelated name {tid!r}", file=sys.stderr)
                rows.append((run, tid, float(reward)))
    return rows


def write(rows, path):
    rows.sort()
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["run", "task_id", "reward"])
        w.writerows(rows)
    keys = [(r, t) for r, t, _ in rows]
    if len(keys) != len(set(keys)):
        print(f"warning: duplicate (run, task_id) rows in {path}", file=sys.stderr)
    for run in sorted({r for r, _, _ in rows}):
        rr = [x for r, _, x in rows if r == run]
        print(f"{os.path.basename(path)} run {run}: n={len(rr)} mean={sum(rr) / len(rr):.4f}")


def main():
    download_dir, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    orig = original_rows(download_dir)
    write(orig, os.path.join(out_dir, "original.csv"))
    write(harbor_rows(download_dir, sorted({t for _, t, _ in orig})), os.path.join(out_dir, "harbor.csv"))


if __name__ == "__main__":
    main()
