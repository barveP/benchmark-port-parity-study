# Memo: Phase 2, the analysis

Date: 2026-10-11. Branch `phase-2`. Rules were fixed in `memos/phase-2-preregistration.md` before any outcome was computed; five amendments are recorded there with their reasons and timing. Every number below comes from a script in `scripts/` and an output file in `results/phase2/`; the map is in `results/phase2/NUMBERS_phase2.md`. Independent checks: two blind re-derivations of the RQ2 headline from the pre-registration text (one matched exactly; the other differed only in choices the text left open, which became amendment 4), a code review and a statistics review of RQ1 and RQ2, and the same for RQ3 (section 11 records what they changed).

## 1. Bottom line

- **What the rule guarantees (RQ1).** With three runs per side, Harbor's range-overlap rule flags a perfect port 10% of the time (5 to 9% for discrete pass rates), and catches a gap of two run-to-run SDs 62% of the time. At its own false-alarm rate it is nearly as good as a t-test (64%). Its defects are structural: its false-alarm rate is set by the run count alone (33%, 10%, 2.9%, 0.8% at 2, 3, 4, 5 runs); for any fixed gap its detection falls as runs are added (78% at k = 2, 9% at k = 10, while a t-test rises from 22% to 99%); it passes more easily the noisier the runs; and a pass means only "not rejected at the 10% level", never equivalence. The paper's own wording ("within standard errors") is stricter, not laxer: 25 to 44% false alarms depending on the reading.
- **What the published evidence establishes (RQ2).** The 58 comparisons with three runs per side look close: median gap 0.7 points, no gap distinguishable from zero. But with three runs the median smallest provable margin is 4.4 points; equivalence within 3 points can be shown for 22 of 58 and within 5 points for 36. Twenty-one comparisons pass the overlap rule yet cannot show equivalence within 5 points, and the rule passes the four largest gaps (15.6, 8.3, 4.9 and 4.6 points). The published data also show far fewer rule failures than a perfect-parity model predicts (1 against 5.8 expected), which is what one expects when ports are revised until the rule passes: pass rates cannot validate the rule.
- **What would fix it (RQ3).** Showing equivalence within 3 points at 80% power needs about 7 runs per side at the median noise (4 at the quietest quartile, 16 at the noisiest); within 5 points, 3 to 6. A paired per-task analysis does not tighten the interval on average (the run-level interval is narrower for 17 of 31 adapters); it reveals that 23 to 41% of tasks have different pass rates on the two sides, which the run-level numbers hide. Injecting defects into real per-task outcomes shows that with three runs every test, including the overlap rule, catches a defect that breaks 10% of tasks only about half the time, and that a perfect port can be shown equivalent within 5 points only half the time; both improve with runs, the overlap rule does not.

## 2. The comparison table (pre-registered rule)

The 121 experiments give 82 comparisons between the original harness and the Harbor port, plus 15 transitive legs through the Terminal-Bench adapter kept as a secondary set. The 39 experiments without a comparison are Harbor-only runs, rows whose "original" value is a published leaderboard number with no run list (aa-lcr), reported means with empty run lists (evoeval), or transitive entries. The main metric came from the paper's Tables 3 and 4 in 48 cases plus Frontier-CS whose aggregated per-problem rows match the table, from per-group aggregation in 1 (Multi-SWE-bench, seven languages of ten tasks), from a headline name in 29, and from "first remaining row" in 3. Run counts: 61 comparisons have 3 runs per side, 7 have 2, 5 have 5, 2 have 4, 2 have 6, 1 has 3 against 5, and 4 have a single run on at least one side. Script `scripts/p2_build_comparisons.py`; outputs `comparisons.csv`, `comparisons_legs.csv`, `selection_log.json`.

## 3. RQ1: what the rule guarantees

