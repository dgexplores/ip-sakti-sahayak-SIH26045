#!/bin/zsh
# Grade golden cases against the LIVE API via curl. Run from repo root.
BASE="${1:-https://sakti-api.onrender.com}"
PASS=0; TOTAL=0
grade() {
  local q="$1" jur="$2" want_abstain="$3" want_loc="$4"
  TOTAL=$((TOTAL+1))
  local resp
  resp=$(curl -s -m 120 -X POST "$BASE/api/v1/chat" -H "Content-Type: application/json" \
    --data "{\"query\":$(printf '%s' "$q" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))'),\"jurisdiction\":\"$jur\",\"language\":\"en\",\"explain_simple\":false}")
  local score abstain gotjur fw ncite toploc
  score=$(printf '%s' "$resp" | python3 -c "import json,sys; print(json.load(sys.stdin)['confidence']['score'])")
  abstain=$(printf '%s' "$resp" | python3 -c "import json,sys; print(json.load(sys.stdin)['confidence']['abstain'])")
  gotjur=$(printf '%s' "$resp" | python3 -c "import json,sys; print(json.load(sys.stdin).get('jurisdiction'))")
  fw=$(printf '%s' "$resp" | python3 -c "import json,sys; print((json.load(sys.stdin).get('firewall') or {}).get('status'))")
  ncite=$(printf '%s' "$resp" | python3 -c "import json,sys; print(len(json.load(sys.stdin).get('citations',[])))")
  toploc=$(printf '%s' "$resp" | python3 -c "import json,sys; c=json.load(sys.stdin).get('citations',[]); print(c[0].get('locator','')[:50] if c else '')")
  local ok="PASS" want_ab="False"
  [ "$want_abstain" = "1" ] && want_ab="True"
  [ "$abstain" != "$want_ab" ] && ok="FAIL(abstain:$abstain)"
  [ "$gotjur" != "$jur" ] && ok="FAIL(jur:$gotjur)"
  echo "[$ok] ${q:0:55} | score=$score abstain=$abstain fw=$fw cites=$ncite top=$toploc"
  [ "$ok" = "PASS" ] && PASS=$((PASS+1))
}
grade "Is classical Ashwagandha churna as per Charaka Samhita patentable in India?" india 0
grade "I made a novel Ashwagandha extract with 10x withanolide by new process, patentable?" india 0
grade "WIPO GRATK disclosure requirement for PCT filing with Indian genetic resource" international 0
grade "Do I need NBA approval to export aloe vera sourced in Kerala for cosmetic use?" india 0
grade "Can I sell chyawanprash as food under FSSAI Ayurveda Aahar or need drug licence?" india 0
grade "Random unrelated: write a poem about mango" india 1
echo "== $PASS/$TOTAL =="
