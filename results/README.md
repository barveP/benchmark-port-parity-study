# Results

- `phase0/`: reproduction of the first-pass numbers (inventory, overlap rule, error rates, the first metric cut); `NUMBERS.md` at the repo root maps each number to its script.
- `phase1/`: prior-work records (candidates screened, sources verified) and the source checks under `extra_verifications/`.
- `phase2/`: the analysis. `comparisons.csv` is the pre-registered comparison table; `rq1_rules.json` the rule error rates; `rq2_summary.json` and `rq2_comparisons.csv` the evidence per comparison; `rq3_*.json` the runs needed, the paired per-task analysis and the injected-defect study; `figures/` the three figures; `NUMBERS_phase2.md` maps every number quoted in the memos to its output.

All outputs regenerate with `scripts/run_phase0.sh` and `scripts/run_phase2.sh`.
