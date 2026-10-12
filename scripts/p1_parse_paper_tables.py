#!/usr/bin/env python3
"""Phase 1: parse Tables 3 and 4 of arXiv 2609.04298v3 (adapter catalog with parity scores) from
the arXiv HTML rendering, write them as CSV, and cross-check each row against the JSON snapshot.

Get the HTML with:  curl -sSL -o paper_v3.html https://arxiv.org/html/2609.04298v3
Usage: python -I scripts/p1_parse_paper_tables.py <paper_v3.html> <snapshot_dir> <out_csv> <out_json>
Cross-check rule: a table row "matches" a JSON metric row when the reported original mean and the
reported harbor mean both agree within rounding (half a unit of the table's last decimal), trying
the JSON values as-is and scaled by 100.
"""
import csv
import html as htmlmod
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parity_lib import iter_metric_rows, parse_pm  # noqa: E402

src, snap, out_csv, out_json = sys.argv[1:5]
raw = open(src, encoding="utf-8", errors="ignore").read()


def clean(cell):
    cell = re.sub(r"<annotation[^>]*>.*?</annotation>", "", cell, flags=re.S)  # drop LaTeX alt text
    cell = re.sub(r"<[^>]+>", " ", cell)
    cell = htmlmod.unescape(cell).replace("\\pm", "")
    return re.sub(r"\s+", " ", cell).strip()


tables = []
for tb in re.findall(r"<table.*?</table>", raw, flags=re.S):
    if "Parity Agent" not in tb or "Harbor" not in tb:
        continue
    rows = []
    for tr in re.findall(r"<tr.*?</tr>", tb, flags=re.S):
        cells = [clean(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, flags=re.S)]
        if len(cells) >= 10 and cells[0] not in ("Benchmark", ""):
            rows.append(cells[:10])
    if rows:
        tables.append(rows)
if len(tables) != 2:
    sys.exit(f"expected 2 tables, found {len(tables)}")

cols = ["table", "benchmark", "subdomain", "scenario", "mode", "parity_agent", "parity_model", "k", "parity_set",
        "orig", "harbor", "orig_mean", "orig_sem", "harbor_mean", "harbor_sem", "parity_n", "full_n"]
out = []
for ti, rows in enumerate(tables, start=3):
    for r in rows:
        rec = dict(zip(cols[1:11], r))
        rec["table"] = ti
        for side in ("orig", "harbor"):
            pm = parse_pm(rec[side].replace("±", "+/-"))
            rec[side + "_mean"], rec[side + "_sem"] = (pm if pm else (None, None))
        m = re.match(r"(\d[\d,]*)/(\d[\d,]*)", rec["parity_set"])
        rec["parity_n"], rec["full_n"] = (int(m.group(1).replace(",", "")), int(m.group(2).replace(",", ""))) if m else (None, None)
        out.append(rec)

# cross-check against the JSON snapshot
json_rows = []
for adapter, i, e, j, m in iter_metric_rows(snap):
    po, ph = parse_pm(m.get("original")), parse_pm(m.get("harbor"))
    if po and ph:
        json_rows.append((adapter, i, j, e.get("agent"), e.get("model"), e.get("number_of_runs", e.get("number_of_trials")),
                          m.get("metric"), po[0], ph[0], po[1], ph[1]))


def tol(text):
    m = re.search(r"\d+(?:\.(\d+))?", text or "")
    dec = len(m.group(1)) if (m and m.group(1)) else 0
    return 0.5 * 10 ** (-dec) + 1e-9


n_matched = 0
for rec in out:
    rec["json_matches"] = []
    if rec["orig_mean"] is None or rec["harbor_mean"] is None:
        continue
    to, th = tol(rec["orig"]), tol(rec["harbor"])
    for (adapter, i, j, agent, model, k, metric, om, hm, os_, hs) in json_rows:
        for scale in (1.0, 100.0):
            if abs(om * scale - rec["orig_mean"]) <= to and abs(hm * scale - rec["harbor_mean"]) <= th:
                rec["json_matches"].append({"adapter": adapter, "exp": i, "metric_index": j, "agent": agent, "model": model,
                                            "number_of_runs": k, "metric": metric, "scale": scale,
                                            "json_sem": [os_, hs]})
                break
    n_matched += bool(rec["json_matches"])

with open(out_csv, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=cols + ["n_json_matches"])
    w.writeheader()
    for rec in out:
        w.writerow({**{c: rec.get(c) for c in cols}, "n_json_matches": len(rec["json_matches"])})
with open(out_json, "w") as fh:
    json.dump(out, fh, indent=1)

print(f"table rows: {len(out)} (Table 3: {len(tables[0])}, Table 4: {len(tables[1])}); matched to a JSON row by both reported means: {n_matched}")
print("k column counts:", {k: sum(1 for r in out if r['k'] == k) for k in sorted({r['k'] for r in out})})
print("rows with N/A scores:", [r['benchmark'] for r in out if r['orig_mean'] is None])
print("rows with identical reported strings on both sides:", [r['benchmark'] for r in out if r['orig'] == r['harbor'] and r['orig_mean'] is not None])
print("rows with a 0.0 SEM on at least one side (k>1):", [(r['benchmark'], r['k'], r['orig'], r['harbor']) for r in out if r['k'] not in ('1', '–', '-') and (r['orig_sem'] == 0 or r['harbor_sem'] == 0)])
print("UNMATCHED rows (no JSON row reports both means):")
for r in out:
    if not r["json_matches"] and r["orig_mean"] is not None:
        print(f"   {r['benchmark']} | k={r['k']} | {r['parity_set']} | {r['orig']} vs {r['harbor']} | {r['parity_agent']}/{r['parity_model']}")
print("rows matched to >1 JSON row:", [(r['benchmark'], len(r['json_matches'])) for r in out if len(r['json_matches']) > 1])
