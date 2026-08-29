#!/bin/bash
set -e
cd "$(dirname "$0")/.."
echo "== chunker + classifier tests =="
cd backend && python3 -m pytest app/tests/test_classifier.py app/tests/test_chunker.py -v
echo "== api tests =="
python3 -m pytest app/tests/test_api.py -v
echo "== ingest dry-run =="
python3 -m app.pipelines.ingest.cli --manifest ../corpus/manifest.json --dry-run | tail -20
echo "== eval =="
python3 -m app.eval.ragas_eval --golden ../eval/golden_set.json | tail -20
echo "== frontend build =="
cd ../frontend && npm run build | tail -20
echo "ALL CHECKS PASSED"
