"""Tests for the Phase 2 rules and the comparison builder. Run: .venv/bin/python -I -m pytest -q"""
import csv
import json
import math
import os
import subprocess
import sys

import numpy as np
import pytest
from scipy.stats import ttest_ind, ttest_rel

from parity_lib import (diff_ci_halfwidth, paired_task_verdicts, ranges_overlap, rule_verdicts, sem, tost_power)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_vectorised_rules_agree_with_scalar_definitions():
    rng = np.random.default_rng(1)
    a = rng.normal(50, 3, (400, 3)); b = rng.normal(51, 3, (400, 3))
    v = rule_verdicts(a, b, margins=(2, 5))
    for i in range(400):
        x, y = list(a[i]), list(b[i])
        gap = np.mean(y) - np.mean(x)
        assert v["R"][i] == (not ranges_overlap(x, y, eps=1e-9))
        assert v["S1"][i] == (abs(gap) > sem(x) + sem(y) + 1e-12)
        assert v["S2"][i] == (abs(gap) > math.sqrt(sem(x) ** 2 + sem(y) ** 2) + 1e-12)
        assert v["W"][i] == (ttest_ind(x, y, equal_var=False).pvalue < 0.05)
        assert v["E2"][i] == (abs(gap) + diff_ci_halfwidth(x, y, 0.90) <= 2)
        assert v["E5"][i] == (abs(gap) + diff_ci_halfwidth(x, y, 0.90) <= 5)


def test_rules_handle_zero_variance():
    a = np.array([[50.0, 50.0, 50.0]]); b = np.array([[52.0, 52.0, 52.0]]); c = np.array([[50.0, 50.0, 50.0]])
    v = rule_verdicts(a, b, margins=(3,))
    assert v["R"][0] and v["S1"][0] and v["S2"][0] and v["W"][0] and v["E3"][0]  # exact 2-point gap, no noise
    v = rule_verdicts(a, c, margins=(3,))
    assert not v["R"][0] and not v["S1"][0] and not v["W"][0] and v["E3"][0]


def test_false_alarm_rates_at_k3_normal():
    rng = np.random.default_rng(2)
    a = rng.standard_normal((100_000, 3)); b = rng.standard_normal((100_000, 3))
    v = rule_verdicts(a, b, margins=(1,))
    assert abs(v["R"].mean() - 0.10) < 0.005          # closed form 2(3!)^2/6!
    assert 0.02 < v["W"].mean() < 0.06                 # Welch at k=3 is conservative (about 0.035), never anti-conservative
    assert v["S2"].mean() > v["S1"].mean() > v["R"].mean()


def test_paired_task_verdicts_match_scipy():
    rng = np.random.default_rng(3)
    n, k = 60, 3
    p = rng.random(n)
    xa = rng.random((50, k, n)) < p; xb = rng.random((50, k, n)) < p
    v = paired_task_verdicts(xa, xb, margins=(3,))
    for i in range(50):
        d = (xb[i].mean(0) - xa[i].mean(0)) * 100
        assert v["P"][i] == (ttest_rel(xb[i].mean(0) * 100, xa[i].mean(0) * 100).pvalue < 0.05)
        from scipy.stats import t as tdist
        hw = tdist.ppf(0.95, n - 1) * d.std(ddof=1) / math.sqrt(n)
        assert v["PE3"][i] == (abs(d.mean()) + hw <= 3)


def test_tost_power_monotone_in_k_and_margin():
    assert tost_power(3, 0, 2, 3) < tost_power(6, 0, 2, 3) < tost_power(12, 0, 2, 3)
    assert tost_power(5, 0, 2, 2) < tost_power(5, 0, 2, 3) < tost_power(5, 0, 2, 5)