Script `scripts/p2_rq1_rules.py`; output `rq1_rules.json`; figure `figures/fig_rq1_rules.png`. Rules: R range overlap; S1 mean ± SEM bars overlap; S2 gap within the standard error of the difference; S3 gap within one side's SEM (the literal reading of D.7); T pooled t-test at 0.05; W Welch t-test at 0.05; E(m) TOST equivalence within ±m. All rates are properties of the rule under a stated noise model, not of the published ports (see the selection check below).

**Normal noise, three runs per side.** Rows: false alarm (perfect port flagged), detection of a 1 SD and a 2 SD gap, and the detection of the pooled t-statistic tuned to the same false alarm.

| rule | false alarm | detects 1 SD | detects 2 SD | t at same false alarm, 2 SD |
|---|---|---|---|---|
| R range overlap | 0.100 | 0.26 | 0.62 | 0.64 |
| S1 SEM bars overlap | 0.254 | 0.50 | 0.86 | 0.86 |
| S2 within SE of difference | 0.374 | 0.63 | 0.92 | 0.92 |
| S3 within one SEM | 0.439 | 0.68 | 0.94 | 0.94 |
| T pooled t, 0.05 | 0.050 | 0.16 | 0.46 | 0.46 |
| W Welch t, 0.05 | 0.035 | 0.12 | 0.37 | 0.38 |

S1, S2, S3, T and W are one statistic at different thresholds; their detection differences are their alpha levels. The range rule is a different statistic, but at its own false-alarm rate it loses only two points of detection. Its problem is not inefficiency.

**What changes with runs.** False alarm by k = 2, 3, 4, 5, 6, 8, 10: R 0.333, 0.100, 0.029, 0.008, 0.002, 0.000, 0.000 (closed form 2(k!)²/(2k)!, exact for any continuous noise); S1 0.33, 0.25, 0.22, 0.21, 0.20, 0.19, 0.18; T 0.05 throughout; W 0.023 to 0.049. Detection of a fixed 2 SD gap: R 0.78, 0.62, 0.49, 0.38, 0.29, 0.16, 0.09; T 0.22, 0.46, 0.66, 0.79, 0.88, 0.96, 0.99. The fall for R holds for any noise distribution: the no-overlap event for k + 1 runs is contained in the event for k runs.

**Noise.** For a true gap of 2 points and the same run-to-run SD on both sides, the chance of passing the range rule at k = 3 is 0.00, 0.02, 0.38, 0.62, 0.74, 0.83, 0.87, 0.89 at SD 0.25, 0.5, 1, 1.5, 2, 3, 5, 10 points, with limit 0.90. At the observed median SD of 1.7 points a 2-point gap passes about 68% of the time, while TOST shows equivalence within 3 points about 12% of the time. If only the port side is noisier (gap 1 original SD), the pass chance rises from 0.40 to a peak of 0.82 near three times the original SD and then falls toward 0.75.

**Discrete scores.** With scores that are pass counts over n tasks, ties count as overlap, so the false alarm at k = 3 is 0.049, 0.067, 0.072, 0.080, 0.089, 0.092 at n = 10, 30, 50, 100, 300, 1000 (base rate 0.3). A 5-point gap is 1.1 run SDs at n = 100 and 3.4 at n = 1000; R detects it 25% and 94% of the time, T 17% and 86%.

**Realistic noise.** Per-task pass probabilities from the recovered Harbor-side outcomes of 39 adapters (amendment 5: light shrinkage; implied run SD quartiles 1.5, 2.1, 2.8 points against 1.1, 1.7, 2.7 observed). Medians over adapters at k = 3: false alarm R 0.07, S1 0.25, T 0.05; detection of a 5-point loss R 0.57, T 0.47, S1 0.86; equivalence within 5 shown for a perfect port 0.45, within 3 0.08. The pre-registered Beta(1,1) prior doubles the implied SD (2.6, 3.3, 4.5) and halves detection (R 0.33); it is reported as the sensitivity.

**The bridge to RQ3.** Under perfect parity with k = 3 the smallest provable margin is 2.3 run SDs on average, about 3.9 points at the median SD, which is why the published medians sit near 4.4. Equivalence within one run SD is shown 3% of the time at k = 3 and needs 18 runs per side for 80% power; within 2 SD, 6 runs; within 3 SD, 3 runs.

