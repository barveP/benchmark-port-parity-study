# benchmark-port-parity

How much does a parity experiment prove? A statistical look at benchmarks ported to Harbor.

Harbor is the agent-evaluation framework behind Terminal-Bench. About 90 benchmarks have been ported to it through adapters, and each port is checked with a "parity experiment": the same agent and model run on the original harness and on the port, usually three runs per side. Harbor's contributor guide calls the two sides a match when their run-score ranges overlap. This project asks what that check can and cannot show, re-analyses the published parity runs with confidence intervals and equivalence tests, and proposes a protocol with a stated margin.

## Status

- Phase 0 (reproduce the first-pass numbers): done. Every number in `BRIEF.md` regenerates from `scripts/`; see `NUMBERS.md`. Two independent re-derivations and two adversarial reviews found no arithmetic errors; the caveats they raised are in `memos/phase-0-1-memo.md`.
- Phase 1 (prior-work check): done; table and verdict in `memos/phase-0-1-memo.md`.
- Phase 2 (analysis): in progress on branch `phase-2`; rules fixed in `memos/phase-2-preregistration.md` before any outcome was computed; results in `results/phase2/`.
- Phases 3 and 4 (results memo, paper): not started.

## Layout

| Path | What it holds |
|---|---|
| `BRIEF.md` | the research brief (kept untracked until the author decides it belongs in the repo) |
| `data/raw/harbor_parity/` | the 84 `parity_experiment.json` files, one per adapter, copied from Harbor commit `dc933be707feafbb9efcdf092cb8a0e391332617` (2026-10-10); `data/raw/MANIFEST.json` records a SHA-256 for each |
| `data/raw/ADAPTER_CONTRIBUTING.md` | Harbor's contributor guide at the same commit (the matching criterion is in Step 5) |
| `scripts/parity_lib.py` | shared definitions: loading, run-list parsing, the overlap rule, its exact error rates, SEM, t quantiles |
| `scripts/p0_*.py` | Phase 0 scripts; each writes JSON/CSV into `results/phase0/` |
| `scripts/p1_parse_paper_tables.py` | parses Tables 3 and 4 of the Harbor paper (arXiv HTML) into `data/paper/tables_3_4.csv` and cross-checks them against the JSON |
| `scripts/p2_build_comparisons.py` | one comparison per experiment under the pre-registered rule |
| `scripts/p2_rq1_rules.py` | error rates of the overlap rule and three alternatives under normal, binomial and per-task noise |
| `scripts/p2_rq2_evidence.py` | gaps, intervals and smallest provable margins for every comparison |
| `scripts/p2_rq3_runs_needed.py`, `p2_rq3_paired.py`, `p2_rq3_defects.py` | runs needed at 80% power; paired per-task analysis; injected-defect detection curves |
| `scripts/parity_verdict.py` | reads a `parity_experiment.json` and prints the verdict, the smallest provable margin and the runs needed |
| `scripts/pertask/<adapter>.py`, `data/pertask/<adapter>/` | per-task outcomes recovered from the Hugging Face dataset, one parser per adapter, validated against the published run scores |
| `scripts/run_phase0.sh` | regenerates all Phase 0 outputs, rewrites `NUMBERS.md`, runs the tests |
| `scripts/fetch_harbor_snapshot.sh` | re-creates `data/raw/` from the pinned commit |
| `starter/` | the first-pass scripts, kept unchanged for the record |
| `tests/` | pytest suite (closed form vs simulation, parsing, manifest hashes, synthetic snapshot) |
| `memos/` | one memo per phase |
| `NUMBERS.md` | every number in the brief, its regenerated value, the script and output file it comes from |

## Reproduce

```bash
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python numpy scipy matplotlib pytest pypdf
bash scripts/run_phase0.sh
bash scripts/run_phase2.sh
```

Scripts are run with `python -I` and take the data directory as an argument, so nothing is imported from the data folder.

## Data sources

- Harbor repository: https://github.com/harbor-framework/harbor (Apache-2.0), pinned at the commit above.
- Raw parity runs: https://huggingface.co/datasets/harborframework/parity-experiments (public).
- The maintainers' paper: arXiv 2609.04298 v3, "Harbor Adapters and Harbor-Index", Appendix D.

Only public data is used. No model API calls are made anywhere in this repository.

## Acknowledgments

The Harbor team made this analysis possible by publishing their parity runs.

## License

MIT, see `LICENSE`.
