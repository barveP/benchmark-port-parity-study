#!/usr/bin/env python3
"""Shared helpers for the port-parity analysis.

Every analysis script imports from here, so each definition lives in one place.
Dependencies: standard library, numpy, scipy.

Vocabulary (one line each)
  experiment : one agent+model comparison inside a parity_experiment.json (one JSON object)
  metric row : one entry of an experiment's "metrics" list (one scored quantity)
  side       : "original" (upstream harness) or "harbor" (the port); some rows add "tb_adapter"
  run list   : per-run scores for one side, e.g. original_runs = [39.5, 40.5, 41.0]
  k          : runs per side
  SEM        : standard error of the mean = sample SD / sqrt(k)
"""
from __future__ import annotations

import glob
import json
import math
import os
import re
import statistics

# ----------------------------------------------------------------------------- loading


def snapshot_files(root: str) -> list[str]:
    """Parity JSON files under `root`.

    Accepts our pinned snapshot (data/raw/harbor_parity/<adapter>.json) or a Harbor
    checkout (<root>/adapters/<adapter>/parity_experiment.json). Sorted by path, so the
    adapter order is alphabetical in both layouts.
    """
    a = sorted(glob.glob(os.path.join(root, "adapters", "*", "parity_experiment.json")))
    if a:
        return a
    b = [f for f in sorted(glob.glob(os.path.join(root, "*.json")))
         if os.path.basename(f) != "MANIFEST.json"]
    if not b:
        raise FileNotFoundError(f"no parity files under {root}")
    return b


def adapter_name(path: str) -> str:
    base = os.path.basename(path)
    if base == "parity_experiment.json":
        return os.path.basename(os.path.dirname(path))
    return os.path.splitext(base)[0]


def iter_experiments(root: str):
    """Yield (adapter, index_within_file, experiment_dict) in file order."""
    for f in snapshot_files(root):
        with open(f) as fh:
            d = json.load(fh)
        exps = d if isinstance(d, list) else [d]
        for i, e in enumerate(exps):
            yield adapter_name(f), i, e


def iter_metric_rows(root: str):
    """Yield (adapter, exp_index, experiment, metric_index, metric_row) in file order."""
    for adapter, i, e in iter_experiments(root):
        for j, m in enumerate(e.get("metrics") or []):
            yield adapter, i, e, j, m


# ----------------------------------------------------------------------------- run lists


def is_num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def numeric_runs(v):
    """First-pass convention: keep only numeric entries of a run list; None if none remain."""
    if not isinstance(v, list):
        return None
    nums = [float(x) for x in v if is_num(x)]
    return nums or None


def side_runs(m: dict, side: str):
    """First-pass convention: first non-empty numeric list among <side>_runs, <side>_trials."""
    for suf in ("_runs", "_trials"):
        nums = numeric_runs(m.get(side + suf))
        if nums:
            return nums
    return None


_PCT = re.compile(r"^\s*([-+]?\d+(?:\.\d+)?)\s*%?\s*$")


def lenient_runs(v):
    """Phase-2 convention: also accept strings such as '58.3%' or '58.7'. None if any entry fails."""
    if not isinstance(v, list) or not v:
        return None
    out = []
    for x in v:
        if is_num(x):
            out.append(float(x))
        elif isinstance(x, str) and _PCT.match(x):
            out.append(float(_PCT.match(x).group(1)))
        else:
            return None
    return out


_PM = re.compile(
    r"^\s*([-+]?\d+(?:\.\d+)?)\s*%?\s*(?:(?:\+/-|±|\+-|\\pm)\s*([-+]?\d+(?:\.\d+)?)\s*%?)?\s*$"
)


def parse_pm(s):
    """Parse a reported 'mean ± err' string ('40.3 +/- 0.44', '65.0% ± 6.5%', '68.0').

    Returns (mean, err) with err=None when absent, or None when the string does not parse.
    """
    if not isinstance(s, str):
        return None
    s = re.sub(r"\s*\([^)]*\)\s*$", "", s)  # drop a trailing note such as "(stderr across 3 runs)"
    m = _PM.match(s)
    if not m:
        return None
    return float(m.group(1)), (float(m.group(2)) if m.group(2) is not None else None)


# ----------------------------------------------------------------------------- statistics


def mean(x):
    return sum(x) / len(x)


def sample_sd(x):
    return statistics.stdev(x) if len(x) > 1 else float("nan")


def sem(x):
    """Harbor's reporting convention: sample SD / sqrt(k)."""
    return sample_sd(x) / math.sqrt(len(x))


