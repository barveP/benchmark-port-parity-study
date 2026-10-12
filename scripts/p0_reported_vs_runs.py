#!/usr/bin/env python3
"""Phase 0 (preliminary, feeds RQ2): does each reported "mean ± err" string match its raw runs?

For every metric row with a parseable reported string on a side and a run list of length >= 2
(lenient parsing: "58.3%" counts as 58.3), compare:
  * reported mean vs mean(runs)             -> "mean_ok" if |diff| <= half a unit of the last reported decimal
  * reported err  vs SEM(runs) and SD(runs) -> "sem", "sd", "both" (SEM == SD only if k = 1, so
    effectively never), "neither", or "none" (no ± part reported)
Unit alignment: if runs are all <= 1 and the reported mean > 1, runs are fractions; scale by 100.
Usage: python -I scripts/p0_reported_vs_runs.py <snapshot_dir> <out_dir>
"""
import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parity_lib import iter_metric_rows, lenient_runs, mean, parse_pm, sample_sd, sem  # noqa: E402


def rounding_tol(text, value_in_text):
    """Half a unit in the last reported decimal place, plus a little slack for float noise."""
    m = re.search(r"-?\d+(?:\.(\d+))?", text)
    dec = len(m.group(1)) if (m and m.group(1)) else 0
    return 0.5 * 10 ** (-dec) + 1e-9 + 0.01 * 10 ** (-dec)

root, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
rows, counts = [], collections.Counter()
for adapter, i, e, j, m in iter_metric_rows(root):
    for side in ("original", "harbor"):
        pm = parse_pm(m.get(side))
        runs = lenient_runs(m.get(side + "_runs")) or lenient_runs(m.get(side + "_trials"))
        if pm is None or runs is None or len(runs) < 2:
            continue
        rep_mean, rep_err = pm
        if max(runs) <= 1.0 and rep_mean > 1.0:
            runs = [x * 100 for x in runs]
        mu, s, se = mean(runs), sample_sd(runs), sem(runs)
        txt = str(m.get(side))
        parts = re.split(r"\+/-|±|\+-", txt)
        tol_mean = rounding_tol(parts[0], rep_mean)
        mean_ok = abs(mu - rep_mean) <= tol_mean
        if rep_err is None:
            err_cls = "none"
        else:
            tol_err = rounding_tol(parts[1] if len(parts) > 1 else parts[0], rep_err)
            ok_sem, ok_sd = abs(se - rep_err) <= tol_err, abs(s - rep_err) <= tol_err
            err_cls = "sem" if ok_sem and not ok_sd else "sd" if ok_sd and not ok_sem else "both" if ok_sem else "neither"
        counts[(mean_ok, err_cls)] += 1
        rows.append({"adapter": adapter, "exp": i, "metric": m.get("metric"), "side": side, "k": len(runs),
                     "reported": m.get(side), "mean_runs": round(mu, 3), "sem_runs": round(se, 3), "sd_runs": round(s, 3),
                     "mean_ok": mean_ok, "err_class": err_cls})
res = {"tolerance": "half a unit in the last reported decimal place", "n_checked": len(rows),
       "by_mean_ok_and_err_class": {f"mean_ok={a},err={b}": c for (a, b), c in sorted(counts.items(), key=lambda kv: -kv[1])},
       "mean_mismatch_rows": [r for r in rows if not r["mean_ok"]],
       "err_neither_rows": [r for r in rows if r["err_class"] == "neither"],
       "err_sd_rows": [r for r in rows if r["err_class"] == "sd"]}
with open(os.path.join(out, "reported_vs_runs.json"), "w") as fh:
    json.dump(res, fh, indent=1)
print(f"sides checked (k>=2, parseable): {len(rows)}")
for k, v in res["by_mean_ok_and_err_class"].items():
    print(f"  {k}: {v}")
print(f"reported mean differs from mean(runs) beyond rounding: {len(res['mean_mismatch_rows'])}")
for r in res["mean_mismatch_rows"]:
    print(f"   {r['adapter']}#{r['exp']} {r['metric']!r} {r['side']}: reported {r['reported']!r} vs mean(runs) {r['mean_runs']} (k={r['k']})")
print(f"± matches SD rather than SEM: {len(res['err_sd_rows'])} | matches neither: {len(res['err_neither_rows'])}")
for r in res["err_neither_rows"][:30]:
    print(f"   {r['adapter']}#{r['exp']} {r['metric']!r} {r['side']}: reported {r['reported']!r}; SEM {r['sem_runs']} SD {r['sd_runs']} (k={r['k']})")
