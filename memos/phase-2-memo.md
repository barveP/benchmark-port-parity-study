# Memo: Phase 2, the analysis

Date: 2026-10-11. Rules were fixed in `memos/phase-2-preregistration.md` before any outcome was computed; six amendments are recorded there with their reasons and timing. The rules were fixed before the Phase 2 scripts were run; amendment 5 was made before the final RQ3 run, and amendment 6 after the first RQ3 outputs had been reviewed. Every number below comes from a script in `scripts/` and an output file in `results/phase2/`; the map is in `results/phase2/NUMBERS_phase2.md`.

## 1. Bottom line

- **What the rule guarantees (RQ1).** With three runs per side, Harbor's range-overlap rule flags a perfect port 10% of the time for continuous scores (4 to 9% when pass counts can tie), and catches a gap of two run-to-run SDs 62% of the time. At its own false-alarm rate it is nearly as good as a t-test (64%). Its defects are structural: its false-alarm rate is set by the run count alone (33%, 10%, 2.9%, 0.8% at 2, 3, 4, 5 runs); for any fixed gap its detection falls as runs are added (78% at k = 2, 9% at k = 10, while a t-test rises from 22% to 99%); it passes more easily the noisier the runs; and a pass means only "not rejected at the 10% level", never equivalence. The paper's own wording ("within standard errors") is stricter, not laxer: 25 to 44% false alarms depending on the reading.
- **What the published evidence establishes (RQ2).** The 58 comparisons with three runs per side look close: median gap 0.7 points, no gap distinguishable from zero. But with three runs the median smallest provable margin is 4.4 points; equivalence within 3 points can be shown for 22 of 58 and within 5 points for 36. Twenty-one comparisons pass the overlap rule yet cannot show equivalence within 5 points, and the rule passes the four largest gaps (15.6, 8.3, 4.9 and 4.6 points). The published data also show far fewer rule failures than a perfect-parity model predicts (1 against 5.8 expected), which is what one expects when ports are revised until the rule passes: pass rates cannot validate the rule.
- **What would fix it (RQ3).** Showing equivalence within 3 points at 80% power needs about 7 runs per side at the median noise (4 at the quietest quartile, 16 at the noisiest); within 5 points, 3 to 6. Pairing the sides task by task is not a precision gain: on the same files the paired interval is wider than the run-level one for 15 of 26 adapters, where under shared noise it would be about a sixth narrower, because it absorbs task-level disagreement that the run scores cannot see. That disagreement exceeds what shared per-task pass probabilities produce in 14 of 27 adapters, while a within-task permutation test rejects the mean gap for none of them; the data cannot say whether it comes from the port. Nearly a third of the Harbor-side run totals (9 of 30) are also under-dispersed relative to their own per-task flip rates, an open data-quality question. Injecting defects into real per-task outcomes shows that with three runs none of the evaluated 5% tests catches the simulated 10% break defect more than about two thirds of the time; the best calibrated paired statistic is a stratified-by-task test (67%, added after the first RQ3 run, amendment 6c), not the paired t (54%); and a perfect port can be shown equivalent within 5 points only half the time (51%). All of these improve with runs; the overlap rule gets worse.

## 2. The comparison table (pre-registered rule)

The 121 experiments give 82 comparisons between the original harness and the Harbor port, plus 15 transitive legs through the Terminal-Bench adapter kept as a secondary set. The 39 experiments without a comparison are Harbor-only runs, rows whose "original" value is a published leaderboard number with no run list (aa-lcr), reported means with empty run lists (evoeval), or transitive entries. The main metric came from the paper's Tables 3 and 4 in 48 cases plus Frontier-CS whose aggregated per-problem rows match the table, from per-group aggregation in 1 (Multi-SWE-bench, seven languages of ten tasks), from a headline name in 29, and from "first remaining row" in 3. Run counts: 61 comparisons have 3 runs per side, 7 have 2, 5 have 5, 2 have 4, 2 have 6, 1 has 3 against 5, and 4 have a single run on at least one side. Script `scripts/p2_build_comparisons.py`; outputs `comparisons.csv`, `comparisons_legs.csv`, `selection_log.json`.

## 3. RQ1: what the rule guarantees