**Selection check.** If all 58 published k = 3 ports were perfect and runs independent, the rules would flag R 5.8, S1 14.8, S2 21.7, S3 25.4, T 2.9 of them; observed 1, 4, 12, 18, 0 (binomial lower tails 0.017, <0.001, 0.005, 0.032, 0.052). Published parity records are post-selection: ports are debugged and rerun until the rule passes. The pass rate of the published data therefore says nothing about the rule's error rates, and the RQ1 numbers must be read as model properties.

## 4. RQ2: what the published evidence establishes

Analysable comparisons have at least 2 runs per side, a point-scale metric, and neither identical run lists nor zero spread on both sides. The headline set is the 58 comparisons with exactly 3 runs per side. Per comparison: gap (Harbor minus original), pooled-t 95% and 90% intervals, the smallest provable margin |gap| + half-width of the 90% interval, and each rule's verdict. Script `scripts/p2_rq2_evidence.py`; outputs `rq2_summary.json`, `rq2_comparisons.csv`; figure `figures/fig_rq2_margins.png`.

| Set | n | median abs gap | median run SD | smallest provable margin, quartiles | TOST within ±2 / ±3 / ±5 | Welch within ±3 / ±5 | fail overlap | S1 / S2 / S3 mismatches | overlap passes but margin > 5 |
|---|---|---|---|---|---|---|---|---|---|
| k = 3 on both sides (headline) | 58 | 0.67 | 1.71 | 2.4 / 4.4 / 6.0 | 7 / 22 / 36 | 20 / 31 | 1 | 4 / 12 / 18 | 21 |
| all comparisons with >= 2 runs per side | 75 | 0.67 | 1.79 | 2.4 / 4.4 / 6.2 | 10 / 29 / 45 | 25 / 39 | 1 | 5 / 14 / 20 | 29 |
| one comparison per adapter | 66 | 0.67 | 1.74 | 2.4 / 4.4 / 6.0 | 9 / 26 / 40 | 22 / 35 | 1 | 5 / 14 / 20 | 25 |
| k = 3, row matches the paper table | 37 | 0.58 | 1.49 | 2.2 / 3.4 / 5.8 | 5 / 17 / 26 | 15 / 23 | 1 | 3 / 9 / 10 | 10 |
| k = 3, parity on a subset | 22 | 0.67 | 2.31 | 3.2 / 5.0 / 6.9 | 2 / 5 / 11 | 5 / 8 | 0 | 1 / 5 / 7 | 11 |
| k = 3, parity on the full set | 34 | 0.60 | 1.54 | 2.3 / 3.7 / 5.8 | 5 / 16 / 23 | 14 / 21 | 1 | 3 / 6 / 10 | 10 |
| k >= 2 including identical non-constant rows | 76 | 0.67 | 1.84 | 2.4 / 4.4 / 6.4 | 10 / 29 / 45 | 25 / 39 | 1 | 5 / 14 / 20 | 30 |

In words:

