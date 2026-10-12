"""Tests for the Phase 0 definitions. Run: .venv/bin/python -I -m pytest -q"""
import json
import math
import os
import subprocess
import sys

import pytest

from parity_lib import (diff_ci_halfwidth, lenient_runs, numeric_runs, parse_pm, pooled_sd, range_separation,
                        ranges_overlap, rule_false_alarm_binomial_sim, rule_false_alarm_exact, rule_mismatch_rate_normal,
                        rule_mismatch_rate_sim, runs_needed_plugin, runs_needed_power, sem, side_runs, t_quantile,
                        tost_power, welch_ci_halfwidth)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_closed_form_values():
    assert rule_false_alarm_exact(2) == pytest.approx(1 / 3)
    assert rule_false_alarm_exact(3) == pytest.approx(0.1)
    assert rule_false_alarm_exact(5) == pytest.approx(1 / 126)
    assert rule_false_alarm_exact(8) == pytest.approx(1 / 6435)


@pytest.mark.parametrize("k", [1, 2, 3, 4, 5, 8])
def test_exact_integral_matches_closed_form_at_zero_gap(k):
    assert rule_mismatch_rate_normal(k, 0.0) == pytest.approx(rule_false_alarm_exact(k), rel=1e-6, abs=1e-9)


@pytest.mark.parametrize("k,delta", [(2, 0), (3, 0), (3, 2), (5, 2), (8, 3)])
def test_simulation_matches_exact_within_monte_carlo_error(k, delta):
    n = 100_000
    p = rule_mismatch_rate_normal(k, delta)
    p_hat = rule_mismatch_rate_sim(k, delta, n=n, seed=11)
    se = math.sqrt(max(p * (1 - p), 1e-6) / n)
    assert abs(p_hat - p) < 5 * se + 1e-4


def test_rule_gets_weaker_as_runs_increase_for_a_fixed_gap():
    # detection probability for a 2 SD gap falls as k grows
    rates = [rule_mismatch_rate_normal(k, 2.0) for k in (2, 3, 5, 8)]
    assert rates == sorted(rates, reverse=True)


def test_rule_weak_against_a_two_sd_gap_at_k3():
    assert 0.60 < rule_mismatch_rate_normal(3, 2.0) < 0.66   # detection ~62%, so it misses ~38%


def test_ranges_overlap():
    assert ranges_overlap([39.5, 40.5, 41.0], [41.0, 42.1, 45.7])     # touching counts as overlap
    assert not ranges_overlap([39.5, 40.5, 41.0], [41.1, 42.1, 45.7])  # usaco: fails by 0.1
    assert ranges_overlap([33.33] * 3, [16.67, 58.33, 50.0])          # rexbench: noisy side passes
    a, b = [0.09085135251589957, 0.06666666666666667], [0.09085135251589958] * 3  # pixiu acc_stderr
    assert not ranges_overlap(a, b) and ranges_overlap(a, b, eps=1e-9)  # a 1e-17 floating-point tie
    assert 0 < range_separation(a, b) < 1e-9
    assert range_separation([39.5, 40.5, 41.0], [45.7, 42.1, 41.1]) == pytest.approx(0.1)
    assert range_separation([1, 3], [2, 4]) < 0


def test_parse_pm():
    assert parse_pm("40.3 +/- 0.44") == (40.3, 0.44)
    assert parse_pm("45.2 ± 1.3") == (45.2, 1.3)
    assert parse_pm("65.0% ± 6.5%") == (65.0, 6.5)
    assert parse_pm("68.0") == (68.0, None)
    assert parse_pm(None) is None and parse_pm("n/a") is None


def test_run_list_parsing():
    assert numeric_runs([1, 2.5, "3", True, None]) == [1.0, 2.5]
    assert numeric_runs(["58.3%"]) is None
    assert lenient_runs(["58.3%", "56.2", 60]) == [58.3, 56.2, 60.0]
    assert lenient_runs(["abc"]) is None
    assert side_runs({"original_trials": [1, 2]}, "original") == [1.0, 2.0]
    assert side_runs({"tb_adapter_runs": [1, 2]}, "harbor") is None


def test_sem_matches_guide_formula():
    x = [44.0, 45.5, 46.1]
    xbar = sum(x) / 3
    expected = math.sqrt(sum((v - xbar) ** 2 for v in x) / (3 * 2))
    assert sem(x) == pytest.approx(expected)


def test_pooled_sd_and_t():
    assert pooled_sd([1, 2, 3], [2, 3, 4]) == pytest.approx(1.0)
    assert t_quantile(0.975, 4) == pytest.approx(2.776, abs=1e-3)
    assert t_quantile(0.95, 4) == pytest.approx(2.132, abs=1e-3)


def test_snapshot_matches_manifest():
    import hashlib
    man = json.load(open(os.path.join(ROOT, "data/raw/MANIFEST.json")))
    for name, info in man["files"].items():
        p = os.path.join(ROOT, "data/raw", "harbor_parity" if name.endswith(".json") else "", name)
        assert hashlib.sha256(open(p, "rb").read()).hexdigest() == info["sha256"], name


