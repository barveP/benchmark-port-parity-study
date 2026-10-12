#!/usr/bin/env python3
"""Phase 2: build the comparison table under the pre-registered rule (memos/phase-2-preregistration.md).

One row per experiment and main metric, original side vs Harbor side. Writes:
  comparisons.csv      every experiment with a main metric (all k), with flags and the selection branch
  comparisons_legs.csv secondary set: transitive legs through the Terminal-Bench adapter
  selection_log.json   excluded names, unmatched experiments, data-quality lists
Usage: python -I scripts/p2_build_comparisons.py <snapshot_dir> <paper_tables_csv> <out_dir>
"""
import csv
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parity_lib import iter_experiments, lenient_runs, mean, parse_pm, zero_spread  # noqa: E402

SIDE_WORDS = {"stderr", "std", "sem", "missing", "cost", "token", "tokens", "time", "latency", "count", "counts", "ids"}
HEADLINE = {"resolve", "resolved", "pass", "passed", "success", "solve", "solving", "accuracy", "acc", "score", "reward", "f1"}


def is_headline(name):
    """Amendment 2 (2026-10-11): whole-token match, same tokenization as the side-quantity rule."""
    return any(t in HEADLINE for t in re.split(r"[^a-z0-9]+", str(name).lower()))
ADAPTER_ALIASES = {  # paper table names -> snapshot adapter file names, where they differ
    "swe-bench-multilingual": "swebench_multilingual", "swe-bench pro": "swebenchpro", "swe-bench verified": "swebench",
    "swe-smith": "swesmith", "swt bench": "swtbench", "swe-lancer": "swelancer", "webgen-bench": "webgen_bench",
    "aider polyglot": "aider_polyglot", "bigcodebench": "bigcodebench_hard", "frontiercs": "frontier-cs-algorithm",
    "livecodebench": "livecodebench", "humanevalfix": "humanevalfix", "crust-bench": "crustbench", "arc-agi-2": "arc_agi_2",
    "reasoning gym": "reasoning-gym", "gpqa diamond": "gpqa-diamond", "humanity’s last exam": "hle", "humanity's last exam": "hle",
    "aa-lcr": "aa-lcr", "scienceagent bench": "scienceagentbench", "scienceagentbench": "scienceagentbench",
    "researchcode bench": "research-code-bench", "researchcodebench": "research-code-bench", "bix-bench": "bixbench",
    "lab-bench": "labbench", "ace-bench": "ace-bench", "deepsynth": "deepsynth", "seal-0": "seal0", "da-code": "dacode",
    "spider 2": "spider2-dbt", "pixiu": "pixiu", "crmarena": "crmarena", "medagentbench": "medagentbench",
    "cybergym": "cybergym", "strongreject": "strongreject", "mmau": "mmau", "ml-dev-bench": "ml_dev_bench",
    "llm-srbench": "llmsr_bench", "omni-math": "omni-math", "ineqmath": "ineqmath", "kumo": "kumo", "mmmlu": "mmmlu",
    "simpleqa": "simpleqa", "replicationbench": "replicationbench", "sldbench": "sldbench", "mlgym-bench": "mlgym-bench",
    "codepde": "codepde", "scicode": "scicode", "qcircuitbench": "qcircuitbench", "gaia": "gaia", "gaia2": "gaia2",
    "bfcl": "bfcl", "widesearch": "widesearch", "financeagent": "financeagent", "spreadsheetbench": "spreadsheetbench",
    "lawbench": "lawbench", "usaco": "usaco", "quixbugs": "quixbugs", "gso": "gso", "algotune": "algotune",
    "devopsgym": "devopsgym", "aime": "aime", "cooperbench": "cooperbench", "featbench": "featbench",
    "featurebench": "featurebench", "theagentcompany": "theagentcompany", "graphdesignbench": "gdb",
}

snap, tables_csv, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
adapters_present = {a for a, _, _ in iter_experiments(snap)}


def norm(name):
    return re.sub(r"\s+", " ", name.strip().lower())


