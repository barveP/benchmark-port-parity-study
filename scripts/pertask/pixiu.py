"""Per-task outcomes for the PIXIU parity experiment (HF adapters/pixiu).

Usage: python -I pixiu.py <download_dir> <out_dir>
<download_dir> is the local mirror of adapters/pixiu/ (results_collection/ and
harbor_parity/running_records/). Stdlib only; nothing in <download_dir> is executed.
Experiment: agent codex@0.75.0, model gpt-5-mini-2026-03-01; 29 PIXIU subsets
(cra-ccf, en-fpb, flare-ner, ...) x 15 samples = 435 tasks, 3 trials per side.

Harbor side: harbor_parity/running_records/trial<k>/pixiu-<subset>-parity/result.json,
the Harbor job-level result.json: stats.evals["codex__<subset>"].reward_stats.reward =
{"<reward>": [trial names...]}. These are the jobs the published Harbor metrics were
computed from. results_collection/result_harbor_<subset>_trial<k>.json holds an older
copy of the same jobs (before some trials were re-run) and is used only as a fallback.
Trial names are "<task name>__<7-char suffix>", e.g. "pixiu-fpb-fpb3876__jKHTZJj";
the suffix after "__" is stripped, so task_id = the Harbor task name. The reward is
0/1 for classification/QA/finred, a fraction for the labeling and TSA subsets, and
all 0.0 for ectsum/edtsum/finqa. Subset flare-australian is dropped: its Harbor task
names collapse to two values (australian00000/00001) across 15 trials, so the trials
cannot be attributed to tasks.

Original side: results_collection/result_original_<subset>_trial<k>.json, the
lm-eval-harness "write_out" file written by PIXIU's evaluator: a list of 15 per-doc
records {doc_id, prompt_0, logit_0, truth, pred, gold, <metric fields>}. The per-doc
reward is the record's "acc" field (0/1, 19 subsets); for flare-headlines it is
1 if pred == gold in the "avg_f1" tuple "(<category>, <pred>, <gold>, [...])". The
other 9 subsets (tsa, ner, finer-ord, cd, fnxl, fsrl, finred, ectsum, edtsum) store
only (prediction, gold) payloads per doc, not a per-doc score, and are left out.
The write_out file has no task name, only doc_id = 0..14 in dataset order, so
task_id is built from the Harbor naming of the same subset: the Harbor names carry
15 consecutive dataset indices (e.g. fpb3876..fpb3890), and doc_id k is mapped to
<prefix><min_index + k>, zero-padded like the Harbor names. This assumes both sides
evaluated the same 15 consecutive samples in dataset order; it was spot-checked by
comparing the gold labels in the Harbor verifier/metrics.json files (pred_gold_pair)
with the write_out "gold" fields for a few subsets (all 15 agree in each).

Outputs <out_dir>/original.csv and <out_dir>/harbor.csv with columns
run,task_id,reward (run = trial number). Run means are printed per subset so they
can be checked against the published per-subset run scores.
"""
import ast
import csv
import json
import os
import re
import sys

RUNS = (1, 2, 3)
SUBSETS = (
    "cra-ccf", "cra-ccfraud", "en-forecasting-travelinsurance", "en-fpb",
    "finben-finer-ord", "finben-fomc", "flare-australian", "flare-causal20-sc",
    "flare-cd", "flare-cfa", "flare-ectsum", "flare-edtsum", "flare-finqa",
    "flare-finred", "flare-fiqasa", "flare-fnxl", "flare-fsrl", "flare-german",
    "flare-headlines", "flare-ma", "flare-mlesg", "flare-multifin-en", "flare-ner",
    "flare-sm-acl", "flare-sm-bigdata", "flare-sm-cikm", "flare-tatqa", "flare-tsa",
    "taiwan",
)


def harbor_trials(path):
    """[(task_id, reward)] from a Harbor job-level result.json (suffix stripped)."""
    with open(path) as f:
        evals = json.load(f)["stats"]["evals"]
    (_, ev), = evals.items()
    trials = [(t.split("__", 1)[0], float(r))
              for r, ids in ev["reward_stats"]["reward"].items() for t in ids]
    if len(trials) != ev["n_trials"]:
        print(f"  WARNING {path}: {len(trials)} trials listed vs n_trials={ev['n_trials']}")
    return trials


