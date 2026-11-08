#!/usr/bin/env bash
# Regenerate every Phase 0 number and compare it with the first-pass value (written to NUMBERS.md).
# Run from the repo root.
set -euo pipefail
PY=.venv/bin/python
SNAP=data/raw/harbor_parity
OUT=results/phase0
$PY -I scripts/p0_inventory.py "$SNAP" "$OUT"
$PY -I scripts/p0_overlap.py "$SNAP" "$OUT"
$PY -I scripts/p0_rule_error_rates.py "$OUT"
$PY -I scripts/p0_first_pass_cut.py "$SNAP" "$OUT"
$PY -I scripts/p0_reported_vs_runs.py "$SNAP" "$OUT"
$PY -I scripts/p0_check_first_pass.py "$OUT" NUMBERS.md
$PY -I -m pytest -q
