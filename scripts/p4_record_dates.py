#!/usr/bin/env python3
"""Phase 4: date each headline comparison against the day the range-overlap criterion entered the guide.
The criterion was added by Harbor pull request 1403, merged 2026-04-19 (https://github.com/harbor-framework/harbor/pull/1403). Reads the
experiment dates from the pinned parity files and the headline set from results/phase2/rq2_comparisons.csv.
Usage: python -I scripts/p4_record_dates.py <snapshot dir> <phase2 dir>
"""
import csv
import datetime
import json
import os
import sys

snap, p2 = sys.argv[1], sys.argv[2]
RULE_DATE = "2026-04-19"
rows = [r for r in csv.DictReader(open(os.path.join(p2, "rq2_comparisons.csv"))) if r["k_original"] == "3" and r["k_harbor"] == "3"]
dates = {}
for r in rows:
    exps = json.load(open(os.path.join(snap, f"{r['adapter']}.json")))
    e = exps[int(r["exp"])]
    assert e.get("adapter_name", r["adapter"]) in (r["adapter"], e.get("adapter_name")), (r["adapter"], e.get("adapter_name"))
    dates[f"{r['adapter']}#{r['exp']}"] = e.get("date")


def norm(d):
    """Normalise a date string such as 2026-3-23 to 2026-03-23; None if it cannot be parsed."""
    if not d:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%b %d, %Y", "%B %d, %Y"):
        try:
            return datetime.datetime.strptime(str(d).strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


dates = {k: norm(v) for k, v in dates.items()}
known = {k: v for k, v in dates.items() if v}
before = sorted(k for k, v in known.items() if v < RULE_DATE)
out = {"rule_date": RULE_DATE, "n_headline": len(rows), "n_with_date": len(known), "n_dated_before_rule": len(before),
       "n_dated_on_or_after_rule": len(known) - len(before), "earliest": min(known.values()), "latest": max(known.values()),
       "named": {k: dates.get(k) for k in dates if k.split("#")[0] in ("usaco", "rexbench", "pixiu", "gdb", "frontier-cs-algorithm")},
       "dates": dates}
json.dump(out, open(os.path.join(p2, "record_dates.json"), "w"), indent=1)
print({k: v for k, v in out.items() if k != "dates"})