table = {}
for r in csv.DictReader(open(tables_csv)):
    key = norm(r["benchmark"])
    a = ADAPTER_ALIASES.get(key, key.replace(" ", "_").replace("-", "_"))
    cand = [a, a.replace("_", "-"), a.replace("-", "_")]
    hit = next((c for c in cand if c in adapters_present), None)
    if hit and r["orig_mean"] not in ("", "None") and r["harbor_mean"] not in ("", "None"):
        table.setdefault(hit, []).append({"orig": float(r["orig_mean"]), "harbor": float(r["harbor_mean"]),
                                          "orig_txt": r["orig"], "harbor_txt": r["harbor"], "k": r["k"], "set": r["parity_set"]})


def tol(txt):
    m = re.search(r"\d+(?:\.(\d+))?", txt or "")
    return 0.5 * 10 ** (-(len(m.group(1)) if m and m.group(1) else 0)) + 1e-9


def side_list(m, side):
    for suf in ("_runs", "_trials"):
        v = lenient_runs(m.get(side + suf))
        if v:
            return v, side + suf
    return None, None


def is_side_quantity(name):
    """Amendment 1 (2026-10-11): whole-token match, so 'counted' and 'Semantic' are not excluded."""
    tokens = re.split(r"[^a-z0-9]+", str(name).lower())
    return any(t in SIDE_WORDS for t in tokens)


rows, legs, log = [], [], {"excluded_side_quantities": {}, "experiments_without_comparison": [], "original_variant_rows": [],
                           "single_run_rows": [], "table_unmatched_adapters": sorted(set(table) - set()),}
for adapter, i, e in iter_experiments(snap):
    cands = []
    for j, m in enumerate(e.get("metrics") or []):
        name = m.get("metric")
        if any(k in m for k in ("original_llm_runs", "original_json_runs")):
            log["original_variant_rows"].append(f"{adapter}#{i}: {name}")
        a, ka = side_list(m, "original")
        b, kb = side_list(m, "harbor")
        t, kt = side_list(m, "tb_adapter")
        if t and (a or b):  # transitive legs
            if a:
                legs.append({"adapter": adapter, "exp": i, "metric_index": j, "metric": name, "leg": "original_vs_tb_adapter",
                             "side_a_runs": a, "side_b_runs": t, "agent": e.get("agent"), "model": e.get("model")})
            if b:
                legs.append({"adapter": adapter, "exp": i, "metric_index": j, "metric": name, "leg": "tb_adapter_vs_harbor",
                             "side_a_runs": t, "side_b_runs": b, "agent": e.get("agent"), "model": e.get("model")})
        if not (a and b):
            continue
        if is_side_quantity(name):
            log["excluded_side_quantities"][str(name)] = log["excluded_side_quantities"].get(str(name), 0) + 1
            continue
        cands.append((j, m, a, b, ka, kb))
    if not cands:
        log["experiments_without_comparison"].append(f"{adapter}#{i} ({e.get('agent')}, {e.get('model')})")
        continue
    chosen, branch = None, None
    for ent in table.get(adapter, []):  # branch 1: match the paper's table entry
        for c in cands:
            pm_o, pm_h = parse_pm(c[1].get("original")), parse_pm(c[1].get("harbor"))
            if not (pm_o and pm_h):
                continue
            for sc in (1.0, 100.0):
                if abs(pm_o[0] * sc - ent["orig"]) <= tol(ent["orig_txt"]) and abs(pm_h[0] * sc - ent["harbor"]) <= tol(ent["harbor_txt"]):
                    chosen, branch = c, "1:paper_table"
                    break
            if chosen:
                break
        if chosen:
            break
    if not chosen and len(cands) >= 5 and len({str(c[1].get("metric")) for c in cands}) == 1 \
            and len({str(c[1].get("benchmark_name")) for c in cands}) == len(cands) \
            and len({(len(c[2]), len(c[3])) for c in cands}) == 1:
        # Amendment 2b: per-task rows (one row per problem, same metric, equal k): aggregate by run index
        k = len(cands[0][2])
        agg_a = [sum(c[2][r] for c in cands) / len(cands) for r in range(k)]
        agg_b = [sum(c[3][r] for c in cands) / len(cands) for r in range(k)]
        m0 = dict(cands[0][1]); m0["metric"] = f"{m0.get('metric')} (mean over {len(cands)} per-task rows)"
        m0["original"] = m0["harbor"] = None
        chosen, branch = (cands[0][0], m0, agg_a, agg_b, cands[0][4], cands[0][5]), "2b:aggregated_per_task_rows"
    if not chosen:  # branch 2: headline name
        for c in cands:
            if is_headline(c[1].get("metric", "")):
                chosen, branch = c, "2:headline_name"
                break
    if not chosen:  # branch 3: first remaining
        chosen, branch = cands[0], "3:first_remaining"
    j, m, a, b, ka, kb = chosen
    vals = a + b
    pct_in_text = "%" in str(m.get("original", "")) + str(m.get("harbor", ""))
    fraction = max(vals) <= 1.0 and min(vals) >= 0 and not pct_in_text
    scale = 100.0 if fraction else 1.0
    a_pts, b_pts = [x * scale for x in a], [x * scale for x in b]
    native = min(a_pts + b_pts) < 0 or max(a_pts + b_pts) > 100
    adapted, parity_n = e.get("adapted_benchmark_size"), e.get("parity_benchmark_size")
    subset = ("subset" if parity_n < adapted else "full") if isinstance(adapted, (int, float)) and isinstance(parity_n, (int, float)) else "unknown"
    row = {"adapter": adapter, "exp": i, "metric_index": j, "agent": e.get("agent"), "model": e.get("model"), "metric": m.get("metric"),
           "selection_branch": branch, "key_original": ka, "key_harbor": kb, "k_original": len(a), "k_harbor": len(b),
           "scaled_x100": scale == 100.0, "native_units": native, "parity_set": subset, "parity_n": parity_n, "adapted_n": adapted,
           "original_runs": a_pts, "harbor_runs": b_pts, "mean_original": mean(a_pts), "mean_harbor": mean(b_pts),
           "gap": mean(b_pts) - mean(a_pts), "identical_lists": a == b,
           "zero_spread_both": len(a) >= 2 and len(b) >= 2 and zero_spread(a) and zero_spread(b),
           "zero_spread_one": (len(a) >= 2 and zero_spread(a)) != (len(b) >= 2 and zero_spread(b)),
           "single_run_side": min(len(a), len(b)) < 2, "reported_original": m.get("original"), "reported_harbor": m.get("harbor"),
           "in_paper_table": adapter in table}
    if row["single_run_side"]:
        log["single_run_rows"].append(f"{adapter}#{i}: {m.get('metric')} k={len(a)}v{len(b)}")
    rows.append(row)