Script `scripts/p2_rq1_rules.py`; output `rq1_rules.json`; figure `figures/fig_rq1_rules.png`. Rules: R range overlap; S1 mean ± SEM bars overlap; S2 gap within the standard error of the difference; S3 gap within one side's SEM (the literal reading of D.7); T pooled t-test at 0.05; W Welch t-test at 0.05; E(m) TOST equivalence within ±m. All rates are properties of the rule under a stated noise model, not of the published ports (see the selection check below).

**Normal noise, three runs per side.** Rows: false alarm (perfect port flagged), detection of a 1 SD and a 2 SD gap, and the detection of the pooled t-statistic tuned to the same false alarm.

| rule | false alarm | detects 1 SD | detects 2 SD | t at same false alarm, 2 SD |
|---|---|---|---|---|
| R range overlap | 0.099 (closed form 0.100) | 0.26 | 0.62 | 0.64 |
| S1 SEM bars overlap | 0.254 | 0.50 | 0.86 | 0.86 |
| S2 within SE of difference | 0.374 | 0.63 | 0.92 | 0.92 |
| S3 within one SEM | 0.439 | 0.68 | 0.94 | 0.94 |
| T pooled t, 0.05 | 0.050 | 0.16 | 0.46 | 0.46 |
| W Welch t, 0.05 | 0.035 | 0.12 | 0.37 | 0.38 |

S1, S2, T and W are one statistic at different thresholds (S3 approximately so); their detection differences are their alpha levels. The range rule is a different statistic, but at its own false-alarm rate it loses only two points of detection. Its problem is not inefficiency.

**What changes with runs.** False alarm by k = 2, 3, 4, 5, 6, 8, 10: R 0.333, 0.100, 0.029, 0.008, 0.002, 0.000, 0.000 (closed form 2(k!)²/(2k)!, exact for any continuous noise); S1 0.33, 0.25, 0.22, 0.21, 0.20, 0.19, 0.18; T 0.05 throughout; W 0.023 to 0.049. Detection of a fixed 2 SD gap: R 0.78, 0.62, 0.49, 0.38, 0.29, 0.16, 0.09; T 0.22, 0.46, 0.66, 0.79, 0.88, 0.96, 0.99. The fall for R holds for any noise distribution: the no-overlap event for k + 1 runs is contained in the event for k runs.

**Noise.** For a true gap of 2 points and the same run-to-run SD on both sides, the chance of passing the range rule at k = 3 is 0.00, 0.02, 0.38, 0.62, 0.68, 0.74, 0.82, 0.87, 0.89 at SD 0.25, 0.5, 1, 1.5, 1.7, 2, 3, 5, 10 points, with limit 0.90. At the observed median SD of 1.7 points a 2-point gap passes 68% of the time, while TOST shows equivalence within 3 points 12% of the time. If only the port side is noisier (gap 1 original SD), the pass chance rises from 0.40 (port SD zero, closed form) to a peak of 0.82 at three to four times the original SD and then falls toward 0.75 (0.76 at 100 times).

**Discrete scores.** With scores that are pass counts over n tasks, ties count as overlap, so the false alarm at k = 3 is 0.049, 0.067, 0.072, 0.080, 0.089, 0.092 at n = 10, 30, 50, 100, 300, 1000 (base rate 0.3). A 5-point gap is 1.1 run SDs at n = 100 and 3.4 at n = 1000; R detects it 25% and 94% of the time, T 17% and 86%.

**Realistic noise.** Per-task pass probabilities from the recovered Harbor-side outcomes of the 30 adapters with binary outcomes and validated replicate runs (amendments 5 and 6: light shrinkage; model run SD quartiles 1.7, 2.2, 3.1 points, against 1.1, 1.7, 2.7 observed in the headline set, whose runs are often under-dispersed, see section 6). Medians over adapters at k = 3: false alarm R 0.07 (ties count as overlap), S1 0.25, T 0.05; detection of a 5-point loss R 0.58, T 0.47, S1 0.87; equivalence within 5 points shown for a perfect port 0.50, within 3 points 0.10. The pre-registered Beta(1,1) prior inflates the model SD (2.9, 3.8, 5.0) and cuts detection of the 5-point loss to R 0.32; it is reported as the sensitivity.

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
- Sensitivity: one comparison per adapter leaves the within-5 share unchanged (40 of 66, 61%, against 36 of 58, 62%); including the identical-list row changes nothing; Welch intervals lower the headline within-5 count from 36 to 31. The 37 rows that match the paper's table have lower run SDs (median 1.5) and a median margin of 3.4. MMAU is among the 58 although its two sides are per-task identical (section 5); without it the within-3 and within-5 counts each drop by one.
- By run count: k = 2 (7 comparisons) shows equivalence within 5 points for 2; k = 5 (5) for 3; k = 6 (2) for 2; the 3-against-5 comparison (SWE-Lancer) within 3. The second SWE-bench Pro entry (4 runs, 10 tasks) has a smallest provable margin of 16 points.