def pooled_sd(a, b):
    """Pooled run-to-run SD under equal variance: sqrt(((k1-1) var_a + (k2-1) var_b) / (k1+k2-2)).

    With equal k this is sqrt((var_a + var_b) / 2). Needs at least 2 runs on each side.
    """
    k1, k2 = len(a), len(b)
    if min(k1, k2) < 2:
        raise ValueError("pooled_sd needs at least 2 runs per side")
    return math.sqrt(((k1 - 1) * statistics.variance(a) + (k2 - 1) * statistics.variance(b)) / (k1 + k2 - 2))


def diff_ci_halfwidth(a, b, conf: float = 0.95):
    """Half-width of the pooled-t confidence interval for mean(a) - mean(b).

    hw = t_{(1+conf)/2, k1+k2-2} * s_p * sqrt(1/k1 + 1/k2). conf=0.90 gives the TOST interval:
    equivalence within +-m at alpha=0.05 holds iff |gap| + hw90 <= m.
    """
    k1, k2 = len(a), len(b)
    return t_quantile((1 + conf) / 2, k1 + k2 - 2) * pooled_sd(a, b) * math.sqrt(1 / k1 + 1 / k2)


def welch_ci_halfwidth(a, b, conf: float = 0.95):
    """Half-width of the Welch (unequal-variance) interval for mean(a) - mean(b), Satterthwaite df."""
    k1, k2 = len(a), len(b)
    v1, v2 = statistics.variance(a) / k1, statistics.variance(b) / k2
    se = math.sqrt(v1 + v2)
    if se == 0:
        return 0.0
    df = (v1 + v2) ** 2 / ((v1 ** 2 / (k1 - 1)) + (v2 ** 2 / (k2 - 1)))
    return t_quantile((1 + conf) / 2, df) * se


def ranges_overlap(a, b, eps: float = 0.0) -> bool:
    """Harbor's matching criterion (adapters/ADAPTER_CONTRIBUTING.md, Step 5).

    eps > 0 treats ranges separated by less than eps as touching; the first pass used eps = 0,
    which lets a floating-point difference of 1e-17 count as a non-overlap.
    """
    return max(a) + eps >= min(b) and max(b) + eps >= min(a)


def range_separation(a, b) -> float:
    """Distance between the two run ranges: positive when they do not overlap, else <= 0."""
    return max(min(b) - max(a), min(a) - max(b))


def zero_spread(x) -> bool:
    return len(set(x)) == 1


def rule_false_alarm_exact(k: int) -> float:
    """P(ranges do not overlap | both sides identically distributed, k runs per side).

    All 2k runs are exchangeable, so each way of choosing which k of the 2k sorted positions
    belong to 'original' is equally likely: C(2k, k) ways. The ranges fail to overlap only when
    one side holds the k lowest positions and the other the k highest: 2 ways. Hence
    P = 2 / C(2k, k) = 2 (k!)^2 / (2k)!.  k=2: 1/3, k=3: 1/10, k=5: 1/126, k=8: 1/6435.
    This holds for ANY continuous noise distribution, not only the normal.
    """
    return 2.0 * math.factorial(k) ** 2 / math.factorial(2 * k)


def rule_mismatch_rate_normal(k: int, delta: float) -> float:
    """Exact P(ranges do not overlap) for k normal runs per side, unit SD, true gap delta.

    P(max A < min B) = integral of k phi(x) Phi(x)^(k-1) (1 - Phi(x - delta))^k dx, and the
    mirror term for max B < min A. delta is in units of the run-to-run SD.
    """
    from scipy.integrate import quad
    from scipy.stats import norm

    def a_below_b(x):
        return k * norm.pdf(x) * norm.cdf(x) ** (k - 1) * norm.sf(x - delta) ** k

    def b_below_a(y):
        return k * norm.pdf(y - delta) * norm.cdf(y - delta) ** (k - 1) * norm.sf(y) ** k

    delta = abs(delta)  # the probability is even in delta; integrate on the side where mass lies
    lo, hi = -12.0, 12.0 + delta
    p1, _ = quad(a_below_b, lo, hi, limit=200)
    p2, _ = quad(b_below_a, lo, hi, limit=200)
    return p1 + p2


def rule_mismatch_rate_sim(k: int, delta: float, n: int = 200_000, seed: int = 7) -> float:
    """Monte Carlo estimate of the same quantity with normal noise (vectorised, fixed seed)."""
    import numpy as np

    rng = np.random.default_rng(seed)
    a = rng.standard_normal((n, k))
    b = rng.standard_normal((n, k)) + delta
    miss = (a.max(axis=1) < b.min(axis=1)) | (b.max(axis=1) < a.min(axis=1))
    return float(miss.mean())


