#!/bin/bash
# Offline end-to-end check: no Docker, no network, no API keys.
#
# Two things were wrong with the previous version. It printed "Backend tests
# (68)" — a number that had been stale for two passes and that nothing
# verified. And it piped the ingest step into `grep`, which replaced the exit
# status with grep's, so an ingest that failed outright still counted as a
# pass. Counts are gone and pipefail is on.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== IP-SAKTI robust check (offline) =="

echo "-- Backend tests --"
(cd backend && python3 -m pytest app/tests/ -q)

echo "-- Ingest dry-run (corpus must load) --"
(cd backend && python3 -m app.pipelines.ingest.cli --manifest ../corpus/manifest.json --dry-run)

echo "-- Eval (exits non-zero on any failing metric) --"
(cd backend && python3 -m app.eval.ragas_eval --golden ../eval/golden_set.json --out ../eval/report.json)

echo "-- API contract smoke --"
(cd backend && python3 -c "
from fastapi.testclient import TestClient
from app.main import app

c = TestClient(app)

# In-scope questions must answer; out-of-scope must abstain. Asserting the
# contract rather than printing it means this step can actually fail.
cases = [
    ({'query': 'Is classical churna patentable under Sec 3(p)?', 'jurisdiction': 'india'}, False),
    ({'query': 'WIPO GRATK disclosure for PCT', 'jurisdiction': 'international'}, False),
    ({'query': 'write a poem about mango', 'jurisdiction': 'india'}, True),
]
for payload, want_abstain in cases:
    r = c.post('/api/v1/chat', json=payload)
    assert r.status_code == 200, (payload, r.status_code)
    j = r.json()
    for key in ('citations', 'confidence', 'firewall', 'corpus_version'):
        assert key in j, (payload, key)
    got = j['confidence']['abstain']
    assert got == want_abstain, (
        f\"{payload['query']!r}: abstain={got} want={want_abstain} \"
        f\"(confidence {j['confidence']['score']:.1f})\"
    )
    print(f\"  {payload['jurisdiction']:14s} conf={j['confidence']['score']:5.1f} \"
          f\"abstain={got} firewall={j['firewall']['status']} docs={len(j['citations'])}\")
print('chat contract OK')
")

echo "-- Frontend typecheck + build --"
(cd frontend && npx tsc --noEmit)
(cd frontend && npm run build)

echo
echo "ALL ROBUST CHECKS PASSED"
echo "Next: make up && make ingest && open http://localhost:3000"