## 5. Data-quality observations (neutral)

- Single-run comparisons (4): OSWorld (1 vs 1), ProgramBench (1 vs 1 and 1 vs 5), SWE-bench Verified (1 vs 3, declared as 3 runs).
- Identical run lists on both sides (2): compilebench (constant, by construction) and mlgym-bench Pass Rate ([83.33, 83.33, 75.0] on both sides).
- Zero spread on one side (6): devopsgym, featurebench, financeagent, gaia2, rexbench (original [33.33] x 3) and spider2-dbt. For these the pooled interval is narrower than the Welch interval (same standard error, 2k - 2 instead of k - 1 degrees of freedom); both are reported.
- Native-unit metric (1): mlgym-bench Mean Reward (573, 103, 131 against 71, 184, 207), gap 0.6 SD.
- Declared run counts differ from the run lists in 5 experiments (kumo x2, programbench, swebench, swelancer). Run lists stored as strings in 4 rows; parsed leniently.
- Reported "mean ± err" strings match the raw runs to within rounding except two locomo rows off by 0.001; the ± is the SEM wherever it can be classified (411 sides; 109 ambiguous at the printed precision; 1 matches neither).
- Some "original" values are published leaderboard scores, not reruns (aa-lcr, four experiments); evoeval reports an original mean ± SEM with an empty run list. Excluded by rule 2. bfcl carries two original-side variants per row; the main list was used.
- In the per-task files: crustbench's files labelled "original" reproduce the JSON's `harbor_runs` and vice versa; ARC-AGI-2's published rates are per puzzle (120) while the files hold per test pair (167); MMAU's two sides are per-task identical in every run (2,999 of 3,000 outcomes), so they are not independent evaluations; SWE-bench Pro's Harbor run 1 of 6 was run on a different 100-task sample (21 tasks in common with the original side); devopsgym's files hold a single 46-task run per experiment rather than the five published 50-task runs; humanevalfix's six runs are two experiments. All recorded in `data/pertask/MANIFEST.json`.
- On nearly a third of the Harbor sides with per-task files (9 of 30 binary adapters), the published run totals vary less across runs than the within-task flip rates imply under independent outcomes (dispersion ratio below 0.1: adebench, bird_bench, financeagent, ineqmath, kumo, labbench, ml_dev_bench, quixbugs, satbench; quartiles 0.10, 0.52, 1.26). financeagent, for example, reports 40 of 50 passes in each of three runs while its tasks flip between runs. The published run lists confirm it. Either outcomes within a run are negatively dependent across tasks or the runs are not independent replicates; the paper reports it as an open question.
- The Hugging Face dataset was last modified on 2026-04-22; of the 44 two-sided adapter folders, 10 fail validation against the published run lists on at least one side (arc_agi_2, codepde, crustbench, devopsgym, featurebench, financeagent, humanevalfix, llmsr_bench, qcircuitbench, swegym) and 13 are excluded from the paired analysis (section 6b).
- Transitive parity (15 legs across 8 adapters) is in `comparisons_legs.csv`; five legs have one run per side.

## 6. RQ3: what would fix it and what it costs

**a. Runs needed** (`scripts/p2_rq3_runs_needed.py`, `rq3_runs_needed.json`). Runs per side for 80% TOST power, at the observed pooled-SD quartiles of the headline set (1.12, 1.71, 2.74 points), under a true gap of 0 (and of 0.6 in parentheses):