- The ports look close. The median absolute gap is 0.7 points, no gap is distinguishable from zero at the 95% level, and neither t-test rejects for any of the 58.
- The evidence that they are close is thin. With three runs per side the median smallest provable margin is 4.4 points; equivalence within 3 points can be shown for 22 of 58 and within 5 points for 36. One in four comparisons cannot show equivalence even within 6 points.
- Counts at fixed margins are knife-edge: moving every margin by 0.1 points moves the within-3 count between 21 and 23 and the within-5 count between 34 and 37. The quartiles are the stable numbers.
- The overlap verdict and the equivalence question disagree. Of the 57 comparisons that pass the rule, 21 cannot show equivalence within 5 points and 35 cannot within 3. The one comparison that fails (USACO, by 0.1 points) has a smallest provable margin of 5.8 points, which 18 passes exceed.
- The rule passes the largest gaps. Frontier-CS passes with a 15.6-point gap (10 problems, run SD 16 points), RexBench with 8.3, PIXIU with 4.9, GDB with 4.6; their smallest provable margins are 44, 35, 20 and 12 points. The opening example of the paper should be USACO against Frontier-CS.
- Subsets are noisier: median run SD 2.3 points on subsets against 1.5 on full sets; median smallest provable margin 5.0 against 3.7.
- The SEM readings of the paper's wording are stricter than the rule: 4, 12 and 18 of the 58 fail S1, S2 and S3 against 1 failing range overlap. Under any of them several accepted ports would not have passed.
- Sensitivity: one comparison per adapter, including the identical-list row, or Welch intervals move the within-5 count by at most five. The 37 rows that match the paper's table have lower run SDs (median 1.5) and a median margin of 3.4.
- By run count: k = 2 (7 comparisons) shows equivalence within 5 points for 2; k = 5 (5) for 3; k = 6 (2) for 2; the 3-against-5 comparison (SWE-Lancer) within 3. The second SWE-bench Pro entry (4 runs, 10 tasks) has a smallest provable margin of 16 points.

## 5. Data-quality observations (neutral)

- Single-run comparisons (4): OSWorld (1 vs 1), ProgramBench (1 vs 1 and 1 vs 5), SWE-bench Verified (1 vs 3, declared as 3 runs).
- Identical run lists on both sides (2): compilebench (constant, by construction) and mlgym-bench Pass Rate ([83.33, 83.33, 75.0] on both sides).
- Zero spread on one side (6): devopsgym, featurebench, financeagent, gaia2, rexbench (original [33.33] x 3) and spider2-dbt. For these the pooled interval is narrower than the Welch interval (same standard error, 2k - 2 instead of k - 1 degrees of freedom); both are reported.
- Native-unit metric (1): mlgym-bench Mean Reward (573, 103, 131 against 71, 184, 207), gap 0.6 SD.
- Declared run counts differ from the run lists in 5 experiments (kumo x2, programbench, swebench, swelancer). Run lists stored as strings in 4 rows; parsed leniently.
- Reported "mean ± err" strings match the raw runs everywhere to within rounding; the ± is the SEM throughout.
- Some "original" values are published leaderboard scores, not reruns (aa-lcr, four experiments); evoeval reports an original mean ± SEM with an empty run list. Excluded by rule 2. bfcl carries two original-side variants per row; the main list was used.
- In the per-task files: crustbench's files labelled "original" reproduce the JSON's `harbor_runs` and vice versa; ARC-AGI-2's published rates are per puzzle (120) while the files hold per test pair (167); MMAU's two sides are per-task identical in every run (2,999 of 3,000 outcomes), so they are not independent evaluations; SWE-bench Pro's Harbor run 1 of 6 was run on a different 100-task sample (21 tasks in common with the original side); devopsgym's files hold a single 46-task run per experiment rather than the five published 50-task runs; humanevalfix's six runs are two experiments. All recorded in `data/pertask/MANIFEST.json`.
- The Hugging Face dataset was last modified on 2026-04-22; 11 of the 49 adapter folders with result files could not be validated against the published run lists on at least one side.
- Transitive parity (15 legs across 11 adapters) is in `comparisons_legs.csv`; five legs have one run per side.

## 6. RQ3: what would fix it and what it costs

**a. Runs needed** (`scripts/p2_rq3_runs_needed.py`, `rq3_runs_needed.json`). Runs per side for 80% TOST power, at the observed pooled-SD quartiles of the headline set (1.12, 1.71, 2.74 points), under a true gap of 0 (and of 0.6 in parentheses):

| margin | SD 1.1 (quiet quartile) | SD 1.7 (median) | SD 2.7 (noisy quartile) |
|---|---|---|---|
| ±2 points | 7 (9) | 14 (20) | 33 (49) |
| ±3 points | 4 (4) | 7 (8) | 16 (18) |
| ±5 points | 3 (3) | 3 (4) | 6 (7) |

