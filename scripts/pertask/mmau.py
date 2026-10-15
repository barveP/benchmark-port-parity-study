"""Per-task outcomes for the MMAU parity experiment (HF adapters/mmau).

Usage: python -I mmau.py <download_dir> <out_dir>
<download_dir> mirrors adapters/mmau/ (results_collection/ required, original_parity/
optional). Stdlib only. Experiment: agent terminus-2, model gpt-4o-2024-08-06,
1000 MMAU test-mini tasks x 3 trials per side.

Original side: results_collection/original-trial<k>.json is a JSON list of the 1000
MMAU test-mini records {"id", "question", "choices", "answer", "model_output", ...}.
There is no correctness field, so the reward is recomputed with MMAU's own rule
(string_match in the benchmark's evaluation.py, re-implemented below): lower-case,
tokenise with \\b\\w+\\b into word sets; the prediction is correct iff it contains every
token of the answer and no token that occurs only in an incorrect choice. This gives
581/553/564 correct, i.e. exactly the published 58.1/55.3/56.4 (plain exact match
would give 578/549/560). When original_parity/original-parity-trial<k>.json is
present it is scored the same way and any disagreement is printed (not fatal).

Harbor side: results_collection/harbor-trial<k>.json is a Harbor job-level result.json:
stats.evals["terminus-2__gpt-4o__mmau"].reward_stats.reward = {"0.0": [...], "1.0": [...]}.
Trial names are "<first 32 chars of the MMAU uuid>__<7-char suffix>", e.g.
"a1517078-ff3b-4090-983e-0b0ce4cc__vDRNugJ". The suffix is stripped and the 32-char
prefix is mapped back to the full 36-char uuid through the original-side id list (the
mapping is unique). A trial listed only under exception_stats (run 2: one
RewardFileNotFoundError) has no reward and is written as 0.0, which is how Harbor's
metrics[0].mean counts it (sum of rewards / n_total_trials = 1000).

results_collection/gpt-4o-trial<k>.json (original-side layout) is a separate
"gpt-4o without agent" experiment absent from the snapshot JSON; it is ignored.

task_id = the MMAU uuid exactly as in the original files. Writes <out_dir>/original.csv
and <out_dir>/harbor.csv with columns run,task_id,reward (run = trial number k).
"""
import csv
import json
import os
import re
import sys

RUNS = (1, 2, 3)
WORD = re.compile(r"\b\w+\b")


def tokens(text):
    return set(WORD.findall(text.lower()))


def string_match(answer, prediction, choices):
    """MMAU evaluation.py scoring rule."""
    pred, ans = tokens(prediction), tokens(answer)
    if not pred:
        return False
    wrong = set()
    for choice in choices:
        ct = tokens(choice)
        if ct != ans:
            wrong |= ct - ans
    return ans <= pred and pred.isdisjoint(wrong)


def score_original(path):
    """{uuid: 1.0/0.0} from an MMAU model-output file."""
    with open(path) as f:
        records = json.load(f)
    out = {}
    for r in records:
        if r["id"] in out:
            sys.exit(f"{path}: duplicate id {r['id']}")
        out[r["id"]] = 1.0 if string_match(r["answer"], r["model_output"], r["choices"]) else 0.0
    return out


def read_harbor(path, prefix_to_uuid):
    """{uuid: reward} from a Harbor job-level result.json."""
    with open(path) as f:
        d = json.load(f)
    evals = d["stats"]["evals"]
    if len(evals) != 1:
        sys.exit(f"{path}: expected one eval, found {list(evals)}")
    (name, ev), = evals.items()

    def uuid_of(trial):
        prefix = trial.split("__", 1)[0]
        if prefix not in prefix_to_uuid:
            sys.exit(f"{path}: trial {trial} matches no MMAU id")
        return prefix_to_uuid[prefix]

    out = {}
    for reward, trials in ev["reward_stats"]["reward"].items():
        for t in trials:
            tid = uuid_of(t)
            if tid in out:
                sys.exit(f"{path}: duplicate task {tid}")
            out[tid] = float(reward)
    for exc, trials in ev.get("exception_stats", {}).items():
        for t in trials:
            tid = uuid_of(t)
            if tid not in out:
                print(f"  note: {os.path.basename(path)}: {t} ({exc}) has no reward; written as 0.0")
                out[tid] = 0.0
    n_total = d["n_total_trials"]
    if len(out) != n_total:
        print(f"  WARNING {os.path.basename(path)}: {len(out)} tasks vs n_total_trials={n_total}")
    print(f"  {os.path.basename(path)} [{name}]: sum/n_total = {sum(out.values()) / n_total:.4f}, "
          f"file metrics mean = {ev['metrics'][0]['mean']}")
    return out


def write_csv(path, runs):
    rows = sorted((k, t, r) for k, d in runs.items() for t, r in d.items())
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["run", "task_id", "reward"])
        for k, t, r in rows:
            w.writerow([k, t, int(r) if r.is_integer() else r])
    print(f"{os.path.basename(path)}: {len(rows)} rows, run means % = " + ", ".join(
        f"run{k}: {100 * sum(d.values()) / len(d):.2f} (n={len(d)})" for k, d in sorted(runs.items())))


def main(dl, out):
    os.makedirs(out, exist_ok=True)
    rc = os.path.join(dl, "results_collection")
    original = {}
    for k in RUNS:
        p = os.path.join(rc, f"original-trial{k}.json")
        if not os.path.exists(p):
            print(f"  WARNING missing {p}")
            continue
        original[k] = score_original(p)
        alt = os.path.join(dl, "original_parity", f"original-parity-trial{k}.json")
        if os.path.exists(alt):
            other = score_original(alt)
            diff = sorted(t for t in set(other) | set(original[k]) if other.get(t) != original[k].get(t))
            print(f"  original trial{k}: original_parity copy scores {sum(other.values()):.0f}/{len(other)}; "
                  f"{'agrees with results_collection' if not diff else f'differs on {len(diff)} tasks, e.g. {diff[:3]}'}")
    if not original:
        sys.exit("no original-side files; cannot build the Harbor id map either")
    prefixes = {}
    for t in set().union(*original.values()):
        prefixes.setdefault(t[:32], set()).add(t)
    clash = {p: v for p, v in prefixes.items() if len(v) > 1}
    if clash:
        sys.exit(f"ambiguous 32-char uuid prefixes: {clash}")
    prefix_to_uuid = {p: next(iter(v)) for p, v in prefixes.items()}
    harbor = {}
    for k in RUNS:
        p = os.path.join(rc, f"harbor-trial{k}.json")
        if not os.path.exists(p):
            print(f"  WARNING missing {p}")
            continue
        harbor[k] = read_harbor(p, prefix_to_uuid)
    for side, runs in (("original", original), ("harbor", harbor)):
        if not runs:
            print(f"{side}: no per-task data; nothing written")
            continue
        if len({frozenset(d) for d in runs.values()}) != 1:
            print(f"  WARNING {side}: task sets differ across runs")
        write_csv(os.path.join(out, f"{side}.csv"), runs)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
