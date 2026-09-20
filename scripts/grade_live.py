"""Grade the 6 golden cases against the LIVE API. Run: python3 scripts/grade_live.py [BASE_URL]"""
import json
import sys
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "https://sakti-api.onrender.com"


def post(path, body):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def main():
    cases = json.load(open("eval/golden_set.json"))["cases"]
    passed = 0
    for i, c in enumerate(cases):
        q = c["query"]
        jur = c.get("expected_jurisdiction", "india")
        try:
            r = post("/api/v1/chat", {
                "query": q, "jurisdiction": jur, "language": "en",
                "explain_simple": False,
            })
        except Exception as e:
            print(f"[{i}] {q[:50]!r} ERROR {e}")
            continue
        checks = []
        # 1. abstention matches
        want_abstain = bool(c.get("should_abstain"))
        got_abstain = bool(r["confidence"]["abstain"])
        checks.append(("abstain", want_abstain == got_abstain,
                       f"want={want_abstain} got={got_abstain} score={r['confidence']['score']}"))
        # 2. jurisdiction matches
        checks.append(("jurisdiction", r.get("jurisdiction") == jur,
                       f"want={jur} got={r.get('jurisdiction')}"))
        # 3. expected locator cited (substring, locator markers stripped like UI does)
        want_locs = [x.get("locator", "") for x in c.get("citations", [])]
        got_locs = " | ".join(x.get("locator", "") for x in r.get("citations", []))
        for wl in want_locs:
            key = wl.replace("#", "").strip().split("—")[0].strip().split("-")[0].strip()
            key = key.replace("Sec ", "Sec ").strip()
            checks.append((f"locator:{key[:30]}", key[:12] in got_locs, f"in [{got_locs[:80]}]"))
        # 4. quote integrity: every blockquote line verbatim in some cited span
        spans = [x.get("span_text", "") for x in r.get("citations", [])]
        bad = []
        for line in r.get("answer", "").split("\n"):
            s = line.strip()
            if s.startswith(">"):
                q2 = s.lstrip(">").strip().strip("*").strip()
                if q2 and not any(q2[:60] in sp or q2 in sp for sp in spans):
                    # allow system-notice bold paragraphs (not statute quotes)
                    if not (q2.startswith("**Jurisdiction") or q2.startswith("**Paid")):
                        bad.append(q2[:60])
        checks.append(("quotes-verbatim", not bad, f"bad={bad[:2]}" if bad else "all clean"))
        ok = all(x[1] for x in checks)
        passed += ok
        print(f"[{'PASS' if ok else 'FAIL'}] {q[:55]!r}")
        for name, good, detail in checks:
            if not good:
                print(f"    x {name}: {detail}")
        fw = (r.get("firewall") or {}).get("status")
        print(f"    score={r['confidence']['score']} abstain={got_abstain} firewall={fw}")
    print(f"\n{passed}/{len(cases)} cases pass")


if __name__ == "__main__":
    main()
