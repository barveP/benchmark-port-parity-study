"""Per-task outcomes for the ADE-bench parity experiment (HF adapter folder
``adapters/adebench``, snapshot adapter ``adebench``).

Usage: python -I adebench.py <download_dir> <out_dir>

Reads ``<download_dir>/results_collection/`` and writes ``original.csv`` and
``harbor.csv`` (columns run,task_id,reward) to ``<out_dir>``.

Original side: ``results_origin_trial<k>.json`` = the ade-bench ``results.json``
of run k: ``{"results": [{"task_id": ..., "is_resolved": true|false|null, ...}],
"resolved_ids": [...], "unresolved_ids": [...], "accuracy": float}``.
reward = 1 if is_resolved is true, else 0 (null = agent timeout, listed in
unresolved_ids by the benchmark itself). task_id is taken verbatim, e.g.
``airbnb001``, ``analytics_engineering002.medium``, ``f1003.hard``.

Harbor side: ``result_harbor_trial<k>.json`` = Harbor job-level result.json:
``stats.evals["claude-code__ade-bench"].reward_stats.reward =
{"1.0": [trial names], "0.0": [trial names]}``. Trial names look like
``ade-bench-ana-eng002-medium__gaDhAay``. The ``__<trial>`` suffix and the
``ade-bench-`` prefix are stripped, and the Harbor slug is mapped back to the
benchmark's own task id so the two sides pair up: ``ana-eng`` ->
``analytics_engineering``, trailing ``-medium``/``-hard`` -> ``.medium``/``.hard``.
"""
import csv
import json
import os
import re
import sys


def run_number(path):
    return int(re.search(r"trial(\d+)\.json$", path).group(1))


def harbor_task_id(trial_name):
    slug = trial_name.split("__", 1)[0]
    if slug.startswith("ade-bench-"):
        slug = slug[len("ade-bench-"):]
    if slug.startswith("ana-eng"):
        slug = "analytics_engineering" + slug[len("ana-eng"):]
    return re.sub(r"-(medium|hard)$", r".\1", slug)


def parse_original(path):
    data = json.load(open(path))
    rows = []
    for item in data["results"]:
        resolved = item["is_resolved"]
        if resolved is None:
            print(f"  note: {os.path.basename(path)} {item['task_id']} is_resolved=null "
                  f"(failure_mode={item.get('failure_mode')}); recorded as 0")
        rows.append((item["task_id"], 1.0 if resolved is True else 0.0))
    return rows


def parse_harbor(path):
    data = json.load(open(path))
    rows = []
    for name, ev in data["stats"]["evals"].items():
        if ev.get("n_errors"):
            print(f"  note: {os.path.basename(path)} eval {name} n_errors={ev['n_errors']} "
                  f"exceptions={json.dumps(ev.get('exception_stats'))}")
        for value, trial_names in ev["reward_stats"]["reward"].items():
            rows += [(harbor_task_id(t), float(value)) for t in trial_names]
    return rows


def write_side(files, parser, out_path):
    rows = []
    for path in sorted(files, key=run_number):
        run = run_number(path)
        side_rows = parser(path)
        ids = [t for t, _ in side_rows]
        assert len(ids) == len(set(ids)), f"duplicate task ids in {path}"
        rows += [(run, t, r) for t, r in sorted(side_rows)]
        mean = sum(r for _, r in side_rows) / len(side_rows)
        print(f"  run {run}: {len(side_rows)} tasks, mean reward {mean:.6f} ({100*mean:.2f}%)")
    with open(out_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["run", "task_id", "reward"])
        w.writerows(rows)
    print(f"  wrote {out_path} ({len(rows)} rows)")
    return rows


def main(download_dir, out_dir):
    rc = os.path.join(download_dir, "results_collection")
    names = sorted(os.listdir(rc))
    orig = [os.path.join(rc, n) for n in names if re.fullmatch(r"results_origin_trial\d+\.json", n)]
    harb = [os.path.join(rc, n) for n in names if re.fullmatch(r"result_harbor_trial\d+\.json", n)]
    os.makedirs(out_dir, exist_ok=True)
    print("original:")
    o = write_side(orig, parse_original, os.path.join(out_dir, "original.csv"))
    print("harbor:")
    h = write_side(harb, parse_harbor, os.path.join(out_dir, "harbor.csv"))
    ot, ht = {t for _, t, _ in o}, {t for _, t, _ in h}
    print(f"tasks: original {len(ot)}, harbor {len(ht)}, common {len(ot & ht)}")
    if ot ^ ht:
        print("  unmatched:", sorted(ot ^ ht))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
