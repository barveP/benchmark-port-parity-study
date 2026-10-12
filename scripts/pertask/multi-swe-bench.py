"""Per-task outcomes for the Multi-SWE-bench parity experiment (HF adapter
folder ``adapters/multi-swe-bench``, snapshot adapter ``multi-swe-bench``):
codex@0.101.0 + gpt-5-mini, 3 runs x 70 tasks (10 per language x 7
languages: C, C++, Go, Java, JavaScript, Rust, TypeScript), binary reward
(1 = resolved).

Usage: python -I multi-swe-bench.py <download_dir> <out_dir>

<download_dir> mirrors adapters/multi-swe-bench/ of the Hugging Face dataset
harborframework/parity-experiments.  Writes <out_dir>/original.csv and
<out_dir>/harbor.csv (run,task_id,reward); run r holds the 70 tasks of the
seven per-language run-r files.

Original side -- original_parity/<lang>/run<N>/final_report.json (lang in
c, cpp, go, java, js, rust, ts) is a SWE-bench style report:
total_instances / resolved_instances counts and submitted_ids /
completed_ids / resolved_ids / unresolved_ids / error_ids / ... lists.
task_id = the Multi-SWE-bench instance id verbatim, "<org>/<repo>:pr-<N>",
e.g. "jqlang/jq:pr-2133".  reward = 1.0 if the id is in resolved_ids else
0.0 over submitted_ids (js run 1 has one errored/incomplete instance that is
neither resolved nor unresolved; it counts as 0, as in the report's
resolve rate).  results_collection/result_original_<lang>_run<N>.json holds
copies of these reports, but the go, java and rust copies are stale (older
runs, two in a different "codex-agent" format, and rust run 3 is a byte copy
of java run 3) and do not reproduce the published run scores, so the
original_parity/ reports are used.

Harbor side -- results_collection/result_harbor_<lang>_run<N>.json (lang
as above but "typescript" for ts) is a Harbor job-level result.json;
stats.evals[<name>].reward_stats.reward = {"1.0": [trial names], "0.0":
[trial names]}.  Trial names look like "jqlang__jq2133__Tudmxw2": the
"__<7 chars>" trial suffix is stripped, leaving the Harbor task name, which
is the instance id with org and repo lower-cased and stripped of
non-alphanumerics, joined as "<org>__<repo><N>" and cut to 32 characters
(e.g. "anuraghazra/github-readme-stats:pr-3442" ->
"anuraghazra__githubreadmestats34").  harbor.csv uses the ORIGINAL instance
id as task_id so both files join on task_id; the mapping is asserted
one-to-one per language and run.
"""
import csv
import json
import os
import re
import sys

# (original_parity folder, harbor file tag)
LANGS = [("c", "c"), ("cpp", "cpp"), ("go", "go"), ("java", "java"),
         ("js", "js"), ("rust", "rust"), ("ts", "typescript")]
RUNS = (1, 2, 3)
TRIAL_SUFFIX = re.compile(r"__[A-Za-z0-9]+$")
NON_ALNUM = re.compile(r"[^a-z0-9]")


def harbor_name(instance_id):
    """'Kong/insomnia:pr-7734' -> 'kong__insomnia7734' (32-char cap)."""
    repo, num = instance_id.split(":pr-")
    org, name = repo.split("/")
    org, name = NON_ALNUM.sub("", org.lower()), NON_ALNUM.sub("", name.lower())
    return f"{org}__{name}{num}"[:32]


def read_original(path):
    """{instance id: reward} for one language and run."""
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    ids, resolved = d["submitted_ids"], set(d["resolved_ids"])
    assert len(ids) == len(set(ids)) == d["total_instances"], path
    assert resolved <= set(ids) and len(resolved) == d["resolved_instances"], path
    return {i: (1.0 if i in resolved else 0.0) for i in ids}


def read_harbor(path):
    """{harbor task name: reward} for one language and run."""
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    rewards = {}
    for ev in d["stats"]["evals"].values():
        assert not ev.get("exception_stats"), path
        for reward, names in ev["reward_stats"]["reward"].items():
            for name in names:
                task = TRIAL_SUFFIX.sub("", name)
                assert task not in rewards, f"duplicate task {task} in {path}"
                rewards[task] = float(reward)
    assert len(rewards) == d["n_total_trials"], path
    return rewards


def main(download_dir, out_dir):
    original, harbor = [], []
    for run in RUNS:
        for lang, htag in LANGS:
            o = read_original(os.path.join(download_dir, "original_parity", lang,
                                           f"run{run}", "final_report.json"))
            h = read_harbor(os.path.join(download_dir, "results_collection",
                                         f"result_harbor_{htag}_run{run}.json"))
            names = {harbor_name(i): i for i in o}
            assert len(names) == len(o) and set(names) == set(h), (lang, run, set(names) ^ set(h))
            original += [(run, i, r) for i, r in o.items()]
            harbor += [(run, names[n], r) for n, r in h.items()]
    os.makedirs(out_dir, exist_ok=True)
    for fname, rows in (("original.csv", original), ("harbor.csv", harbor)):
        with open(os.path.join(out_dir, fname), "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["run", "task_id", "reward"])
            w.writerows(sorted(rows))
        print(f"{fname}: {len(rows)} rows")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
