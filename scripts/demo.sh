#!/bin/bash
set -e
echo "IP-SAKTI Sahayak — demo script (2 min)"
echo "1. Start stack: make up"
echo "2. Ingest: make ingest"
echo "3. Open frontend http://localhost:3000 + API http://localhost:8000/docs"
echo ""
echo "Try:"
echo "  curl -X POST http://localhost:8000/api/v1/chat -H 'Content-Type: application/json' -d '{\"query\":\"Is classical churna patentable under Sec 3(p)?\",\"jurisdiction\":\"india\"}' | jq"
echo "  curl -X POST http://localhost:8000/api/v1/chat -H 'Content-Type: application/json' -d '{\"query\":\"WIPO GRATK disclosure for PCT with genetic resource\",\"jurisdiction\":\"international\"}' | jq"