def rule_false_alarm_binomial_sim(k: int, n_tasks: int, p: float, n: int = 200_000, seed: int = 7) -> float:
    """False-alarm rate of the overlap rule when each run score is a pass rate over n_tasks tasks.

    Scores are discrete, so ties happen and count as overlap under the '>=' rule; the result is
    below the continuous value 2 (k!)^2 / (2k)!.
    """
    import numpy as np

    rng = np.random.default_rng(seed)
    a = rng.binomial(n_tasks, p, (n, k)) / n_tasks
    b = rng.binomial(n_tasks, p, (n, k)) / n_tasks
    miss = (a.max(axis=1) < b.min(axis=1)) | (b.max(axis=1) < a.min(axis=1))
    return float(miss.mean())


def t_quantile(p: float, df) -> float:
    """Student-t quantile, e.g. t_quantile(0.975, 4) = 2.776."""
    from scipy.stats import t

    return float(t.ppf(p, df))


def tost_power(k: int, true_gap: float, sigma: float, margin: float, alpha: float = 0.05) -> float:
    """P(pooled-t TOST at level alpha shows equivalence within +-margin) with k runs per side.

    Model: run scores normal with common SD sigma; true mean gap D = true_gap. The observed gap
    dhat ~ N(D, sigma^2 c^2) with c = sqrt(2/k), independent of s_p where nu s_p^2 / sigma^2 ~ chi2(nu),
    nu = 2k - 2. TOST passes iff |dhat| + t_{1-alpha, nu} s_p c <= margin. Integrating over s_p:
      power = int chi2_nu(v) [ Phi((m - t c s - D)/(sigma c)) - Phi((-m + t c s - D)/(sigma c)) ]_+ dv,
    with s = sigma sqrt(v / nu). (This is what the plug-in 'runs needed' rule does NOT compute.)
    """
    from scipy.integrate import quad
    from scipy.stats import chi2, norm

    nu = 2 * k - 2
    c = math.sqrt(2 / k)
    tq = t_quantile(1 - alpha, nu)

    def integrand(v):
        s = sigma * math.sqrt(v / nu)
        hi = (margin - tq * c * s - true_gap) / (sigma * c)
        lo = (-margin + tq * c * s - true_gap) / (sigma * c)
        return chi2.pdf(v, nu) * max(0.0, norm.cdf(hi) - norm.cdf(lo))

    # the bracket is zero once t c s >= margin, i.e. v >= nu (margin / (t c sigma))^2
    v_max = nu * (margin / (tq * c * sigma)) ** 2
    val, _ = quad(integrand, 0, v_max, limit=400)
    return float(val)


def runs_needed_power(margin: float, true_gap: float, sigma: float, power: float = 0.8,
                      alpha: float = 0.05, kmax: int = 2000):
    """Smallest k (runs per side) with tost_power >= power; None if not reached by kmax."""
    for k in range(2, kmax + 1):
        if tost_power(k, true_gap, sigma, margin, alpha) >= power:
            return k
    return None


def runs_needed_plugin(margin: float, gap0: float, sigma: float, alpha: float = 0.05, kmax: int = 2000):
    """The first pass's heuristic: smallest k with gap0 + t_{1-alpha, 2k-2} sigma sqrt(2/k) <= margin.

    This is the k at which a comparison landing exactly on (gap0, sigma) would pass; its actual
    TOST power at that k is well below 80% (0.1 to 0.8 depending on margin and noise). Kept for
    comparison with tost_power.
    """
    for k in range(2, kmax + 1):
        if gap0 + t_quantile(1 - alpha, 2 * k - 2) * sigma * math.sqrt(2 / k) <= margin:
            return k
    return None


