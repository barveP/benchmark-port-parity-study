#!/usr/bin/env python3
"""Phase 1: export the literature-sweep records (candidates and source-verified verdicts) from the
search log into the repo, so the memo's table can be traced. Raw search notes stay out of the repo.
Usage: python -I scripts/p1_export_verdicts.py <journal.jsonl> <out_dir>
"""
import csv
import json
import os
import re
import sys

SCRATCH = re.compile(r"\S*(?:claude-501|scratchpad)\S*")
# Normalise the wording of the search notes before export.
WORDING = [(r"\bWebFetch\b", "page fetch"), (r"\bWebSearch\b", "web search"), (r"\bToolSearch\b", "tool lookup"), (r"\bsubagents?\b", "searches"), (r"\borchestrator\b", "coordinator"), (r"\bthe parent\b", "the lead")]


def scrub(x):
    """Drop local scratch paths and normalise the wording of free-text notes."""
    if isinstance(x, str):
        x = SCRATCH.sub("[local scratch file]", x)
        for a, b in WORDING:
            x = re.sub(a, b, x)
        return x
    if isinstance(x, dict):
        return {k: scrub(v) for k, v in x.items()}
    if isinstance(x, list):
        return [scrub(v) for v in x]
    return x

src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
finders, verdicts, critic = [], [], None
for line in open(src):
    try:
        d = json.loads(line)
    except Exception:
        continue
    if d.get("type") != "result" or not isinstance(d.get("result"), dict):
        continue
    r = scrub(d["result"])
    if "candidates" in r:
        finders.append({"label": d.get("label"), "queries_run": r.get("queries_run"), "notes": r.get("notes"), "candidates": r["candidates"]})
    elif "verdict" in r:
        verdicts.append(r)
    elif "gaps" in r:
        critic = r
summary = {"n_search_agents": len(finders), "n_queries": sum(len(f.get("queries_run") or []) for f in finders),
           "n_candidate_records": sum(len(f["candidates"]) for f in finders), "n_verified_at_source": len(verdicts),
           "critic_followup_searches": [g["query"] for g in (critic or {}).get("gaps", [])]}
json.dump(summary, open(os.path.join(out, "phase1_summary.json"), "w"), indent=1)
cols = ["verdict", "confidence", "title", "url", "date", "authors", "venue", "read_depth", "analyzes_harbor_parity_data",
        "critiques_range_overlap_rule", "applies_equivalence_testing_to_benchmark_ports",
        "compares_reimplemented_benchmark_to_original_statistically", "what_it_does", "what_it_leaves_open", "citation"]
order = {"kills": 0, "narrows": 1, "neighbor": 2, "irrelevant": 3}
with open(os.path.join(out, "phase1_verdicts.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    for v in sorted(verdicts, key=lambda v: (order.get(v.get("verdict"), 9), v.get("title", ""))):
        w.writerow(v)
cands = [c for f in finders for c in f["candidates"]]
with open(os.path.join(out, "phase1_candidates.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["overlap_risk", "title", "url", "date", "type", "source", "read_depth", "summary", "why"], extrasaction="ignore")
    w.writeheader()
    for c in sorted(cands, key=lambda c: ({"high": 0, "medium": 1, "low": 2, "none": 3}.get(c.get("overlap_risk"), 9), c.get("title", ""))):
        w.writerow(c)
nq = sum(len(f.get("queries_run") or []) for f in finders)
print(f"finders {len(finders)} | queries {nq} | candidates {len(cands)} | verdicts {len(verdicts)} | critic gaps {len(critic['gaps']) if critic else 0}")
print("verdict counts:", {k: sum(1 for v in verdicts if v.get('verdict') == k) for k in order})
