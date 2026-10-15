# Phase 2 pre-registration: rules fixed before computing outcomes

Date: 2026-10-11, before any Phase 2 script was run. This is an analysis plan committed to the repository (commit 6bcb9ba), not a registration with an outside registry. Data: the pinned snapshot in `data/raw/` (Harbor commit dc933be7, 2026-10-10) and per-task result files from the Hugging Face dataset `harborframework/parity-experiments`. The first pass's numbers (NUMBERS.md) were known when this was written; the rules below were chosen on principle, and each rule's effect is reported as a sensitivity analysis so a reader can see what it changed.

## 1. Unit of analysis

A comparison is one experiment (one adapter file entry, which is one agent and model pair) and its main metric, comparing the original side with the Harbor side. Experiments whose only comparison is transitive through the Terminal-Bench adapter (`tb_adapter_*` fields) form a secondary set where each leg is its own comparison; they are excluded from the headline numbers and reported in one sensitivity row.

## 2. Candidate metric rows

A row is a candidate when both sides have a run list after lenient parsing (numbers, or strings like "58.3%" or "58.7"). Key precedence on each side: `<side>_runs`, then `<side>_trials`. An empty or null list is no run list; a reported "mean ± err" string alone never counts (this excludes rows whose "original" value is a published leaderboard number, such as aa-lcr). Rows with `original_llm_runs` or `original_json_runs` are variants of the original side; they are listed as data-quality notes and not analysed.

## 3. Side quantities excluded by name

A metric is a side quantity, not a score, when its lower-cased name, split into tokens on non-alphanumeric characters, contains any of: `stderr`, `std`, `sem`, `missing`, `cost`, `token`, `tokens`, `time`, `latency`, `count`, `counts`, `ids`. The script prints every excluded name so the list can be audited.

Amendment 1 (2026-10-11, after the first run of the selection script and before any statistic was computed): the rule was first written as a substring match, which wrongly excluded "success rate (pass@1, no-result counted as 0)" and "Mean Semantic Score". Changed to whole-token matching.

## 4. Main-metric choice, in order

1. If the adapter appears in Tables 3 or 4 of the Harbor paper (`data/paper/tables_3_4.csv`) and a candidate row's reported means on both sides equal the table's entries within rounding, in either unit, that row is the main metric.
2. Otherwise the first candidate row, in file order, whose name matches a headline pattern: a whole word among resolve, resolved, pass, passed, success, solve, solving, accuracy, acc, score, reward, f1.
3. Otherwise the first remaining candidate row.
The chosen branch is recorded for every comparison.

Amendment 2 (2026-10-11, same day as amendment 1, before any statistic was computed): (a) the headline pattern is matched on whole tokens, like the side-quantity rule, so "macro_reward" and "success_rate" count; (b) when step 1 fails and an experiment holds five or more rows with the same metric name, one per task, with equal run counts, the rows are per-task scores and are aggregated by run index into one comparison (run i of the experiment is the mean over rows of run i); this applies to Frontier-CS, whose paper-table entry is such a mean. (c) A reported string with a trailing note in parentheses, such as "58.00% +/- 0.88% (stderr across 3 runs)", is parsed by dropping the note.

## 5. Units and scales

Scores are analysed in points (0 to 100). A row is a fraction when every value on both sides lies in [0, 1] and the reported strings carry no `%`; fractions are multiplied by 100. Rows with any value below 0 or above 100 after this step (for example BART scores, NMSE, RMSE, speedup ratios, unbounded rewards) form the native-unit set: they are kept with their gap expressed in units of the pooled run-to-run SD only, and are excluded from point-margin summaries.