| margin | SD 1.1 (quiet quartile) | SD 1.7 (median) | SD 2.7 (noisy quartile) |
|---|---|---|---|
| ±2 points | 7 (9) | 14 (20) | 33 (49) |
| ±3 points | 4 (4) | 7 (8) | 16 (18) |
| ±5 points | 3 (3) | 3 (4) | 6 (7) |

For 90% power the need rises by up to about a third (0 to 37% across the table). Per comparison with its own SD and a true gap of 0, the median need for ±3 is 7 runs (quartiles 4 to 16); 21% of the 58 would need 3 or fewer, 40% 5 or fewer, 62% 10 or fewer, and 2 (RexBench, Frontier-CS) more than 400; for ±5 half need 3 or fewer. For 4 comparisons the observed gap already exceeds 3 points. The first pass's "14, 6, 3 runs" were plug-in values; the plug-in rule's actual power ranges from 12 to 78% across this table.

**b. Paired per-task analysis** (`scripts/p2_rq3_paired.py`, `rq3_paired.json`, `rq3_paired.csv`). Per-task outcomes were recovered from the Hugging Face files by one parser per adapter (`scripts/pertask/`), validated against the published run scores, and recorded in `data/pertask/MANIFEST.json`. Of 49 adapter folders, 44 have both sides; 27 form the primary paired set (replicate runs of one experiment, at least 20 common tasks, both sides reproducing the published scores, or a documented exception), 4 whose "original" files are Terminal-Bench adapter runs form a secondary set, and the rest are excluded with a reason in the manifest. For each adapter, tasks were aligned by id, the per-task difference averaged, and a 10,000-resample task-level bootstrap taken; a within-task permutation test (2,000 permutations) supplies the null in which both sides share each task's pass probability.

- Precision: paired smallest provable margins have quartiles 3.0, 4.5, 5.7 points; run-level margins from the same files 2.2, 2.9, 5.9. The run/paired width ratio has quartiles 0.49, 0.67, 1.27, and is below 1 for 15 of 26 adapters. Under shared noise its expected median is 1.2, because the run-level interval pays 4 degrees of freedom while the paired one has hundreds; 15 of 26 observed ratios fall below the 25th percentile of their own permutation null. Paired: 7 of 27 within ±3 and 16 within ±5; run-level (26 with an interval): 14 and 17.
- What the extra width is. The task-level spread of side differences exceeds the shared-noise null (p < 0.05) in 14 of 27 adapters (10 at p < 0.01: bfcl, crustbench, dacode, ds1000, kumo, ml_dev_bench, multi-swe-bench, pixiu, spider2-dbt, widesearch; swebenchpro at 0.013), and is consistent with it in the other 13. Several adapters have tasks that pass in every run on one side and fail in every run on the other (ds1000 13, crustbench 6, dacode 6, kumo 6, bfcl 5, multi-swe-bench 5; SWE-bench Verified 36, with one original run; deveval 6 in the secondary set). The mean gap is exchangeable in all 27 (permutation p > 0.05 everywhere; the stratified test rejects for 0 of 21 binary adapters; no bootstrap interval excludes zero). The share of tasks with different pass rates (quartiles 25, 37, 41%) is uninformative on its own: two independent sides with shared probabilities also disagree on a large share of tasks.
- A second cause of narrow run-level intervals: under-dispersed run totals (section 5). Where either side's dispersion ratio is below 0.1 (adebench, deepsynth, kumo, labbench, ml_dev_bench, spider2-dbt, theagentcompany), the run-level interval is narrow for a reason the per-task data do not support.
- What the paper may say: the ports agree on the mean score everywhere, and disagree task by task in about half of the adapters; the run-level interval is the right interval for the fixed-task-set gap and the only one that would absorb run-level shocks (which cannot be assessed from these files: the real runs are under-dispersed, with dispersion-ratio medians of 0.36 on the Harbor side and 0.50 on the original side); the paired interval answers whether the port would agree on new tasks like these and is the only view that exposes task-level disagreement. It may not call the task-level differences systematic or defects: one pair of sides cannot separate a port effect from side-specific stickiness (seeds, environments, caching).
- Secondary set (4 Terminal-Bench legs): paired margins 3.4, 4.3, 6.1; run-level 3.6, 4.5, 5.5.

