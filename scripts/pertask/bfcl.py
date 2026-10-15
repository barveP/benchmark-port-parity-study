"""Per-task outcomes for the BFCL parity experiment (HF adapters/bfcl).

Usage: python -I bfcl.py <download_dir> <out_dir>
<download_dir> is the local mirror of adapters/bfcl/ (results_collection/ and
original_parity/<run>/score/). Stdlib only.

Harbor side (results_collection/result_harbor_<model>_run<k>.json): a JSON list of
trial records; reward = record["verifier_result"]["rewards"]["reward"] (0.0 / 1.0).
The Harbor task name is record["task_name"] without the "harbor/" prefix, e.g.
"bfcl-live-irrelevance-103-3-0" (record["trial_name"] is "<task>__<suffix>", but
Harbor truncates long task names there, so it is only used as a cross-check).

Original side: BFCL's model-output files
results_collection/result_original_<handler>_<model>_run<k>.json (JSONL, one
{"id", "result", ...} per task) list the tasks but carry no correctness. The
per-category score files original_parity/run<k>/score/<handler-dir>/{live,non_live}/
BFCL_v4_<category>_score.json are JSONL whose first line is
{"accuracy", "correct_count", "total_count"} and whose remaining lines are one entry
per FAILED task (with its "id"). reward = 0 if the task id appears as a failure,
else 1. The script checks sum(total_count) == number of ids and
sum(correct_count) == number of passes.

Task ids: the BFCL id exactly as in the original files ("live_irrelevance_103-3-0").
Harbor renamed each id to "bfcl-" + id.replace("_", "-"); that rename is inverted
(and verified to be a bijection over the task set) so both CSVs share task ids.

Outputs (columns run,task_id,reward): original.csv / harbor.csv are the primary
comparison (CodexWriteFileHandler vs Harbor) for gpt-5-mini; the same for
gpt-4o-mini goes to original__gpt-4o-mini.csv / harbor__gpt-4o-mini.csv; the
supplementary original handlers go to original_llm__<model>.csv (CodexHandler,
"codex") and original_json__<model>.csv (CodexStdoutJsonHandler, "codexfile").
"""
import csv
import glob
import json
import os
import sys

MODELS = {"gpt5mini": "gpt-5-mini", "gpt4omini": "gpt-4o-mini"}
# results_collection handler tag -> (score directory prefix, output file prefix)
HANDLERS = {"codexwritefile": ("codex-writefile", "original"),
            "codex": ("codex", "original_llm"),
            "codexfile": ("codex-file", "original_json")}
RUNS = (1, 2, 3)


def fmt(r):
    r = float(r)
    return str(int(r)) if r.is_integer() else repr(r)


def write_csv(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["run", "task_id", "reward"])
        for run, tid, r in sorted(rows, key=lambda x: (x[0], x[1])):
            w.writerow([run, tid, fmt(r)])
    by_run = {}
    for run, _, r in rows:
        by_run.setdefault(run, []).append(float(r))
    means = {k: 100 * sum(v) / len(v) for k, v in sorted(by_run.items())}
    print(f"{os.path.basename(path)}: {len(rows)} rows, run means % = "
          + ", ".join(f"run{k}: {m:.2f} (n={len(by_run[k])})" for k, m in means.items()))


def original_ids(rc, handler, model, run):
    p = os.path.join(rc, f"result_original_{handler}_{model}_run{run}.json")
    if not os.path.exists(p):
        return None
    with open(p) as f:
        return [json.loads(l)["id"] for l in f if l.strip()]


def original_rows(dl, handler, model, run, ids):
    score_dir = os.path.join(dl, "original_parity", f"run{run}", "score",
                             f"{HANDLERS[handler][0]}-{MODELS[model]}")
    files = sorted(glob.glob(os.path.join(score_dir, "*", "BFCL_v4_*_score.json")))
    if not files:
        print(f"  WARNING no score files under {score_dir}; skipped")
        return None
    total = correct = 0
    failed = set()
    for p in files:
        with open(p) as f:
            lines = [json.loads(l) for l in f if l.strip()]
        total += lines[0]["total_count"]
        correct += lines[0]["correct_count"]
        for entry in lines[1:]:
            if entry.get("valid", False):
                print(f"  WARNING {os.path.basename(p)}: non-failure entry {entry.get('id')}")
            failed.add(entry["id"])
    if len(ids) != len(set(ids)):
        print(f"  WARNING duplicated ids in result file ({len(ids) - len(set(ids))})")
    unknown = failed - set(ids)
    if unknown:
        print(f"  WARNING {len(unknown)} failed ids not in result file: {sorted(unknown)[:5]}")
    rows = [(run, tid, 0 if tid in failed else 1) for tid in ids]
    passes = sum(r for _, _, r in rows)
    if total != len(ids) or correct != passes:
        print(f"  WARNING score totals {correct}/{total} vs reconstructed {passes}/{len(ids)}")
    return rows


def harbor_rows(rc, model, run, id_map):
    p = os.path.join(rc, f"result_harbor_{model}_run{run}.json")
    if not os.path.exists(p):
        return None
    with open(p) as f:
        recs = json.load(f)
    rows = []
    for x in recs:
        # task_name is "harbor/<task>"; trial_name is "<task>__<suffix>" but Harbor
        # truncates long task names there, so the suffix-stripped form is only a check.
        name = x["task_name"].split("/", 1)[-1]
        short = x["trial_name"].split("__", 1)[0]
        if not name.startswith(short):
            print(f"  WARNING run{run}: trial_name {short!r} does not match task {name!r}")
        if x.get("exception_info"):
            print(f"  note: run{run} {name} has exception_info (reward still recorded)")
        reward = x["verifier_result"]["rewards"]["reward"]
        rows.append((run, id_map.get(name, name), reward))
    missing = [n for _, n, _ in rows if n not in id_map.values()]
    if missing:
        print(f"  WARNING {len(missing)} Harbor names without a BFCL id mapping: {missing[:5]}")
    return rows


def main(dl, out):
    rc = os.path.join(dl, "results_collection")
    os.makedirs(out, exist_ok=True)
    for model, model_name in MODELS.items():
        suffix = "" if model == "gpt5mini" else f"__{model_name}"
        print(f"== {model_name}")
        ids = None
        for handler, (_, prefix) in HANDLERS.items():
            rows = []
            for run in RUNS:
                run_ids = original_ids(rc, handler, model, run)
                if run_ids is None:
                    print(f"  no result file for {handler} run{run}")
                    continue
                ids = ids or run_ids
                r = original_rows(dl, handler, model, run, run_ids)
                if r:
                    rows += r
            if rows:
                name = prefix + (suffix if prefix == "original" else f"__{model_name}")
                write_csv(os.path.join(out, name + ".csv"), rows)
        # Harbor renamed "live_irrelevance_103-3-0" to "bfcl-live-irrelevance-103-3-0".
        id_map = {"bfcl-" + i.replace("_", "-"): i for i in (ids or [])}
        if len(id_map) != len(ids or []):
            print("  WARNING Harbor rename is not injective on this task set")
        rows = []
        for run in RUNS:
            r = harbor_rows(rc, model, run, id_map)
            if r:
                rows += r
        if rows:
            write_csv(os.path.join(out, "harbor" + suffix + ".csv"), rows)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
