#!/bin/bash
# Full local health check.
#
# This used to pipe long commands into `tail`, which replaced their exit status
# with tail's — so a failing eval and a failing frontend build both printed a
# green "ALL CHECKS PASSED". It also ran a hand-picked subset of the test files
# (test_classifier, test_chunker, test_api) and called that the suite. It now
# delegates to the Makefile, so there is one definition of "passing" and this
# script cannot drift away from it.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== tests, eval, i18n parity, frontend syntax =="
make check

echo "== ingest dry-run (corpus must load) =="
make ingest-dry

echo "== frontend typecheck + production build =="
make frontend-build

echo
echo "ALL CHECKS PASSED"