**c. Injected defects** (`scripts/p2_rq3_defects.py`, `rq3_defects.json`, `figures/fig_rq3_defects.png`). Primary: 30 adapters with binary outcomes and validated replicate Harbor runs (model run SD quartiles 1.7, 2.2, 3.1 points); both sides simulated from the same per-task probabilities; a defect breaks (or leaks) a fraction f of tasks on the port side; 2,000 replications; mean and (median) over adapters. Rules: R range overlap, S1 SEM bars, T pooled t, P paired t on task means, CMH stratified-by-task test (added after the first RQ3 run, amendment 6c), E5 TOST within 5 shown.

| defect | gap, points | R | S1 | T | P | CMH | E5 shown |
|---|---|---|---|---|---|---|---|
| none (k = 3) | 0 | 0.07 (0.07) | 0.24 | 0.05 | 0.05 | 0.05 | 0.51 (0.50) |
| break 2% | -1.1 | 0.15 (0.10) | 0.38 | 0.11 (0.07) | 0.10 (0.06) | 0.14 (0.09) | 0.47 |
| break 5% | -2.7 | 0.37 (0.23) | 0.61 | 0.32 (0.18) | 0.29 (0.15) | 0.39 (0.26) | 0.29 |
| break 10% | -5.4 | 0.64 (0.68) | 0.82 | 0.59 (0.58) | 0.54 (0.48) | 0.67 (0.74) | 0.07 |
| break 20% | -11.0 | 0.87 (0.99) | 0.95 | 0.85 (0.98) | 0.82 (0.97) | 0.90 (1.00) | 0.02 |
| leak 10% | +4.5 | 0.58 (0.64) | 0.77 | 0.51 (0.55) | 0.48 (0.47) | 0.61 (0.70) | 0.18 |
| break 10%, k = 5 | -5.4 | 0.51 (0.48) | 0.87 | 0.75 (0.87) | 0.60 (0.60) | 0.77 (0.91) | 0.12 |
| break 10%, k = 10 | -5.4 | 0.36 (0.19) | 0.92 | 0.86 (0.98) | 0.67 (0.78) | 0.86 (0.99) | 0.19 |
| none, k = 10 | 0 | 0.00 | 0.18 | 0.05 | 0.05 | 0.05 | 0.94 (1.00) |

Reading: with three runs, a defect that costs 5 points is caught about six times in ten by any calibrated test; the overlap rule's edge at k = 3 is its 7% false alarm, and it is the only rule that gets worse with more runs. The paired t is the wrong paired statistic for a sparse defect: its standard error includes the between-task spread of the defect itself, which does not shrink with runs, so it trails the pooled t (P at or below T for 24 of 30 adapters, strictly below for 22) and falls further behind at k = 10. The stratified-by-task test (McNemar at one run) has none of that cost and is the best calibrated test at three and five runs. A perfect port shows equivalence within 5 points 51% of the time at k = 3 (median over adapters 50%), 75% (87%) at k = 5, 94% (100%) at k = 10. Sensitivities: the 21 well-dispersed adapters give the same picture (R 0.64, T 0.59, CMH 0.67 at break 10%); the Beta(1,1) prior lowers every rate (R 0.43, T 0.34, CMH 0.45); the 8 fractional-score adapters, simulated by resampling their observed rewards, give R 0.72, T 0.67, P 0.59. The nominal 2% cell breaks one task for the small adapters (1.4 to 3.0%). Because the real Harbor runs are under-dispersed in nearly a third of adapters, run-level detection and E5 are, if anything, understated for those.

**d. Verdict script.** `scripts/parity_verdict.py <parity_experiment.json> [--margin m]` prints, per metric row, the overlap verdict and separation, the gap with its 95% interval, the smallest provable margin, and the runs per side needed for 80% power at that row's own noise. USACO: ranges do not overlap by 0.1; gap +2.6 [-1.4, +6.7]; margin 5.8; 7 runs for ±3. RexBench: overlaps by 16.7; gap +8.3 [-27, +44]; margin 35; 464 runs for ±3.

## 7. Recommended protocol

