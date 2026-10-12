#!/usr/bin/env bash
# Re-create data/raw/ from the pinned Harbor commit. Needs git and network. Idempotent.
set -euo pipefail
COMMIT=dc933be707feafbb9efcdf092cb8a0e391332617
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$ROOT/external"
if [ ! -d "$ROOT/external/harbor/.git" ]; then
  git clone --filter=blob:none --no-checkout https://github.com/harbor-framework/harbor.git "$ROOT/external/harbor"
fi
git -C "$ROOT/external/harbor" checkout --quiet "$COMMIT"
mkdir -p "$ROOT/data/raw/harbor_parity"
for f in "$ROOT"/external/harbor/adapters/*/parity_experiment.json; do
  cp "$f" "$ROOT/data/raw/harbor_parity/$(basename "$(dirname "$f")").json"
done
cp "$ROOT/external/harbor/adapters/ADAPTER_CONTRIBUTING.md" "$ROOT/data/raw/ADAPTER_CONTRIBUTING.md"
echo "snapshot refreshed from $COMMIT; verify with: .venv/bin/python -I -m pytest -q tests/test_phase0.py -k manifest"