def test_scripts_run_on_synthetic_snapshot(tmp_path):
    snap = tmp_path / "snap"; snap.mkdir(); out = tmp_path / "out"
    (snap / "alpha.json").write_text(json.dumps([{"adapter_name": "alpha", "number_of_runs": 3,
        "adapted_benchmark_size": 100, "parity_benchmark_size": 50, "metrics": [
            {"metric": "acc_stderr", "original_runs": [1, 1, 1], "harbor_runs": [1, 1, 1]},
            {"metric": "acc", "original_runs": [0.5, 0.6, 0.7], "harbor_runs": [0.55, 0.65, 0.6]}]}]))
    (snap / "beta.json").write_text(json.dumps({"adapter_name": "beta", "metrics": [
            {"metric": "rate", "original_runs": [10], "harbor_runs": [20, 30]}]}))
    py = sys.executable
    for s in ("p0_inventory.py", "p0_overlap.py", "p0_first_pass_cut.py"):
        subprocess.run([py, "-I", os.path.join(ROOT, "scripts", s), str(snap), str(out)], check=True, capture_output=True)
    inv = json.load(open(out / "inventory.json")); ov = json.load(open(out / "overlap.json")); fp = json.load(open(out / "first_pass_cut.json"))
    assert inv["n_experiments"] == 2 and inv["n_metric_rows"] == 3
    assert inv["runs_per_side_by_experiment"] == {"3": 1, "missing": 1}
    assert inv["parity_set"] == {"subset": 1, "unknown": 1}
    assert ov["n_paired"] == 3 and ov["n_fail_overlap"] == 1 and ov["n_fail_overlap_single_run_side"] == 1
    assert ov["n_identical_lists"] == 1 and ov["n_zero_spread_both"] == 1
    assert fp["n_analysed"] == 1 and fp["n_excluded_zero_spread_both"] == 0
    row = json.load(open(out / "first_pass_cut.json"))
    assert row["largest_gaps"][0][0] == "alpha" and row["largest_gaps"][0][1] == "acc"


def test_mismatch_rate_is_even_in_delta():
    for k, d in ((3, 2.0), (3, 13.0), (5, 0.7)):
        assert rule_mismatch_rate_normal(k, d) == pytest.approx(rule_mismatch_rate_normal(k, -d), abs=1e-9)


def test_pooled_sd_general_formula_and_ci():
    a, b = [1.0, 2.0, 3.0], [2.0, 3.0, 4.0, 5.0]
    import statistics
    sp = math.sqrt((2 * statistics.variance(a) + 3 * statistics.variance(b)) / 5)
    assert pooled_sd(a, b) == pytest.approx(sp)
    assert diff_ci_halfwidth(a, b, 0.95) == pytest.approx(t_quantile(0.975, 5) * sp * math.sqrt(1 / 3 + 1 / 4))
    with pytest.raises(ValueError):
        pooled_sd([1.0], [1.0, 2.0])


def test_ci_matches_scipy_ttest():
    from scipy.stats import ttest_ind
    a, b = [39.5, 40.5, 41.0], [45.7, 42.1, 41.1]
    ci = ttest_ind(a, b, equal_var=True).confidence_interval(0.95)
    assert (ci.high - ci.low) / 2 == pytest.approx(diff_ci_halfwidth(a, b, 0.95), rel=1e-9)
    ciw = ttest_ind(a, b, equal_var=False).confidence_interval(0.95)
    assert (ciw.high - ciw.low) / 2 == pytest.approx(welch_ci_halfwidth(a, b, 0.95), rel=1e-9)


def test_tost_power_matches_simulation():
    import numpy as np
    rng = np.random.default_rng(3)
    k, D, sigma, m, n = 3, 0.6, 2.16, 5.0, 200_000
    a = rng.normal(0, sigma, (n, k)); b = rng.normal(D, sigma, (n, k))
    sp = np.sqrt((a.var(axis=1, ddof=1) + b.var(axis=1, ddof=1)) / 2)
    passes = np.abs(a.mean(axis=1) - b.mean(axis=1)) + t_quantile(0.95, 2 * k - 2) * sp * math.sqrt(2 / k) <= m
    p_hat = passes.mean(); p = tost_power(k, D, sigma, m)
    assert abs(p_hat - p) < 5 * math.sqrt(p * (1 - p) / n) + 1e-3
    assert tost_power(50, 0.0, 2.0, 3.0) > 0.99
    assert tost_power(3, 2.5, 2.0, 3.0) < 0.2


def test_plugin_rule_has_low_power_and_power_rule_needs_more_runs():
    # the first pass's 14 / 6 / 3 runs per side have only ~40-55% TOST power at gap 0.6, sigma 2.16
    for m, k in ((2, 14), (3, 6), (5, 3)):
        assert runs_needed_plugin(m, 0.6, 2.16) == k
        assert 0.35 < tost_power(k, 0.6, 2.16, m) < 0.6
    assert runs_needed_power(2, 0.6, 2.16, 0.8) == 31
    assert runs_needed_power(3, 0.6, 2.16, 0.8) == 12
    assert runs_needed_power(5, 0.6, 2.16, 0.8) == 5


def test_discrete_scores_make_false_alarm_rate_an_upper_bound():
    cont = rule_false_alarm_exact(3)
    p30 = rule_false_alarm_binomial_sim(3, 30, 0.4, n=100_000)
    p1000 = rule_false_alarm_binomial_sim(3, 1000, 0.4, n=100_000)
    assert p30 < p1000 < cont and p30 < 0.08 and 0.085 < p1000 < 0.1
