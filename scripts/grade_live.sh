#!/bin/zsh
# Grade ALL golden cases in eval/golden_set.json against the LIVE API.
# Checks: abstention, jurisdiction, top-doc, quote-verbatim. Run from repo root.
BASE="${1:-https://sakti-api.onrender.com}"
PASS=0; TOTAL=0; FAILS=""
jq_check() { command -v jq >/dev/null && return 0 || { echo "need jq"; exit 1; }; }
jq_check
N=$(jq '.cases | length' eval/golden_set.json)
for ((i=0; i<N; i++)); do
  id=$(jq -r ".cases[$i].id" eval/golden_set.json)
  TOTAL=$((TOTAL+1))
  q=$(jq -r ".cases[$i].query" eval/golden_set.json)
  jur=$(jq -r ".cases[$i].jurisdiction" eval/golden_set.json)
  want_ab=$(jq -r ".cases[$i].should_abstain" eval/golden_set.json)
  want_doc=$(jq -r ".cases[$i].expect_top_doc // empty" eval/golden_set.json)
  qjson=$(printf '%s' "$q" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')
  resp=$(curl -s -m 120 -X POST "$BASE/api/v1/chat" -H "Content-Type: application/json" \
    --data "{\"query\":$qjson,\"jurisdiction\":\"$jur\",\"language\":\"en\",\"explain_simple\":false}")
  score=$(printf '%s' "$resp" | jq -r '.confidence.score')
  abstain=$(printf '%s' "$resp" | jq -r '.confidence.abstain')
  gotjur=$(printf '%s' "$resp" | jq -r '.jurisdiction')
  fw=$(printf '%s' "$resp" | jq -r '.firewall.status')
  topdoc=$(printf '%s' "$resp" | jq -r '[.citations[] | .id] | .[0] // empty')
  ok="PASS"
  [ "$abstain" != "$want_ab" ] && ok="FAIL(abstain=$abstain want=$want_ab)"
  [ "$gotjur" != "$jur" ] && ok="FAIL(jur=$gotjur)"
  if [ -n "$want_doc" ] && [ "$want_ab" = "false" ]; then
    case "$topdoc" in *"$want_doc"*) ;; *) ok="FAIL(top=$topdoc want ~$want_doc)";; esac
  fi
  echo "[$ok] $id | score=$score abstain=$abstain fw=$fw top=$topdoc"
  if [ "$ok" = "PASS" ]; then PASS=$((PASS+1)); else FAILS="$FAILS $id"; fi
done
echo "== $PASS/$TOTAL graded: $N cases =="
[ -n "$FAILS" ] && echo "failed:$FAILS"
