# Numbers: first pass vs reproduction

Source snapshot: Harbor commit dc933be707feafbb9efcdf092cb8a0e391332617 (see data/raw/MANIFEST.json). 87 of 87 numbers match; where the first pass rounded a value, a match means agreement within that rounding (for the simulated probabilities, within rounding plus Monte Carlo error). Tolerances: 0.01 for simulated probabilities, 0.0075 against the exact integral, 0.05 for values given to one decimal.

The first-pass cut is the first pass's one-main-metric-per-experiment selection of 43 comparisons (three runs per side), defined in `scripts/p0_first_pass_cut.py`.

| Number (as reported by the first pass) | First pass | Reproduced | Match | Script | Output |
|---|---|---|---|---|---|
| files | 84 | 84 | yes | `scripts/p0_inventory.py` | `results/phase0/inventory.json` |
| experiments | 121 | 121 | yes | `scripts/p0_inventory.py` | `results/phase0/inventory.json` |
| metric rows | 298 | 298 | yes | `scripts/p0_inventory.py` | `results/phase0/inventory.json` |
| experiments with 3 runs per side | 68 | 68 | yes | `scripts/p0_inventory.py` | `results/phase0/inventory.json` |
| experiments with 1 run per side | 15 | 15 | yes | `scripts/p0_inventory.py` | `results/phase0/inventory.json` |
| experiments with 2 runs per side | 9 | 9 | yes | `scripts/p0_inventory.py` | `results/phase0/inventory.json` |
| experiments with 5 runs per side | 9 | 9 | yes | `scripts/p0_inventory.py` | `results/phase0/inventory.json` |
| experiments with 4 runs per side | 4 | 4 | yes | `scripts/p0_inventory.py` | `results/phase0/inventory.json` |
| experiments with 6 runs per side | 2 | 2 | yes | `scripts/p0_inventory.py` | `results/phase0/inventory.json` |
| experiments with 8 runs per side | 2 | 2 | yes | `scripts/p0_inventory.py` | `results/phase0/inventory.json` |
| experiments with no run count recorded | 12 | 12 | yes | `scripts/p0_inventory.py` | `results/phase0/inventory.json` |
| parity on a subset | 38 | 38 | yes | `scripts/p0_inventory.py` | `results/phase0/inventory.json` |
| parity on the full set | 77 | 77 | yes | `scripts/p0_inventory.py` | `results/phase0/inventory.json` |
| parity set unknown | 6 | 6 | yes | `scripts/p0_inventory.py` | `results/phase0/inventory.json` |
| metric rows with runs on both sides | 254 | 254 | yes | `scripts/p0_overlap.py` | `results/phase0/overlap.json` |
| rows failing range overlap | 8 | 8 | yes | `scripts/p0_overlap.py` | `results/phase0/overlap.json` |
|   of which 3 runs per side | 5 | 5 | yes | `scripts/p0_overlap.py` | `results/phase0/overlap.json` |
|   of which a single run on one side | 3 | 3 | yes | `scripts/p0_overlap.py` | `results/phase0/overlap.json` |
| failing rows are the eight the first pass names | yes | yes | yes | `scripts/p0_overlap.py` | `results/phase0/overlap.json` |
| rows with identical run lists | 45 | 45 | yes | `scripts/p0_overlap.py` | `results/phase0/overlap.json` |
| rows with zero spread on both sides | 36 | 36 | yes | `scripts/p0_overlap.py` | `results/phase0/overlap.json` |
| P(mismatch) k=2, gap 0 SD (simulation) | 0.33 | 0.331 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| P(mismatch) k=2, gap 1 SD (simulation) | 0.49 | 0.493 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| P(mismatch) k=2, gap 2 SD (simulation) | 0.78 | 0.778 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| P(mismatch) k=2, gap 3 SD (simulation) | 0.94 | 0.943 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| P(mismatch) k=2, gap 4 SD (simulation) | 0.99 | 0.991 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| P(mismatch) k=3, gap 0 SD (simulation) | 0.1 | 0.1 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| P(mismatch) k=3, gap 1 SD (simulation) | 0.26 | 0.262 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| P(mismatch) k=3, gap 2 SD (simulation) | 0.63 | 0.622 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| P(mismatch) k=3, gap 3 SD (simulation) | 0.89 | 0.89 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| P(mismatch) k=3, gap 4 SD (simulation) | 0.98 | 0.982 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| P(mismatch) k=5, gap 0 SD (simulation) | 0.008 | 0.008 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| P(mismatch) k=5, gap 1 SD (simulation) | 0.07 | 0.074 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| P(mismatch) k=5, gap 2 SD (simulation) | 0.38 | 0.376 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| P(mismatch) k=5, gap 3 SD (simulation) | 0.77 | 0.768 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| P(mismatch) k=5, gap 4 SD (simulation) | 0.96 | 0.956 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| P(mismatch) k=8, gap 0 SD (simulation) | 0.0 | 0.0 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| P(mismatch) k=8, gap 1 SD (simulation) | 0.01 | 0.011 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| P(mismatch) k=8, gap 2 SD (simulation) | 0.16 | 0.161 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| P(mismatch) k=8, gap 3 SD (simulation) | 0.59 | 0.586 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| P(mismatch) k=8, gap 4 SD (simulation) | 0.9 | 0.905 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| closed form k=3: 2(3!)^2/6! | 0.1 | 0.1 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| simulation vs exact integral, worst absolute difference in Monte Carlo SEs (must be < 4) | < 4 | 2.63 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| first-pass cut: comparisons analysed | 43 | 43 | yes | `scripts/p0_first_pass_cut.py` | `results/phase0/first_pass_cut.json` |
| first-pass cut: median run-to-run SD (points) | 2.2 | 2.2 | yes | `scripts/p0_first_pass_cut.py` | `results/phase0/first_pass_cut.json` |
| first-pass cut: median gap (points) | 0.6 | 0.6 | yes | `scripts/p0_first_pass_cut.py` | `results/phase0/first_pass_cut.json` |
| first-pass cut: largest gaps, rexbench | 8.3 | 8.3 | yes | `scripts/p0_first_pass_cut.py` | `results/phase0/first_pass_cut.json` |
| first-pass cut: largest gaps, pixiu | 4.9 | 4.9 | yes | `scripts/p0_first_pass_cut.py` | `results/phase0/first_pass_cut.json` |
| first-pass cut: largest gaps, gdb | 4.6 | 4.6 | yes | `scripts/p0_first_pass_cut.py` | `results/phase0/first_pass_cut.json` |
| first-pass cut: largest gaps, multi-swe-bench | 3.3 | 3.3 | yes | `scripts/p0_first_pass_cut.py` | `results/phase0/first_pass_cut.json` |
| first-pass cut: largest gaps, usaco | 2.6 | 2.6 | yes | `scripts/p0_first_pass_cut.py` | `results/phase0/first_pass_cut.json` |
| first-pass cut: fail range overlap | 1 | 1 | yes | `scripts/p0_first_pass_cut.py` | `results/phase0/first_pass_cut.json` |
| first-pass cut: the one failure is usaco [39.5, 40.5, 41.0] vs [45.7, 42.1, 41.1] | yes | yes | yes | `scripts/p0_first_pass_cut.py` | `results/phase0/first_pass_cut.json` |
| first-pass cut: TOST equivalence within +-2 | 5 | 5 | yes | `scripts/p0_first_pass_cut.py` | `results/phase0/first_pass_cut.json` |
| first-pass cut: TOST equivalence within +-3 | 12 | 12 | yes | `scripts/p0_first_pass_cut.py` | `results/phase0/first_pass_cut.json` |
| first-pass cut: TOST equivalence within +-5 | 23 | 23 | yes | `scripts/p0_first_pass_cut.py` | `results/phase0/first_pass_cut.json` |
| first-pass cut: 95% CI equivalence within +-2 | 3 | 3 | yes | `scripts/p0_first_pass_cut.py` | `results/phase0/first_pass_cut.json` |
| first-pass cut: 95% CI equivalence within +-3 | 7 | 7 | yes | `scripts/p0_first_pass_cut.py` | `results/phase0/first_pass_cut.json` |
| first-pass cut: 95% CI equivalence within +-5 | 16 | 16 | yes | `scripts/p0_first_pass_cut.py` | `results/phase0/first_pass_cut.json` |
| first-pass cut: gaps distinguishable from zero | 0 | 0 | yes | `scripts/p0_first_pass_cut.py` | `results/phase0/first_pass_cut.json` |
| runs per side needed for +-2 (median noise, gap 0.6; first-pass plug-in rule) | 14 | 14 | yes | `scripts/p0_first_pass_cut.py` | `results/phase0/first_pass_cut.json` |
| runs per side needed for +-3 (median noise, gap 0.6; first-pass plug-in rule) | 6 | 6 | yes | `scripts/p0_first_pass_cut.py` | `results/phase0/first_pass_cut.json` |
| runs per side needed for +-5 (median noise, gap 0.6; first-pass plug-in rule) | 3 | 3 | yes | `scripts/p0_first_pass_cut.py` | `results/phase0/first_pass_cut.json` |
| exact integral equals closed form at gap 0, k=2 | 0.3333333333333333 | 0.3333333333333333 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| exact integral equals closed form at gap 0, k=3 | 0.1 | 0.09999999999999999 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| exact integral equals closed form at gap 0, k=5 | 0.007936507936507936 | 0.007936507936508422 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| exact integral equals closed form at gap 0, k=8 | 0.0001554001554001554 | 0.0001554001554003167 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| P(mismatch) k=2, gap 0 SD: first pass (rounded) vs exact integral | 0.33 | 0.333 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| P(mismatch) k=2, gap 1 SD: first pass (rounded) vs exact integral | 0.49 | 0.494 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| P(mismatch) k=2, gap 2 SD: first pass (rounded) vs exact integral | 0.78 | 0.778 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| P(mismatch) k=2, gap 3 SD: first pass (rounded) vs exact integral | 0.94 | 0.943 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| P(mismatch) k=2, gap 4 SD: first pass (rounded) vs exact integral | 0.99 | 0.991 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| P(mismatch) k=3, gap 0 SD: first pass (rounded) vs exact integral | 0.1 | 0.1 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| P(mismatch) k=3, gap 1 SD: first pass (rounded) vs exact integral | 0.26 | 0.264 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| P(mismatch) k=3, gap 2 SD: first pass (rounded) vs exact integral | 0.63 | 0.624 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| P(mismatch) k=3, gap 3 SD: first pass (rounded) vs exact integral | 0.89 | 0.89 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| P(mismatch) k=3, gap 4 SD: first pass (rounded) vs exact integral | 0.98 | 0.982 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| P(mismatch) k=5, gap 0 SD: first pass (rounded) vs exact integral | 0.008 | 0.008 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| P(mismatch) k=5, gap 1 SD: first pass (rounded) vs exact integral | 0.07 | 0.074 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| P(mismatch) k=5, gap 2 SD: first pass (rounded) vs exact integral | 0.38 | 0.377 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| P(mismatch) k=5, gap 3 SD: first pass (rounded) vs exact integral | 0.77 | 0.768 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| P(mismatch) k=5, gap 4 SD: first pass (rounded) vs exact integral | 0.96 | 0.956 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| P(mismatch) k=8, gap 0 SD: first pass (rounded) vs exact integral | 0.0 | 0.0 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| P(mismatch) k=8, gap 1 SD: first pass (rounded) vs exact integral | 0.01 | 0.01 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| P(mismatch) k=8, gap 2 SD: first pass (rounded) vs exact integral | 0.16 | 0.162 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| P(mismatch) k=8, gap 3 SD: first pass (rounded) vs exact integral | 0.59 | 0.588 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
| P(mismatch) k=8, gap 4 SD: first pass (rounded) vs exact integral | 0.9 | 0.905 | yes | `scripts/p0_rule_error_rates.py` | `results/phase0/rule_error_rates.json` |
