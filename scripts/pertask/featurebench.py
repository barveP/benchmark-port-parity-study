"""Per-task outcomes for the FeatureBench parity experiment (HF adapter folder
``adapters/featurebench``, snapshot adapter ``featurebench``): codex@0.106.0 +
openai/gpt-5-mini, 2 trials x 30 lite-split tasks (26 lv1 + 4 lv2), binary
reward (1 = the task's FAIL_TO_PASS and PASS_TO_PASS tests all pass).

Usage: python -I featurebench.py <download_dir> <out_dir>

<download_dir> mirrors adapters/featurebench/ of the Hugging Face dataset
harborframework/parity-experiments; only results_collection/ is read.
Writes <out_dir>/original.csv and <out_dir>/harbor.csv (run,task_id,reward).

Original side -- results_collection/result_original_trial<N>.json is the
per-attempt report written by FeatureBench's ``fb eval``:
{instance_id: {instance_id: {"resolved": bool, "pass_rate": float,
"n_attempt", "patch_*", "tests_status": {...}}}}.  task_id = the FeatureBench
instance_id verbatim (e.g. "Lightning-AI__pytorch-lightning.126fa6f1
.test_connector.825ef3b1.lv1"); reward = float(resolved).  pass_rate is NOT
used (it is the fraction of tests passing, a secondary metric).

Harbor side -- results_collection/result_harbor_trial<N>.json is NOT a
job-level result.json but a dict {task_name: trial record}, one Harbor
per-trial result.json per task (fields task_name, trial_name, config.agent,
verifier_result.rewards.reward, exception_info, ...).  reward =
verifier_result.rewards.reward (0.0/1.0); no trial raised an exception.
task_name is the untruncated Harbor task slug, so the "__<7 chars>" trial
suffix on trial_name is never needed.  Harbor lower-cased the FeatureBench
instance_ids ("lightning-ai__...", "linkedin__liger-kernel..."); every
lower-cased original id matches a Harbor slug one-to-one (asserted), so
harbor.csv uses the ORIGINAL instance_id as task_id and both files join.

Data defect handled here -- in result_harbor_trial2.json two of the four lv2
records (transformers test_modeling_seggpt, liger-kernel
test_fused_neighborhood_attention) are ORACLE runs (config.agent.name ==
"oracle", model None, a separate job), evidently collected in place of the
codex lv2 rerun records; they carry reward 1.0.  They are not outcomes of the
agent under study, so records whose agent is not the experiment's agent
(codex, taken from the majority of records) are dropped and listed on
stdout.  harbor.csv therefore has 30 rows for run 1 and 28 for run 2; no
value is invented for the two missing cells (the README and the published
run-2 score 5/30 imply the authors counted them as 0).
"""
import csv
import json
import os
import re
import sys
from collections import Counter


def read_original(path):
    """{instance_id: reward} from one fb-eval per-attempt report."""
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    out = {}
    for inst, wrapper in data.items():
        rec = wrapper[inst]  # the report nests each record under its own id
        out[inst] = float(bool(rec["resolved"]))
    return out


def read_harbor(path):
    """({slug: reward}, {slug: agent name}) from one per-task Harbor dict."""
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    rewards, agents = {}, {}
    for slug, rec in data.items():
        assert rec["task_name"] == slug, (path, slug)
        assert rec.get("exception_info") is None, (path, slug)
        rewards[slug] = float(rec["verifier_result"]["rewards"]["reward"])
        agents[slug] = rec["config"]["agent"]["name"]
    return rewards, agents


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
    original, harbor, agents = {}, {}, {}
    for fn in sorted(os.listdir(rc)):
        m = re.fullmatch(r"result_(original|harbor)_trial(\d+)\.json", fn)
        if not m:
            continue
        side, run = m.group(1), int(m.group(2))
        if side == "original":
            original[run] = read_original(os.path.join(rc, fn))
        else:
            harbor[run], agents[run] = read_harbor(os.path.join(rc, fn))

    # Harbor slug -> original instance_id (Harbor lower-cased the ids).
    orig_ids = sorted({i for d in original.values() for i in d})
    by_lower = {i.lower(): i for i in orig_ids}
    assert len(by_lower) == len(orig_ids), "original ids collide when lower-cased"
    slugs = sorted({s for d in harbor.values() for s in d})
    assert set(slugs) == set(by_lower), (
        "harbor slugs != lower-cased original ids",
        sorted(set(slugs) ^ set(by_lower)))

    # Keep only records of the experiment's agent (the majority agent).
    agent = Counter(a for d in agents.values() for a in d.values()).most_common(1)[0][0]
    dropped = [(run, by_lower[s], a) for run, d in sorted(agents.items())
               for s, a in sorted(d.items()) if a != agent]

    print("original.csv (reward = fb eval 'resolved')")
    write_csv(os.path.join(out_dir, "original.csv"),
              [(run, i, rw) for run, d in original.items() for i, rw in d.items()])
    print(f"harbor.csv (task_id = original instance_id; agent kept = {agent!r})")
    write_csv(os.path.join(out_dir, "harbor.csv"),
              [(run, by_lower[s], rw) for run, d in harbor.items()
               for s, rw in d.items() if agents[run][s] == agent])
    print("harbor records dropped because their agent is not the experiment's:")
    for run, inst, a in dropped:
        print(f"  run {run}: {inst} (agent={a!r}, reward={harbor[run][inst.lower()]})")
    print("ids whose Harbor slug differs from the original id (case only):",
          [i for i in orig_ids if i != i.lower()])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