Amendment 4 (2026-10-11, after two blind re-derivations and a code review of the selection script, before the RQ3 results were computed; the RQ2 headline numbers computed before this amendment are kept in `results/phase2/rq2_summary_before_amendment4.json` for comparison):
- (a) Units: a row is a fraction when every value on both sides lies in [0, 1], regardless of a % sign in the reported string. The % clause wrongly kept featurebench's trials [0.133, 0.133] in fraction units.
- (b) Rule 2b applies to per-group rows of equal size (per problem for Frontier-CS, per language of 10 tasks for Multi-SWE-bench); rows named "overall" or after the adapter are not groups; the aggregated means are then checked against the paper table (step 1) and the branch is recorded as "paper table (aggregated)" when they match.
- (c) Two table aliases were wrong (Omni-Math, SpreadsheetBench) so step 1 was silently skipped for them; corrected, and table rows that match no adapter file are now logged.
- (d) Clarifications: among several table-matching rows the headline-named row wins, then file order; a run list with any unparseable entry counts as no list; S2 uses the unpooled standard error sqrt(SEM_a^2 + SEM_b^2), which equals the pooled one when k is equal; "strict" overlap in section 7 means the floating-point tolerance set to zero (ties still overlap), named `R_overlap_eps0`; transitive legs pass the side-quantity rule and record both run counts.
- (e) RQ1 adds the pooled t-test at 0.05 (T) as the reference difference test next to Welch (W, which is conservative at small k), adds S3 = |gap| <= max(SEM_a, SEM_b) as the literal reading of D.7's "within sample SEM", and reports each rule's detection next to the detection of the t-statistic at the same false-alarm rate, because S1, S2, T and W are one statistic at different thresholds.

## 6. Run counts

The headline analysis uses comparisons with exactly 3 runs per side, for comparability with the first pass and because 68 of 121 experiments declare 3 runs. The full analysis uses every comparison with at least 2 runs per side and reports results by k. Comparisons with 1 run on a side get a gap and no interval, and are listed.

## 7. Degenerate rows

Identical run lists on both sides, and rows with zero spread on both sides, are excluded from inferential summaries and listed. Zero spread on one side is kept and flagged; Welch intervals are reported for them as a sensitivity check. Range overlap is computed with a tie tolerance of 1e-9 (strict overlap is also reported).

## 8. Statistics

- Run-level model: each side's k run scores are treated as independent draws of a run-level score with a common variance across sides (pooled t, k1 + k2 - 2 degrees of freedom). Welch intervals are the stated sensitivity check.
- Gap = Harbor mean minus original mean, in points; the absolute gap is used for summaries.
- 95% interval for the gap (pooled t); 90% interval = the TOST interval at alpha 0.05.
- Smallest provable margin = |gap| + half-width of the 90% interval. Equivalence within ±m is shown iff this is at most m. Margins reported: 1, 2, 3, 5, 10 points.
- A gap is distinguishable from zero iff the 95% interval excludes zero (equivalently, the pooled t-test rejects at 0.05).
- Five decision rules compared in RQ1 and applied in RQ2 (amendment 4e adds two more, T and S3): (R) range overlap; (S1) mean ± SEM bars overlap, i.e. |gap| <= SEM_a + SEM_b; (S2) |gap| <= standard error of the difference, i.e. |t| <= 1; (W) Welch t-test at 0.05 flags a mismatch; (E) TOST at margin m shows equivalence. S1 and S2 are the two readings of the paper's "agree within a margin consistent with their standard errors".
- Subset versus full task set from `parity_benchmark_size` < `adapted_benchmark_size`; unknown stays unknown.

## 9. RQ1 simulation designs (fixed now)

