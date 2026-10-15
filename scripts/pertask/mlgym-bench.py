"""Per-task outcomes for the MLGym-Bench Harbor parity experiment (stdlib only).

Usage:  python -I mlgym-bench.py <download_dir> <out_dir>

<download_dir> mirrors adapters/mlgym-bench/ of the Hugging Face dataset
harborframework/parity-experiments.  The files there belong to the SECOND
experiment in data/raw/harbor_parity/mlgym-bench.json: mini-swe-agent@1.10.0 +
openai/gpt-5-mini, "original x harbor adapter (continuous)", 3 runs x 11
environments, metric "Mean Reward".  Rewards are CONTINUOUS and UNBOUNDED
(agent metric minus the task baseline: accuracy deltas near 0.1-0.5, RMSE
deltas in the thousands, negative RL returns), so they are not in [0, 1].
(The first experiment, gpt-5 binary pass/fail on 12 tasks, has no files on
HF; its per-task outcomes are only the resolved/unresolved id lists inside
the snapshot JSON.)

Original side:  results_collection/result_original_trial<N>.json
    {"run": "seed100<N-1>", "n_tasks": 11, "mean_reward": ..,
     "tasks": {<MLGym camelCase name>: {"reward": float, "agent_score": {..},
                                        "baseline": {..}, "all_attempts": [..]}}}
    Task ids are MLGym names ("battleOfSexes", "titanicSurvival", ...).

Harbor side:  results_collection/result_harbor_trial<N>.json (job-level)
    stats.evals[<name>].reward_stats.reward = {"<reward>": [trial names]}
    Trial names are the Harbor task name TRUNCATED TO 32 CHARACTERS plus a
    "__<7 chars>" suffix, e.g. "mlgym-image-classification-cifar__XjousJH",
    which makes 4 of the 11 names per run ambiguous (cifar10 vs cifar10-l1,
    house-price vs house-price-l1).  Each trial is resolved to its full task
    name with harbor_parity/trial<N>/<trial name>/result.json ("task_name"),
    which is needed (and present in the mirror) only for the ambiguous trial
    dirs; unambiguous names are resolved by unique prefix match against the
    11 known task names.  The "__<suffix>" is stripped in either case.

task_id on BOTH sides is the Harbor task name ("mlgym-battle-of-sexes"), the
form used by the snapshot JSON's per_environment table; original MLGym names
are mapped with the explicit table ORIG_TO_HARBOR below (a bijection).
run = N from the file name.  Output: <out_dir>/original.csv and harbor.csv
with columns run,task_id,reward.
"""
import csv
import json
import os
import re
import sys

ORIG_TO_HARBOR = {
    "battleOfSexes": "mlgym-battle-of-sexes",
    "blotto": "mlgym-blotto",
    "imageClassificationCifar10": "mlgym-image-classification-cifar10",
    "imageClassificationCifar10L1": "mlgym-image-classification-cifar10-l1",
    "imageClassificationFMnist": "mlgym-image-classification-f-mnist",
    "prisonersDilemma": "mlgym-prisoners-dilemma",
    "regressionKaggleHousePrice": "mlgym-regression-kaggle-house-price",
    "regressionKaggleHousePriceL1": "mlgym-regression-kaggle-house-price-l1",
    "rlMetaMazeMisc": "mlgym-rl-meta-maze-misc",
    "rlMountainCarContinuous": "mlgym-rl-mountain-car-continuous",
    "titanicSurvival": "mlgym-titanic",
}
TASKS = set(ORIG_TO_HARBOR.values())
TRIAL_SUFFIX = re.compile(r"__[A-Za-z0-9]+$")


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def original_rows(path, run):
    data = load(path)
    rows = [(run, ORIG_TO_HARBOR[name], float(t["reward"]))
            for name, t in data["tasks"].items()]
    assert len(rows) == data["n_tasks"], (path, len(rows))
    mean = sum(r for _, _, r in rows) / len(rows)
    assert abs(mean - data["mean_reward"]) < 1e-6, (path, mean)
    return rows


def resolve_trial(download_dir, run, trial_name):
    """Full Harbor task name for a (possibly truncated) job-level trial name."""
    per_trial = os.path.join(download_dir, "harbor_parity", f"trial{run}",
                             trial_name, "result.json")
    if os.path.exists(per_trial):
        task = load(per_trial)["task_name"]
        assert load(per_trial)["trial_name"] == trial_name, per_trial
    else:
        prefix = TRIAL_SUFFIX.sub("", trial_name)
        matches = [t for t in TASKS if t.startswith(prefix)]
        assert len(matches) == 1, (trial_name, "ambiguous, needs", per_trial)
        task = matches[0]
    assert task in TASKS, (trial_name, task)
    return task


def harbor_rows(download_dir, path, run):
    data = load(path)
    (ev,) = data["stats"]["evals"].values()
    assert not ev["exception_stats"] and data["stats"]["n_errors"] == 0, path
    rows = [(run, resolve_trial(download_dir, run, name), float(reward))
            for reward, names in ev["reward_stats"]["reward"].items()
            for name in names]
    assert len(rows) == data["n_total_trials"], (path, len(rows))
    mean = sum(r for _, _, r in rows) / len(rows)
    assert abs(mean - ev["metrics"][0]["mean"]) < 1e-6, (path, mean)
    return rows


def write_csv(path, rows):
    keys = [(r, t) for r, t, _ in rows]
    assert len(keys) == len(set(keys)), "duplicate (run, task_id)"
    rows.sort()
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["run", "task_id", "reward"])
        w.writerows(rows)


def main(download_dir, out_dir):
    rc = os.path.join(download_dir, "results_collection")
    os.makedirs(out_dir, exist_ok=True)
    sides = {"original": [], "harbor": []}
    for fn in sorted(os.listdir(rc)):
        m = re.fullmatch(r"result_(original|harbor)_trial(\d+)\.json", fn)
        if not m:
            continue
        side, run = m.group(1), int(m.group(2))
        path = os.path.join(rc, fn)
        rows = (original_rows(path, run) if side == "original"
                else harbor_rows(download_dir, path, run))
        vals = [x for _, _, x in rows]
        print(f"{side} run {run}: n_tasks={len(vals)} "
              f"mean={sum(vals) / len(vals):.6f}")
        sides[side] += rows
    tasks = {s: {t for _, t, _ in rows} for s, rows in sides.items()}
    assert tasks["original"] == tasks["harbor"] == TASKS, "task sets differ"
    print(f"tasks in common: {len(TASKS)}")
    for side, rows in sides.items():
        write_csv(os.path.join(out_dir, f"{side}.csv"), rows)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