For 90% power add about 20 to 40%. Per comparison with its own SD and a true gap of 0, the median need for ±3 is 7 runs (quartiles 4 to 13); 21% of comparisons would need 3 or fewer, 41% 5 or fewer; for ±5 half need 3 or fewer. For 4 comparisons the observed gap already exceeds 3 points, so no run count would show equivalence within 3. The first pass's "14, 6, 3 runs" were plug-in values with about 45% power.

**b. Paired per-task analysis** (`scripts/p2_rq3_paired.py`, `rq3_paired.json`, `rq3_paired.csv`). Per-task outcomes were recovered from the Hugging Face files by one parser per adapter (`scripts/pertask/`), validated against the published run scores, and recorded in `data/pertask/MANIFEST.json`. Of 49 adapter folders, 44 have both sides; 32 pass the inclusion rule (replicate runs of one experiment, at least 20 common tasks, both sides reproducing the published scores, or documented exceptions). For each, tasks were aligned by id and the per-task difference averaged, with a 10,000-resample task-level bootstrap.

- The paired interval is not tighter. Smallest provable margin quartiles are 3.2, 4.5, 5.7 points paired against 2.2, 3.2, 5.9 run-level on the same files; the run-level interval is the narrower one for 17 of 31 adapters (width ratio quartiles 0.49, 0.71, 1.33). Paired: 7 of 32 within ±3 and 21 within ±5; run-level: 15 and 21.
- The paired view shows what the aggregate hides: 23 to 41% of common tasks (quartiles) have different pass rates on the two sides, and no paired gap is distinguishable from zero. The run-level interval from three runs is also simply unreliable (its width depends on a standard deviation estimated from three numbers). What the paper can say: pairing by task is the honest interval and the only one that exposes task-level disagreement; it does not buy precision for free. (The statistics review on this point is in section 11.)

**c. Injected defects** (`scripts/p2_rq3_defects.py`, `rq3_defects.json`, `figures/fig_rq3_defects.png`). Thirty-nine adapters with validated Harbor-side per-task outcomes; both sides simulated from the same per-task probabilities; a defect breaks (or leaks) a fraction f of tasks on the port side; 2,000 replications; mean over adapters. Detection rates (verdict = mismatch) at k = 3, with the expected gap in points:

| defect | gap | R overlap | S1 SEM bars | T pooled t | paired t | TOST ±3 shown | TOST ±5 shown |
|---|---|---|---|---|---|---|---|
| none | 0 | 0.07 | 0.25 | 0.05 | 0.05 | 0.21 | 0.49 |
| break 2% | -1.1 | 0.14 | 0.36 | 0.10 | 0.10 | 0.16 | 0.45 |
| break 5% | -2.6 | 0.34 | 0.58 | 0.29 | 0.26 | 0.05 | 0.29 |
| break 10% | -5.4 | 0.61 | 0.80 | 0.56 | 0.52 | 0.01 | 0.08 |
| break 20% | -10.9 | 0.85 | 0.93 | 0.83 | 0.80 | 0.00 | 0.02 |
| leak 10% | +4.6 | 0.58 | 0.78 | 0.52 | 0.48 | 0.03 | 0.15 |

With five runs: break 10% is caught by R 0.47, T 0.72, paired 0.59; with ten runs R 0.33, T 0.85, paired 0.66; and a perfect port shows equivalence within 5 points 0.71 (k = 5) and 0.92 (k = 10) of the time. Reading: at three runs no test reliably catches a defect that costs 5 points; the overlap rule's apparent edge at k = 3 is its 7% false alarm, and it is the only rule that gets worse with more runs. The paired t is slightly weaker than the pooled t for these sparse defects because the defect itself inflates the task-level spread of the differences (review pending on the better paired statistic for sparse defects).

**d. Verdict script.** `scripts/parity_verdict.py <parity_experiment.json> [--margin m]` prints, per metric row, the overlap verdict and separation, the gap with its 95% interval, the smallest provable margin, and the runs per side needed for 80% power at that row's own noise. USACO: ranges do not overlap by 0.1; gap +2.6 [-1.4, +6.7]; margin 5.8; 7 runs for ±3. RexBench: overlaps by 16.7; gap +8.3 [-27, +44]; margin 35; 464 runs for ±3.

