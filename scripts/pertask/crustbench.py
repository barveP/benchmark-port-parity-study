"""Per-task outcomes for the CRUST-bench parity experiment (HF adapter folder
``adapters/crust-bench``, snapshot adapter ``crustbench``): codex@0.77.0 +
gpt-5-nano, 3 runs x 100 C-to-Rust transpilation tasks, binary reward
(1 = the transpiled Rust project passes every ``cargo test``).

Usage: python -I crustbench.py <download_dir> <out_dir>

<download_dir> mirrors adapters/crust-bench/ of the Hugging Face dataset
harborframework/parity-experiments; only results_collection/ is read.
Writes <out_dir>/original.csv and <out_dir>/harbor.csv (run,task_id,reward).

Original side -- results_collection/result_original_trial<N>.csv is the
batch_results.csv written by CRUST-bench's scripts/codex_cli/verify_batch.py
(a byte-identical copy sits in original_parity/codex_cli_batch_100_trial<N>/).
Columns: benchmark,reward,verify_exit,seconds,attempts,output_dir,job_log,
codex_log,run_log,error.  task_id = ``benchmark`` verbatim: the CRUST-bench
project (CBench directory) name, e.g. "2DPartInt", "42-Kocaeli-Printf";
reward = ``reward`` (0/1).  Each file has 99 rows: project "impcheck" has no
row in any run, so it gets no original row here either (the published
original score is passes/100, i.e. it was counted as a failure).

Harbor side -- results_collection/result_harbor_trial<N>.json is a Harbor
job-level result.json; stats.evals["codex__gpt-5-nano__crustbench"]
.reward_stats.reward = {"1.0": [trial names], "0.0": [trial names]}.  Trial
names look like "crustbench-libpsbt__9zGw8z8": the "__<7 chars>" trial suffix
is stripped, then the "crustbench-" dataset prefix, leaving the Harbor task
slug ("libpsbt").  Trials that raised (exception_stats: DaytonaError,
VerifierTimeoutError) have no reward entry; they are written with reward 0.0,
which is how Harbor's own metrics.mean counts them (denominator
n_total_trials = 100).

Task-id pairing -- a Harbor slug is the original project name lower-cased
with "_" -> "-", except two that were truncated ("c-blind-rsa-signature" for
"c-blind-rsa-signatures", "genetic-neural-networ" for
"Genetic-neural-network-for-simple-control").  harbor.csv therefore uses the
ORIGINAL project name as task_id wherever the slug maps (exact normalised
match, else unique normalised-prefix match; one-to-one is asserted) to a name
in the original CSVs, so both files join on task_id.  The one slug with no
original row ("impcheck") is kept as the slug.
"""
import csv
import json
import os
import re
import sys

TRIAL_SUFFIX = re.compile(r"__[A-Za-z0-9]+$")
PREFIX = "crustbench-"


def norm(name):
    return name.lower().replace("_", "-")


def slug(trial_name):
    s = TRIAL_SUFFIX.sub("", trial_name)
    return s[len(PREFIX):] if s.startswith(PREFIX) else s


def read_original(path):
    """{project name: reward} from one verify_batch.py CSV."""
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    out = {r["benchmark"]: float(r["reward"]) for r in rows}
    assert len(out) == len(rows), f"duplicate benchmark names in {path}"
    return out


def read_harbor(path):
    """({slug: reward}, {slug: exception name}) from one Harbor result.json."""
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    rewards, errors = {}, {}
    for ev in data["stats"]["evals"].values():
        for reward, names in ev["reward_stats"]["reward"].items():
            for name in names:
                rewards[slug(name)] = float(reward)
        for exc, names in ev.get("exception_stats", {}).items():
            for name in names:
                errors[slug(name)] = exc
    for s in errors:
        rewards.setdefault(s, 0.0)  # errored trial: Harbor scores it 0
    return rewards, errors


def slug_to_original(slugs, originals):
    by_norm = {norm(o): o for o in originals}
    assert len(by_norm) == len(originals), "original names collide after normalising"
    mapping = {}
    for s in slugs:
        if s in by_norm:
            mapping[s] = by_norm[s]
        else:
            cands = [o for n, o in by_norm.items() if n.startswith(s)]
            if len(cands) == 1:
                mapping[s] = cands[0]
    assert len(set(mapping.values())) == len(mapping), "slug -> original not one-to-one"
    return mapping


def write_csv(path, rows):
    rows.sort()
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["run", "task_id", "reward"])
        w.writerows(rows)
    for run in sorted({r for r, _, _ in rows}):
        vals = [x for r, _, x in rows if r == run]
        print(f"  run {run}: n_tasks={len(vals)} n_pass={int(sum(vals))} "
              f"mean={sum(vals) / len(vals):.4f}")


def main(download_dir, out_dir):
    rc = os.path.join(download_dir, "results_collection")
    os.makedirs(out_dir, exist_ok=True)
    original, harbor, harbor_errors = {}, {}, {}
    for fn in sorted(os.listdir(rc)):
        m = re.fullmatch(r"result_(original|harbor)_trial(\d+)\.(csv|json)", fn)
        if not m:
            continue
        side, run = m.group(1), int(m.group(2))
        if side == "original":
            original[run] = read_original(os.path.join(rc, fn))
        else:
            harbor[run], harbor_errors[run] = read_harbor(os.path.join(rc, fn))

    orig_names = sorted({n for d in original.values() for n in d})
    slugs = sorted({s for d in harbor.values() for s in d})
    mapping = slug_to_original(slugs, orig_names)

    print("original.csv")
    write_csv(os.path.join(out_dir, "original.csv"),
              [(run, name, rw) for run, d in original.items() for name, rw in d.items()])
    print("harbor.csv (task_id = original project name where the slug maps)")
    write_csv(os.path.join(out_dir, "harbor.csv"),
              [(run, mapping.get(s, s), rw) for run, d in harbor.items() for s, rw in d.items()])

    print("harbor trials with an exception (written as reward 0.0):")
    for run, errs in sorted(harbor_errors.items()):
        for s, exc in sorted(errs.items()):
            print(f"  run {run}: {mapping.get(s, s)} ({exc})")
    print("slugs that are not simply lower-case/_->- of an original name:")
    for s, o in sorted(mapping.items()):
        if s != norm(o):
            print(f"  {s!r} -> {o!r}")
    print("harbor slugs with no original row:", sorted(set(slugs) - set(mapping)))
    print("original names with no harbor task:", sorted(set(orig_names) - set(mapping.values())))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
