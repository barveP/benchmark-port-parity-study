# Data

- `raw/harbor_parity/`: the 84 `parity_experiment.json` files from the Harbor repository at commit `dc933be707feafbb9efcdf092cb8a0e391332617` (2026-10-10), one per adapter, unchanged. `raw/MANIFEST.json` holds a SHA-256 per file; `tests/test_phase0.py` checks them.
- `raw/ADAPTER_CONTRIBUTING.md`: Harbor's adapter guide at the same commit; Step 5 states the range-overlap matching criterion.
- `paper/tables_3_4.csv`: Tables 3 and 4 of arXiv 2609.04298 v3 (parity results per adapter), parsed by `scripts/p1_parse_paper_tables.py`.
- `pertask/<adapter>/{original,harbor}.csv`: per-task outcomes (`run, task_id, reward`) recovered from the Hugging Face dataset `harborframework/parity-experiments` with `scripts/pertask/<adapter>.py`. `pertask/MANIFEST.json` records, per adapter, the files used, the formats, whether the recovered run means reproduce the published run scores, and which analyses the adapter enters.