1. State the margin before running: how many points of difference would make the port a different benchmark (3 and 5 points are illustrative; justify the margin for the benchmark).
2. Choose the run count from the noise, not by convention: enough runs per side for 80% TOST power at the margin given the port's run-to-run SD (table 6a; roughly 7 per side at the median noise for ±3, 3 to 4 for ±5), and never fewer than 5 when the SD is unknown.
3. Report the gap with its 90% interval and the smallest provable margin; declare "equivalent within ±m" only when the interval lies inside ±m; otherwise "not yet shown", which is a request for runs, not a verdict of mismatch.
4. Publish per-task outcomes on both sides with aligned task ids; report a stratified-by-task test and the task-level bootstrap interval; investigate tasks that differ in every run.
5. Keep range overlap as a sanity check at most; keep single-run and leaderboard-number comparisons out of parity tables.

## 8. Threats to validity

- Noise model: run scores treated as independent draws with a common variance; checked with binomial and per-task models, which agree on the ordering of rules. Run-level common shocks (infrastructure noise) are not modelled.
- Selection: the published ports are post-selection, so their pass rates cannot validate any rule, and the RQ1 rates are model properties.
- Three runs give a noisy SD; the pooled estimate across comparisons is reported, and the per-task analysis provides a second noise estimate.
- The metric rule and its six amendments; the three that touch the rule (1, 2, 4) leave the headline within-5 count at 36 before and after, a 0.1-point perturbation of every margin moves it between 34 and 37, and Welch intervals lower it to 31.
- Mixed metric types (rates, F1, rewards) on one point scale; native-unit rows excluded.
- Subsets versus full sets: subsets are noisier; reported separately.
- One snapshot (2026-10-10); the Hugging Face dataset lags the repo by months; 11 adapter folders could not be fully validated.
- No benchmark was rerun. Per-task data on the original side come in heterogeneous formats parsed by one script each; validation against the published run scores is the only check.
- The per-task noise model's prior changes detection rates by up to a factor of two; both priors are reported. The model assumes independent outcomes across tasks within a run; the real runs are under-dispersed in nearly a third of adapters, so run-level rates are understated there.
- The paired analysis rests on 27 adapters (21 with both sides reproducing the published scores, 6 documented exceptions); 13 of the 44 two-sided folders are excluded, and four more are Terminal-Bench legs reported separately. Side labels, aggregation units and run samples had to be checked file by file.
- Counts at fixed margins are knife-edge; the quartiles are the stable summary.

## 9. Summary

Harbor checks each ported benchmark with three runs per side and calls it a match when the run ranges overlap. We derived what that rule guarantees and found it is not an equivalence test: under exchangeable continuous scores it flags perfect ports 10% of the time at three runs per side, detects a two-SD gap 62% of the time, gets more lenient with every added run and with every point of noise, and its false-alarm rate cannot be chosen. We then re-analysed the 58 published comparisons with three runs: the ports look close, with a median gap of 0.7 points, but the data can show equivalence within 3 points for only 22 of them and within 5 for 36, and the rule passes gaps of 15.6 and 8.3 points. We recovered per-task outcomes for 27 adapters and found that in half of them the two sides disagree task by task beyond what shared per-task pass probabilities produce, while agreeing on the mean, which the aggregate hides; and that with three runs none of the evaluated 5% tests catches the simulated 10% break defect more than about two times in three. Fixing this costs runs, about seven per side for a 3-point margin at the observed noise, and a stated margin; the protocol has five steps and a script.

## 10. Files

See `results/phase2/NUMBERS_phase2.md` for the number-to-script map and the "Repository layout" section of `README.md`.

## 11. Analysis amendments

Amendment 4 corrected fraction scaling, table aliases and per-group aggregation. The RQ1 comparison records that S2 and the pooled t-test use one statistic at different thresholds, so detection is now reported next to the t-statistic at matched false alarm, the pooled t was added as the reference test (Welch is conservative at k <= 5), and the literal "within one SEM" reading and the selection check were added. The RQ3 amendments record that the Beta(1,1) prior doubled the model noise (amendment 5), that eight fractional-score adapters were being modelled as coin flips (amendment 6b), that ARC-AGI-2 and SWE-bench Pro's off-sample run violated the inclusion rule (6a), that the "paired is wider" ratio compares two targets and has a null expectation of 1.2 (6d), that the paired t is the wrong paired statistic for sparse defects and a stratified test is the right one (6c), and that nearly a third of the Harbor-side run totals are under-dispersed, which is now reported as a data-quality finding.