def rule_verdicts(a, b, margins=(1, 2, 3, 5, 10)):
    """Vectorised decision rules on run scores. a, b: arrays of shape (trials, k1) and (trials, k2).

    Returns a dict of boolean arrays:
      R   range overlap fails (Harbor's rule, ties count as overlap)        True = mismatch
      S1  mean ± SEM bars do not overlap: |gap| > SEM_a + SEM_b              True = mismatch
      S2  |gap| > SE of the difference, i.e. |t| > 1                         True = mismatch
      S3  |gap| > max(SEM_a, SEM_b), the literal reading of "within sample SEM"  True = mismatch
      W   Welch t-test rejects at 0.05 (Satterthwaite df; conservative at k <= 5)  True = mismatch
      T   pooled t-test rejects at 0.05 (k1 + k2 - 2 df; the reference test)  True = mismatch
      E<m> TOST at margin m (pooled t, alpha .05): |gap| + hw90 <= m         True = equivalence shown
    gap is mean(b) - mean(a). If both sides have zero spread, W and T count unequal means as a
    mismatch (adds at most 0.7 points to their false alarm with 10 tasks, nothing at 30 or more).
    S1, S2, T and W are the same statistic at different thresholds when k1 = k2.
    """
    import numpy as np
    from scipy.stats import t as tdist

    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    k1, k2 = a.shape[1], b.shape[1]
    ma, mb = a.mean(1), b.mean(1)
    va, vb = a.var(1, ddof=1), b.var(1, ddof=1)
    gap = mb - ma
    sea, seb = np.sqrt(va / k1), np.sqrt(vb / k2)
    out = {"R": (a.max(1) < b.min(1) - 1e-9) | (b.max(1) < a.min(1) - 1e-9),
           "S1": np.abs(gap) > sea + seb + 1e-12,
           "S2": np.abs(gap) > np.sqrt(sea ** 2 + seb ** 2) + 1e-12,
           "S3": np.abs(gap) > np.maximum(sea, seb) + 1e-12}
    se2 = va / k1 + vb / k2
    with np.errstate(divide="ignore", invalid="ignore"):
        tw = np.where(se2 > 0, gap / np.sqrt(se2), np.where(gap != 0, np.inf, 0.0))
        df = np.where(se2 > 0, se2 ** 2 / ((va / k1) ** 2 / (k1 - 1) + (vb / k2) ** 2 / (k2 - 1)), 1.0)
        df = np.where(np.isfinite(df) & (df > 0), df, 1.0)
        out["W"] = 2 * tdist.sf(np.abs(tw), df) < 0.05
    sp = np.sqrt(((k1 - 1) * va + (k2 - 1) * vb) / (k1 + k2 - 2))
    se_p = sp * math.sqrt(1 / k1 + 1 / k2)
    hw90 = t_quantile(0.95, k1 + k2 - 2) * se_p
    hw95 = t_quantile(0.975, k1 + k2 - 2) * se_p
    out["T"] = np.abs(gap) > hw95 + 1e-12
    out["t_pooled_abs"] = np.where(se_p > 0, np.abs(gap) / np.where(se_p > 0, se_p, 1.0), np.where(gap != 0, np.inf, 0.0))
    for m in margins:
        out[f"E{m}"] = np.abs(gap) + hw90 <= m
    return out


def paired_task_verdicts(xa, xb, margins=(3, 5)):
    """Paired per-task test. xa, xb: arrays (trials, k, n_tasks) of outcomes in [0, 1] for the same tasks.

    d_i = task mean on side b minus task mean on side a, in points. Paired t on d_i (n_tasks - 1 df):
      P      rejects at 0.05                      True = mismatch
      PE<m>  |mean d| + t(.95) SE <= m            True = equivalence shown
    """
    import numpy as np
    from scipy.stats import t as tdist

    d = (np.asarray(xb, dtype=float).mean(1) - np.asarray(xa, dtype=float).mean(1)) * 100
    n = d.shape[1]
    md, sd = d.mean(1), d.std(1, ddof=1)
    se = sd / math.sqrt(n)
    with np.errstate(divide="ignore", invalid="ignore"):
        tt = np.where(se > 0, md / se, np.where(md != 0, np.inf, 0.0))
    out = {"P": 2 * tdist.sf(np.abs(tt), n - 1) < 0.05}
    hw90 = t_quantile(0.95, n - 1) * se
    for m in margins:
        out[f"PE{m}"] = np.abs(md) + hw90 <= m
    # Cochran-Mantel-Haenszel z, stratified by task (binary outcomes; McNemar at k = 1):
    # a_i = port passes over k_b runs, T_i = passes over all runs of task i; under the null of
    # exchangeable outcomes within a task, E[a_i] = k_b T_i / (k_a + k_b) and
    # Var[a_i] = k_a k_b T_i (K - T_i) / (K^2 (K - 1)) with K = k_a + k_b (hypergeometric).
    xa_, xb_ = np.asarray(xa, dtype=float), np.asarray(xb, dtype=float)
    ka, kb = xa_.shape[1], xb_.shape[1]
    K = ka + kb
    a_i = xb_.sum(1)
    T_i = xa_.sum(1) + a_i
    num = (a_i - kb * T_i / K).sum(1)
    var = (ka * kb * T_i * (K - T_i) / (K ** 2 * (K - 1))).sum(1)
    with np.errstate(divide="ignore", invalid="ignore"):
        z = np.where(var > 0, num / np.sqrt(np.where(var > 0, var, 1.0)), np.where(num != 0, np.inf, 0.0))
    out["CMH"] = np.abs(z) > 1.959964
    return out
