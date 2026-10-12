# benchmark-port-parity

How much does a parity experiment prove? A statistical look at benchmarks ported to Harbor.

Harbor is the agent-evaluation framework behind Terminal-Bench. Dozens of benchmarks have been ported to it through adapters, and each port is checked with a parity experiment: the same agent and model run on the original harness and on the port, usually three runs per side. Harbor's contributor guide calls the two sides a match when their run-score ranges overlap. This repository asks what that check can and cannot show, re-analyses the published parity runs with confidence intervals and equivalence tests, and proposes a protocol with a stated margin and a known cost in runs.

## Findings in brief

- With three runs per side, the range-overlap rule flags a perfect port 10% of the time, catches a gap of two run-to-run standard deviations 62% of the time, gets more lenient with every added run and with every point of noise, and a pass never means equivalence.
- The 58 published comparisons with three runs look close (median gap 0.7 points) but can show equivalence within 3 points for only 22 of them and within 5 points for 36; the rule passes gaps of 15.6 and 8.3 points.
- Showing equivalence within 3 points at 80% power takes about 7 runs per side at the observed noise. Per-task outcomes expose disagreement between the sides that the run scores hide; a stratified-by-task test is the right paired statistic, and with three runs no calibrated test catches a defect that breaks 10% of tasks more than about two thirds of the time.

The plain-language write-up is `memos/results-memo.md`. Every number in the memos maps to a script and an output file (`NUMBERS.md`, `results/phase2/NUMBERS_phase2.md`).

## Layout

| Path | What it holds |
|---|---|
| `data/raw/harbor_parity/` | the 84 `parity_experiment.json` files, one per adapter, copied from Harbor commit `dc933be707feafbb9efcdf092cb8a0e391332617` (2026-10-10); `data/raw/MANIFEST.json` records a SHA-256 for each |
| `data/raw/ADAPTER_CONTRIBUTING.md` | Harbor's contributor guide at the same commit (the matching criterion is in Step 5) |
| `data/paper/tables_3_4.csv` | Tables 3 and 4 of the Harbor paper, parsed from the arXiv HTML |
| `data/pertask/` | per-task outcomes for both sides of each parity experiment, recovered from the Hugging Face dataset; `MANIFEST.json` records validation against the published run scores and which analyses use each adapter |
| `scripts/parity_lib.py` | shared definitions: loading, run-list parsing, the decision rules, exact error rates, TOST power |
| `scripts/p0_*.py` | reproduction of the first-pass numbers (`results/phase0/`) |
| `scripts/p1_*.py` | paper-table parsing and the prior-work records (`results/phase1/`) |
| `scripts/p2_*.py` | the analysis: comparison table, RQ1 rule properties, RQ2 evidence, RQ3 runs needed, paired analysis and injected defects (`results/phase2/`) |
| `scripts/pertask/<adapter>.py` | one parser per adapter for the Hugging Face result files |
| `scripts/parity_verdict.py` | reads a `parity_experiment.json` and prints the verdict, the smallest provable margin and the runs needed |
| `scripts/run_phase0.sh`, `scripts/run_phase2.sh` | regenerate every output and run the tests |
| `tests/` | pytest suite: closed forms against simulation, rules against scipy, parsing, manifest hashes, synthetic snapshots |
| `memos/` | results memo, pre-registration, and one memo per phase of the work |
| `starter/` | the first-pass scripts, kept unchanged for the record |

## Reproduce

```bash
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -r requirements.txt
bash scripts/run_phase0.sh
bash scripts/run_phase2.sh
```

Scripts are run with `python -I` and take the data directory as an argument, so nothing is imported from the data folders. `scripts/fetch_harbor_snapshot.sh` re-creates `data/raw/` from the pinned commit. The per-task recovery from Hugging Face is documented in `data/pertask/MANIFEST.json`; the parsers take a download directory and an output directory.

## Data sources

- Harbor repository: https://github.com/harbor-framework/harbor (Apache-2.0), pinned at the commit above.
- Raw parity runs: https://huggingface.co/datasets/harborframework/parity-experiments (public).
- The maintainers' paper: arXiv 2609.04298 v3, "Harbor Adapters and Harbor-Index", Appendix D.

Only public data is used. No benchmark was rerun and no model API was called.

## Acknowledgments

The Harbor team made this analysis possible by publishing their parity runs and per-task results.

## License

MIT, see `LICENSE`.