def original_rewards(path, subset):
    """{doc_id: reward} from a PIXIU write_out file, or None if no per-doc score."""
    with open(path) as f:
        docs = json.load(f)
    out = {}
    for d in docs:
        if "acc" in d:
            r = float(d["acc"])
        elif subset == "flare-headlines":
            _, pred, gold, _ = ast.literal_eval(d["avg_f1"])
            r = float(pred == gold)
        else:
            return None
        if d["doc_id"] in out:
            sys.exit(f"{path}: duplicate doc_id {d['doc_id']}")
        out[d["doc_id"]] = r
    return out


def id_template(names):
    """(prefix, min_index, width) of Harbor task names like pixiu-fpb-fpb3876."""
    parts = [re.fullmatch(r"(.*?)(\d+)", t).groups() for t in names]
    prefixes = {p for p, _ in parts}
    if len(prefixes) != 1:
        sys.exit(f"mixed task-name prefixes {prefixes}")
    nums = [n for _, n in parts]
    return prefixes.pop(), min(map(int, nums)), min(map(len, nums))


def write_csv(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["run", "task_id", "reward"])
        for run, tid, r in sorted(rows):
            w.writerow([run, tid, int(r) if r.is_integer() else r])
    print(f"{os.path.basename(path)}: {len(rows)} rows, "
          f"{len({t for _, t, _ in rows})} task ids")


def main(dl, out):
    os.makedirs(out, exist_ok=True)
    harbor_rows, orig_rows = [], []
    for sub in SUBSETS:
        h_trials, o_rewards = {}, {}
        for k in RUNS:
            p = os.path.join(dl, "harbor_parity", "running_records", f"trial{k}",
                             f"pixiu-{sub}-parity", "result.json")
            if not os.path.exists(p):
                p = os.path.join(dl, "results_collection", f"result_harbor_{sub}_trial{k}.json")
                print(f"  WARNING {sub} trial{k}: using results_collection copy")
            h_trials[k] = harbor_trials(p)
            o_rewards[k] = original_rewards(
                os.path.join(dl, "results_collection", f"result_original_{sub}_trial{k}.json"), sub)
        names = {t for tr in h_trials.values() for t, _ in tr}
        if any(len({t for t, _ in tr}) != len(tr) for tr in h_trials.values()):
            print(f"  WARNING {sub}: Harbor task names not unique within a run; Harbor side dropped")
        else:
            if len({frozenset(t for t, _ in tr) for tr in h_trials.values()}) != 1:
                print(f"  WARNING {sub}: Harbor task sets differ across runs")
            for k, tr in h_trials.items():
                harbor_rows += [(k, t, r) for t, r in tr]
        if None not in o_rewards.values():
            prefix, lo, width = id_template(names)  # name docs like the Harbor tasks
            for k, rewards in o_rewards.items():
                orig_rows += [(k, f"{prefix}{str(lo + i).zfill(width)}", r)
                              for i, r in rewards.items()]
        hm = {k: round(sum(r for _, r in tr) / len(tr), 4) for k, tr in h_trials.items()}
        om = {k: round(sum(v.values()) / len(v), 4) for k, v in o_rewards.items() if v}
        print(f"{sub:32s} harbor {hm}  original {om}")
    for side, rows in (("original", orig_rows), ("harbor", harbor_rows)):
        bad = [(k, t, r) for k, t, r in rows if not 0 <= r <= 1]
        if bad:
            sys.exit(f"{side}: rewards outside [0,1]: {bad[:5]}")
        if rows:
            write_csv(os.path.join(out, f"{side}.csv"), rows)
    o = {t for _, t, _ in orig_rows}
    h = {t for _, t, _ in harbor_rows}
    print(f"task ids: original {len(o)}, harbor {len(h)}, common {len(o & h)}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