def _snapshot(tmp_path):
    snap = tmp_path / "snap"; snap.mkdir()
    (snap / "alpha.json").write_text(json.dumps([{
        "adapter_name": "alpha", "agent": "x", "model": "m", "number_of_runs": 3, "adapted_benchmark_size": 100, "parity_benchmark_size": 50,
        "metrics": [{"metric": "acc_stderr", "original": "1 +/- 0", "harbor": "1 +/- 0", "original_runs": [1, 1, 1], "harbor_runs": [1, 1, 1]},
                    {"metric": "Mean Semantic Score", "original": "0.5", "harbor": "0.5", "original_runs": [0.5, 0.6, 0.7], "harbor_runs": [0.55, 0.65, 0.6]},
                    {"metric": "Resolved Rate (%)", "original": "40.3 +/- 0.4", "harbor": "43.0 +/- 1.4", "original_runs": [39.5, 40.5, 41.0], "harbor_runs": [45.7, 42.1, 41.1]}]}]))
    (snap / "beta.json").write_text(json.dumps([{
        "adapter_name": "beta", "agent": "y", "model": "m", "number_of_runs": 3,
        "metrics": [{"metric": "Partial Score (%)", "benchmark_name": f"p{i}", "original_runs": [10 * i, 10 * i, 10 * i], "harbor_runs": [10 * i + 1, 10 * i + 1, 10 * i + 1]} for i in range(6)]}]))
    (snap / "gamma.json").write_text(json.dumps({"adapter_name": "gamma", "agent": "z", "model": "m",
        "metrics": [{"metric": "success rate (pass@1, no-result counted as 0)", "original": "0.40", "harbor": "0.42", "original_runs": [0.4], "harbor_runs": [0.42]},
                    {"metric": "rate", "original": "40", "harbor": "40", "original_runs": [], "tb_adapter_runs": [40.0]}]}))
    tables = tmp_path / "tables.csv"
    with open(tables, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["table", "benchmark", "subdomain", "scenario", "mode", "parity_agent", "parity_model", "k", "parity_set", "orig", "harbor", "orig_mean", "orig_sem", "harbor_mean", "harbor_sem", "parity_n", "full_n", "n_json_matches"])
        w.writeheader()
        w.writerow({"table": 3, "benchmark": "Alpha", "orig": "40.3 ± 0.4", "harbor": "43.0 ± 1.4", "orig_mean": 40.3, "harbor_mean": 43.0, "k": 3, "parity_set": "50/100"})
    return snap, tables


def test_builder_applies_the_preregistered_rule(tmp_path):
    snap, tables = _snapshot(tmp_path)
    out = tmp_path / "out"
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "scripts", "p2_build_comparisons.py"), str(snap), str(tables), str(out)], check=True, capture_output=True)
    rows = {r["adapter"]: r for r in csv.DictReader(open(out / "comparisons.csv"))}
    log = json.load(open(out / "selection_log.json"))
    # alpha: table match wins over the earlier headline-free rows; acc_stderr excluded by token, Semantic not excluded
    assert rows["alpha"]["metric"] == "Resolved Rate (%)" and rows["alpha"]["selection_branch"] == "1:paper_table"
    assert "acc_stderr" in log["excluded_side_quantities"] and "Mean Semantic Score" not in log["excluded_side_quantities"]
    assert rows["alpha"]["parity_set"] == "subset"
    # beta: six per-task rows aggregated by run index; mean over rows of run i
    assert rows["beta"]["selection_branch"] == "2b:aggregated_per_group_rows"
    assert json.loads(rows["beta"]["original_runs"]) == [25.0, 25.0, 25.0] and json.loads(rows["beta"]["harbor_runs"]) == [26.0, 26.0, 26.0]
    # gamma: 'counted' is not 'count'; fractions scaled; single-run flagged; the tb_adapter row is a leg, not a comparison
    assert rows["gamma"]["metric"].startswith("success rate") and rows["gamma"]["single_run_side"] == "True" and rows["gamma"]["scaled_x100"] == "True"
    assert json.loads(rows["gamma"]["harbor_runs"]) == [42.0]
    assert log["n_legs"] == 0  # tb leg has no original list, so no leg either


def test_cmh_matches_manual_and_mcnemar():
    rng = np.random.default_rng(5)
    n, k = 40, 3
    xa = rng.random((20, k, n)) < 0.5; xb = rng.random((20, k, n)) < 0.5
    v = paired_task_verdicts(xa, xb, margins=(3,))
    for i in range(20):
        a = xb[i].sum(0); T = xa[i].sum(0) + a; K = 2 * k
        num = (a - k * T / K).sum(); var = (k * k * T * (K - T) / (K ** 2 * (K - 1))).sum()
        assert v["CMH"][i] == (abs(num / math.sqrt(var)) > 1.959964)
    # k = 1 reduces to McNemar's z on discordant tasks: z = (b - c) / sqrt(b + c)
    xa1 = rng.random((50, 1, n)) < 0.5; xb1 = rng.random((50, 1, n)) < 0.5
    v1 = paired_task_verdicts(xa1, xb1, margins=(3,))
    for i in range(50):
        b = int(((xb1[i, 0] == 1) & (xa1[i, 0] == 0)).sum()); c = int(((xb1[i, 0] == 0) & (xa1[i, 0] == 1)).sum())
        z = (b - c) / math.sqrt(b + c) if b + c else 0.0
        assert v1["CMH"][i] == (abs(z) > 1.959964)