## 7. Recommended protocol

1. State the margin before running: how many points of difference would make the port a different benchmark (for most scores, 3 to 5 points; tighter for benchmarks near a decision threshold).
2. Choose the run count from the noise, not by convention: enough runs per side for 80% TOST power at the margin given the port's run-to-run SD (table 6a; roughly 7 per side at the median noise for ±3, 3 to 4 for ±5), and never fewer than 5 when the SD is unknown.
3. Report the gap with its 90% interval and the smallest provable margin; declare "equivalent within ±m" only when the interval lies inside ±m; otherwise "not yet shown", which is a request for runs, not a verdict of mismatch.
4. Publish per-task outcomes on both sides with aligned task ids; report the share of tasks whose pass rates differ and a paired interval; investigate tasks that differ in every run.
5. Keep range overlap as a sanity check at most; keep single-run and leaderboard-number comparisons out of parity tables.

## 8. Threats to validity

- Noise model: run scores treated as independent draws with a common variance; checked with binomial and per-task models, which agree on the ordering of rules. Run-level common shocks (infrastructure noise) are not modelled.
- Selection: the published ports are post-selection, so their pass rates cannot validate any rule, and the RQ1 rates are model properties.
- Three runs give a noisy SD; the pooled estimate across comparisons is reported, and the per-task analysis provides a second noise estimate.
- The metric rule and its five amendments; the sensitivity rows show that the headline is insensitive to them (within-5 count 34 to 37 under every variant tried).
- Mixed metric types (rates, F1, rewards) on one point scale; native-unit rows excluded.
- Subsets versus full sets: subsets are noisier; reported separately.
- One snapshot (2026-10-10); the Hugging Face dataset lags the repo by months; 11 adapter folders could not be fully validated.
- No benchmark was rerun. Per-task data on the original side come in heterogeneous formats parsed by one script each; validation against the published run scores is the only check.
- The per-task noise model's prior changes detection rates by up to a factor of two; both priors are reported.
- Counts at fixed margins are knife-edge; the quartiles are the stable summary.

## 9. Two-minute summary and three reviewer questions

Harbor checks each ported benchmark with three runs per side and calls it a match when the run ranges overlap. We derived what that rule guarantees and found it is not an equivalence test: it flags perfect ports 10% of the time, detects a two-SD gap 62% of the time, gets more lenient with every added run and with every point of noise, and its false-alarm rate cannot be chosen. We then re-analysed the 58 published comparisons with three runs: the ports look close, with a median gap of 0.7 points, but the data can show equivalence within 3 points for only 22 of them and within 5 for 36, and the rule passes gaps of 15.6 and 8.3 points. We recovered per-task outcomes for 32 adapters and found that 23 to 41% of tasks have different pass rates on the two sides, which the aggregate hides. Fixing this costs runs, about seven per side for a 3-point margin at the observed noise, and a stated margin; the protocol is five lines and a script.

1. "Overlap tests are known to be miscalibrated; what is new?" The specific rule that gated about 90 ports, its exact error rates and k-dependence, the corpus audit showing what the published runs can establish, the defect-detection curves on real per-task data, and the cost of the fix.
2. "Your false-alarm rates do not match the published failure rate." Correct, and that is the selection effect: ports are revised until the rule passes, so published pass rates cannot validate the rule; our rates are properties of the rule under stated noise models, which we check three ways.
3. "Is the paired analysis worth the trouble if it is not tighter?" It is the only view that exposes task-level disagreement, and it does not depend on an SD estimated from three numbers; we say plainly that it does not buy precision.

## 10. Files

See `results/phase2/NUMBERS_phase2.md` for the number-to-script map and section 2 of `README.md` for the layout.

## 11. What the independent reviews changed

PENDING_REVIEWS
