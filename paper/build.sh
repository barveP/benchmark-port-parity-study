#!/usr/bin/env bash
# Build the paper with tectonic (fetches IEEEtran and other packages on first use) and report the page count.
set -euo pipefail
cd "$(dirname "$0")"
tectonic -c minimal main.tex
../.venv/bin/python -I -c "from pypdf import PdfReader; print('pages:', len(PdfReader('main.pdf').pages))"