log["table_unmatched_adapters"] = sorted(a for a in table if not any(r["adapter"] == a and r["selection_branch"] == "1:paper_table" for r in rows))
log["n_experiments"] = sum(1 for _ in iter_experiments(snap))
log["n_comparisons"] = len(rows)
log["n_legs"] = len(legs)
log["selection_branch_counts"] = {b: sum(1 for r in rows if r["selection_branch"] == b) for b in ("1:paper_table", "2b:aggregated_per_task_rows", "2:headline_name", "3:first_remaining")}
log["k_counts"] = {}
for r in rows:
    kk = f"{r['k_original']}v{r['k_harbor']}"
    log["k_counts"][kk] = log["k_counts"].get(kk, 0) + 1
log["flags"] = {f: sum(1 for r in rows if r[f]) for f in ("native_units", "identical_lists", "zero_spread_both", "zero_spread_one", "single_run_side", "scaled_x100")}
log["parity_set_counts"] = {s: sum(1 for r in rows if r["parity_set"] == s) for s in ("full", "subset", "unknown")}

cols = list(rows[0].keys())
with open(os.path.join(out, "comparisons.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)
with open(os.path.join(out, "comparisons_legs.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(legs[0].keys()) if legs else ["none"])
    w.writeheader()
    w.writerows(legs)
with open(os.path.join(out, "selection_log.json"), "w") as fh:
    json.dump(log, fh, indent=1)

print(f"experiments {log['n_experiments']} | comparisons {len(rows)} | transitive legs {len(legs)} | no comparison {len(log['experiments_without_comparison'])}")
print("selection branch:", log["selection_branch_counts"], "| paper-table adapters not matched by a row:", log["table_unmatched_adapters"])
print("k per side:", dict(sorted(log["k_counts"].items(), key=lambda kv: -kv[1])))
print("flags:", log["flags"], "| parity set:", log["parity_set_counts"])
print("excluded side-quantity names:", log["excluded_side_quantities"])
print("experiments without comparison:", log["experiments_without_comparison"])