- Normal noise: k in 2..10, true gap 0 to 4 SD; exact integrals where available, 200,000 Monte Carlo trials otherwise, seed 7.
- Binomial noise: run score = pass count over n tasks, n in {10, 30, 50, 100, 300, 1000}, base rate p in {0.1, 0.3, 0.5}.
- Realistic noise: per-task pass probabilities drawn from the Harbor-side per-task outcomes of real adapters (a task's probability is its pass rate over the available runs, shrunk toward the mean with a Beta(1,1) prior); runs are simulated by Bernoulli draws per task.
- The "weaker with more runs" and "rewards noise" claims are stated as in memo 0-1, section 3, items 7 and 8, and verified numerically under all three noise models.

## 10. RQ3 designs (fixed now)

- Runs needed: smallest k with TOST power at least 0.8 (and 0.9) for margins 2, 3, 5, under a true gap of 0 and of 0.6 points, at the 25th, 50th and 75th percentile of the observed pooled SD; also per comparison using its own SD.
- Paired per-task analysis: for every adapter whose original-side per-task outcomes can be recovered from the Hugging Face files, align tasks by task id, compute the per-task difference in pass rate across runs, and report a paired 90% and 95% interval (task-level bootstrap, 10,000 resamples, seed 7) and the paired smallest provable margin, next to the run-level interval. Adapters whose original-side files cannot be parsed are listed with the reason.
- Injected-defect study: for each adapter with per-task outcomes on the Harbor side, a defect breaks a fraction f of tasks (forced fail) or leaks a fraction f (forced pass), f in {0.02, 0.05, 0.1, 0.2}; k runs per side are simulated from the per-task model of section 9; detection rate of each rule (R, S1, S2, W, E at m = 3 and 5, and the paired per-task test) over 2,000 replications; k in {3, 5, 10}.
- Amendment 3 (2026-10-11, after a 200-replication smoke test on nine adapters and before the full run): the injected-defect grid gains f = 0 as a no-defect control, so each rule's false-alarm rate and each equivalence test's "shown" rate under true parity are reported on the same per-task model. Reason: the smoke test showed the paired interval is not systematically narrower than the run-level one, so calibration, not width, is the comparison that matters.
- Amendment 5 (2026-10-11, after the per-task recovery and the RQ1 statistics review, before the final RQ3 run): the Beta(1,1) prior on per-task pass probabilities doubles the implied run-to-run SD relative to the observed one (median 3.5 versus 1.7 points), because most tasks are solved in every run or in none and the prior pulls them to 0.2 or 0.8 after three runs. The primary per-task model therefore uses a light shrinkage, (passes + 0.05) / (runs + 0.1), and the Beta(1,1) model is reported as the pre-registered sensitivity. Inclusion rules recorded in `data/pertask/MANIFEST.json`: paired analysis only where both sides reproduce the published run scores and the runs are replicates of one experiment (crustbench included with its sides swapped and flagged; ARC-AGI-2 included at test-pair level); defect simulations only where the Harbor runs are validated replicates with at least 20 tasks and 2 runs.
- Amendment 6 (2026-10-11, after the RQ3 code and statistics reviews, before the final RQ3 run; the pre-amendment outputs are kept in git history at commit 76f6a8c):
  (a) Inclusion: ARC-AGI-2 is excluded from the primary paired and defect sets because three of its six Harbor runs do not reproduce the published scores (reported as a sensitivity row); MMAU is excluded from the paired set because its two sides are per-task identical; SWE-bench Pro's Harbor run 1, which used a different task sample, is dropped from both analyses; the four adapters whose "original" files are Terminal-Bench adapter runs (autocodebench, deveval, livecodebench, quixbugs) form the secondary paired set, as section 1 requires for transitive legs.
  (b) Noise model: the per-task Bernoulli model applies only to adapters with binary outcomes (32 of 39 when this was written; 30 of 38 in the final run, after ARC-AGI-2 was dropped under (a) and PIXIU, whose rewards are fractional, was reclassified by the binary check in the manifest); for the adapters with fractional per-task scores (eight in the final run), runs are simulated by resampling each task's observed rewards across its runs (within-task bootstrap), reported as a sensitivity row. The Beta(1,1) sensitivity is computed for the break defect at k = 3 only.
  (c) Paired test: the paired t on task-level mean differences is kept (it is the statistic named in section 10) and a stratified-by-task test (Cochran-Mantel-Haenszel z on binary outcomes, McNemar at k = 1) is added, because the paired t's standard error includes the between-task spread of a sparse defect and does not shrink with runs.
  (d) Diagnostics added to the paired analysis: a within-task permutation test (2,000 permutations) for whether the task-level spread of side differences exceeds what shared per-task probabilities produce; the same permutation null for the width ratio (its expectation at k = 3 is about 1.19, not 1); and, per side, the ratio of the observed between-run variance of run scores to the variance implied by the within-task flip rates. The width ratio is no longer presented as a method comparison.
  (e) Aggregates in the defect study report the mean, median and interquartile range over adapters, and the model's run SD is the k-independent quantity 100 sqrt(sum p_i (1 - p_i)) / n.
- Protocol and verdict script: `scripts/parity_verdict.py <parity_experiment.json>` prints, per metric row, the overlap verdict, the gap with 95% interval, the smallest provable margin, and the runs per side needed for margins 3 and 5 at 80% power using that row's SD.

## 11. What would change the conclusions

If, under the pre-registered rule, the median smallest provable margin falls below 2 points, or more than half of the comparisons establish equivalence within 3 points, the claim that the published evidence is thin is wrong and the paper narrows to RQ1 and RQ3. If the binomial or realistic noise models reverse the ordering of the decision rules in RQ1, the normal-noise results are dropped from the paper.
