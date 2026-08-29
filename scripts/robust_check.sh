#!/bin/bash
set -e
cd "$(dirname "$0")/.."
echo "== IP-SAKTI Robust Check (free, offline) =="
echo "-- Backend tests (68) --"
cd backend && python3 -m pytest app/tests/ -q
echo "-- Ingest dry-run --"
python3 -m app.pipelines.ingest.cli --manifest ../corpus/manifest.json --dry-run | grep -E "done|docs|chunks|dry"
echo "-- Eval --"
python3 -m app.eval.ragas_eval --golden ../eval/golden_set.json --out ../eval/report.json
cat ../eval/report.json | grep -E "faithfulness|abstention|citation|verdict|total"
echo "-- API smoke --"
python3 -c "
from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)
for payload in [
  {'query':'Is classical churna patentable under Sec 3(p)?','jurisdiction':'india'},
  {'query':'WIPO GRATK disclosure for PCT','jurisdiction':'international'},
  {'query':'write a poem about mango','jurisdiction':'india'},
]:
    r=c.post('/api/v1/chat',json=payload)
    assert r.status_code==200
    j=r.json()
    assert 'citations' in j and 'confidence' in j and 'firewall' in j
    print(f\"✓ {payload['jurisdiction']}: {j['confidence']['score']:.0f}% abstain={j['confidence']['abstain']} firewall={j['firewall']['status']}\")
print('all chat contracts OK')
"
echo "-- Frontend build --"
cd ../frontend && npm run build > /tmp/build.log 2>&1 && grep -E "Compiled|First Load" /tmp/build.log | head -5
echo ""
echo "ALL ROBUST CHECKS PASSED ✅"
echo "Next: make up && make ingest && open http://localhost:3000"
