"""Per-task outcomes for the AA-LCR Harbor parity experiment.

Usage: python -I aa-lcr.py <download_dir> <out_dir>

Input (Harbor side only -- this adapter has no original-side per-task data;
its README says original_parity/ is empty because AA-LCR has no public harness,
and the "original" number is a leaderboard score):
    <download_dir>/results_collection/result_harbor_run<N>.json
Each file is a Harbor job-level result.json with
    stats.evals[<eval name>].reward_stats.reward = {"<reward>": [trial names]}
The four files are NOT repeated runs of one setup; each is a different
(agent, model) experiment with a single run (per the adapter README):
    run1 codex@0.117.0 + gpt-5-mini        (eval codex__gpt-5-mini__aa-lcr)
    run2 claude-code@2.1.104 + haiku-4-5   (eval claude-code__aa-lcr)
    run3 terminus-2@2.0.0 + gpt-5-mini     (eval terminus-2__gpt-5-mini__aa-lcr)
    run4 terminus-2@2.0.0 + haiku-4-5      (eval terminus-2__claude-haiku-4-5__aa-lcr)
The CSV's `run` column is the <N> from the file name, so run == experiment.

Task ids: trial names look like "aa-lcr-16__Ba7ffAW"; the part after "__" is
a per-trial random suffix and is stripped, leaving "aa-lcr-16".

Output: <out_dir>/harbor.csv with columns run,task_id,reward (reward 0.0/1.0).
No original.csv is written.  A per-run summary is printed for validation.
"""
import csv
import json
import re
import sys
from pathlib import Path


def main(download_dir, out_dir):
    rc = Path(download_dir) / "results_collection"
    files = sorted(rc.glob("result_harbor_run*.json"),
                   key=lambda p: int(re.search(r"run(\d+)", p.name).group(1)))
    rows = []
    for path in files:
        run = int(re.search(r"run(\d+)", path.name).group(1))
        data = json.loads(path.read_text())
        evals = data["stats"]["evals"]
        if len(evals) != 1:
            raise SystemExit(f"{path.name}: expected 1 eval, found {list(evals)}")
        (name, ev), = evals.items()
        seen = set()
        for reward_str, trials in ev["reward_stats"]["reward"].items():
            reward = float(reward_str)
            for trial in trials:
                task_id = trial.split("__", 1)[0]
                if task_id in seen:
                    raise SystemExit(f"{path.name}: duplicate task {task_id}")
                seen.add(task_id)
                rows.append((run, task_id, reward))
        n = len(seen)
        mean = sum(r for rr, _, r in rows if rr == run) / n
        print(f"run {run}: eval={name} n_tasks={n} mean={mean:.4f} "
              f"({mean*100:.1f}%) n_errors={ev.get('n_errors')}")

    rows.sort(key=lambda r: (r[0], int(r[1].rsplit("-", 1)[1])))
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "harbor.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["run", "task_id", "reward"])
        w.writerows(rows)
    print(f"wrote {out / 'harbor.csv'}: {len(rows)} rows")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])
