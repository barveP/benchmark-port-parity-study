#!/usr/bin/env bash
# Regenerate every Phase 2 output. Run from the repo root. The per-task steps need data/pertask/ (see README).
set -euo pipefail
PY=.venv/bin/python
SNAP=data/raw/harbor_parity
OUT=results/phase2
$PY -I scripts/p2_build_comparisons.py "$SNAP" data/paper/tables_3_4.csv "$OUT"
$PY -I scripts/p2_rq2_evidence.py "$OUT" results/phase0
$PY -I scripts/p2_rq1_rules.py "$OUT" data/pertask
$PY -I scripts/p2_rq3_runs_needed.py "$OUT"
if [ -d data/pertask ]; then
  $PY -I scripts/p2_rq3_paired.py data/pertask "$SNAP" "$OUT"
  $PY -I scripts/p2_rq3_defects.py data/pertask "$OUT"
fi
$PY -I -m pytest -q
