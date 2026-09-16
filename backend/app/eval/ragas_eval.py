"""Eval — runs the real pipeline over a golden set and grades the responses.

What this replaces
------------------
The previous version never invoked the system. Each golden case carried a
hand-written `answer` and `contexts` list, and the three metrics were computed
against those strings: faithfulness was "how much of the answer's own prose
appears in the contexts beside it", citation precision was "does the case's own
`citations[].locator` appear in the case's own `answer`", and abstention read a
`case["abstained"]` key that the golden file did not contain, so it defaulted to
False. `make eval` therefore reported a clean PASS while measuring nothing about
the RAG pipeline, and `ragas_used` was hardcoded false.

What this measures now
----------------------
Every case is posted to the real `/api/v1/chat` route and graded on the response:

  abstention_accuracy   did the system answer / abstain as the case requires
  jurisdiction_accuracy did it answer for the requested regime
  ip_type_accuracy      did the classifier identify the right branch of IP law
  top_citation_accuracy did the FIRST citation come from the expected document
  quote_integrity       is every quoted span a verbatim substring of a cited source
  firewall_integrity    did any citation come from the other jurisdiction

`quote_integrity` is the project's central claim and the one thing that is fully
checkable offline, so it is verified directly against the corpus rather than
against the answer's own text. `faithfulness` is retained as a lexical overlap
diagnostic but is explicitly labelled a heuristic, because without a judge model
it cannot mean what RAGAS means by the term.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from typing import Any

_WS = re.compile(r"\s+")
# A quoted span is a `> ` line that is not the "[Verify at source] …" link line
# that closes each quote block. Only the second line of a block is excluded now:
# the system notices ("Jurisdiction firewall:", "Check the toggle:", "Paid
# database:") used to be blockquotes too, which meant a notice was counted as a
# quotation, and the product's core distinction — quoted law vs our own words —
# was invisible in the one place that could measure it. They are bold paragraphs
# now, so every remaining blockquote must be verbatim statute or registry text.
_QUOTE_LINE = re.compile(r"^>\s+(?!\[)(.+)$", re.MULTILINE)


def _doc_id_of(citation_id: str) -> str:
    """`cite_<doc_id>#<idx>` -> `<doc_id>`."""
    body = citation_id.removeprefix("cite_")
    return body.split("#", 1)[0]


def _source_texts() -> dict[str, str]:
    """chunk_id -> chunk text, from the offline index (no DB required)."""
    from app.rag.retriever import _offline_index

    return {c.id: c.text for c in _offline_index()}


def _quoted_spans(answer: str) -> list[str]:
    return [m.group(1).strip() for m in _QUOTE_LINE.finditer(answer)]


def cited_texts_of(citations: list[dict], sources: dict[str, str]) -> list[str]:
    """Whitespace-normalised text of every chunk the answer cites.

    Whitespace-normalised on both sides because a quote legitimately spans a line
    break in the source markdown, and the rendered answer joins it back up.
    """
    out: list[str] = []
    for c in citations:
        chunk_id = str(c.get("id", "")).removeprefix("cite_")
        if chunk_id in sources:
            out.append(_WS.sub(" ", sources[chunk_id]))
    return out


def unverifiable_quotes(answer: str, cited_texts: list[str]) -> tuple[list[str], int]:
    """Quotes that are not a verbatim substring of any cited chunk.

    Returns (mismatched spans, count that could not be checked at all). This is
    the single definition of "we quote the exact line" — `make eval` and the unit
    suite both call it, so the two cannot drift into disagreeing about what a
    quotation is.
    """
    bad: list[str] = []
    unverifiable = 0
    for q in _quoted_spans(answer):
        if not cited_texts:
            unverifiable += 1
            continue
        if not any(_WS.sub(" ", q) in t for t in cited_texts):
            bad.append(q[:110])
    return bad, unverifiable


def _faithfulness_heuristic(answer: str, contexts: list[str]) -> float:
    """Lexical overlap between the answer and the cited spans.

    A diagnostic, not RAGAS faithfulness: it needs no judge model, and it cannot
    tell a grounded paraphrase from a coincidence. Reported under a name that says
    so.
    """
    if not contexts or not answer:
        return 0.0
    ctx = _WS.sub(" ", " ".join(contexts)).lower()
    words = [w for w in re.findall(r"\w+", answer.lower()) if len(w) > 3]
    if not words:
        return 0.0
    return round(sum(1 for w in words if w in ctx) / len(words), 3)


def evaluate(golden_path: pathlib.Path, out_path: pathlib.Path | None = None) -> dict[str, Any]:
    from fastapi.testclient import TestClient

    from app.main import app

    data = json.loads(golden_path.read_text(encoding="utf-8"))
    cases = data.get("cases") if isinstance(data, dict) and "cases" in data else data
    if not isinstance(cases, list):
        raise ValueError("golden_set must be a list or {cases: [...]}")

    client = TestClient(app)
    sources = _source_texts()

    results: list[dict] = []
    for case in cases:
        cid = case.get("id") or case.get("query", "")[:40]
        jur = case.get("jurisdiction", "india")
        want_abstain = bool(case.get("should_abstain", False))

        resp = client.post("/api/v1/chat", json={"query": case["query"], "jurisdiction": jur, "language": "en"})
        if resp.status_code != 200:
            results.append({"id": cid, "error": f"HTTP {resp.status_code}", "response": resp.text[:200]})
            continue
        body = resp.json()
        answer = body["answer"]
        conf = body["confidence"]
        citations = body["citations"]
        firewall = body.get("firewall") or {}

        # ── abstention ──────────────────────────────────
        abstained = bool(conf["abstain"])
        abstain_ok = abstained == want_abstain

        # ── jurisdiction ────────────────────────────────
        jurisdiction_ok = body["jurisdiction"] == jur

        # ── classifier ──────────────────────────────────
        expected_ip = case.get("expected_ip_type")
        classified = client.post("/api/v1/classify", json={"query": case["query"], "jurisdiction": jur}).json()
        ip_ok = classified.get("ip_type") == expected_ip if expected_ip else True

        # ── top citation ────────────────────────────────
        # `expect_top_doc_any` is for cases where two documents answer equally
        # well — "how do I get a GI tag" is served by the GI Act that defines the
        # right and by the registry guide that says how to file it.
        expect_top = case.get("expect_top_doc")
        expect_any = case.get("expect_top_doc_any")
        top_doc = _doc_id_of(citations[0]["id"]) if citations else None
        if expect_top is None and not expect_any:
            top_ok = True
        elif expect_any:
            top_ok = top_doc in expect_any
        else:
            top_ok = top_doc == expect_top

        # ── quote integrity ─────────────────────────────
        # Every `> ` line in the answer must be a whitespace-normalised substring
        # of some cited chunk's text. This is the "we quote the exact line" claim.
        quoted = _quoted_spans(answer)
        cited_texts = cited_texts_of(citations, sources)
        if abstained:
            bad_quotes: list[str] = []
            unverifiable = 0
        else:
            bad_quotes, unverifiable = unverifiable_quotes(answer, cited_texts)
        quote_ok = not bad_quotes and unverifiable == 0

        # ── firewall ────────────────────────────────────
        foreign = [c for c in citations if c["id"] and c["source_type"] == "treaty" and jur == "india"]
        firewall_ok = not foreign

        results.append(
            {
                "id": cid,
                "query": case["query"][:70],
                "jurisdiction": jur,
                "confidence": conf["score"],
                "abstained": abstained,
                "want_abstain": want_abstain,
                "abstain_ok": abstain_ok,
                "jurisdiction_ok": jurisdiction_ok,
                "ip_type": classified.get("ip_type"),
                "ip_type_ok": ip_ok,
                "top_doc": top_doc,
                "expect_top_doc": expect_top or (f"any of {expect_any}" if expect_any else None),
                "top_ok": top_ok,
                "quotes": len(quoted),
                "bad_quotes": bad_quotes,
                "unverifiable_quotes": unverifiable,
                "quote_ok": quote_ok,
                "firewall_status": firewall.get("status"),
                "foreign_ratio": firewall.get("foreign_ratio"),
                "firewall_ok": firewall_ok,
                "faithfulness_heuristic": _faithfulness_heuristic(answer, cited_texts),
            }
        )

    def _rate(key: str) -> float:
        graded = [r for r in results if key in r]
        if not graded:
            return 0.0
        return round(sum(1 for r in graded if r[key]) / len(graded), 3)

    # Calibration: the gap the confidence threshold has to sit inside.
    in_scope = [r["confidence"] for r in results if r.get("want_abstain") is False and "confidence" in r]
    out_scope = [r["confidence"] for r in results if r.get("want_abstain") is True and "confidence" in r]

    report: dict[str, Any] = {
        "total": len(results),
        "abstention_accuracy": _rate("abstain_ok"),
        "jurisdiction_accuracy": _rate("jurisdiction_ok"),
        "ip_type_accuracy": _rate("ip_type_ok"),
        "top_citation_accuracy": _rate("top_ok"),
        "quote_integrity": _rate("quote_ok"),
        "firewall_integrity": _rate("firewall_ok"),
        "calibration": {
            "in_scope_min": min(in_scope) if in_scope else None,
            "in_scope_max": max(in_scope) if in_scope else None,
            "out_of_scope_min": min(out_scope) if out_scope else None,
            "out_of_scope_max": max(out_scope) if out_scope else None,
            "separation": round(min(in_scope) - max(out_scope), 1) if in_scope and out_scope else None,
        },
        "faithfulness_heuristic_mean": round(
            sum(r.get("faithfulness_heuristic", 0.0) for r in results) / max(1, len(results)), 3
        ),
        "ragas_used": False,
        "ragas_note": "No judge model configured. `faithfulness_heuristic_mean` is lexical overlap, not RAGAS faithfulness.",
        "cases": results,
    }

    # The eval must be able to fail. A single wrong answer, a single quote that is
    # not verbatim, or a single cross-jurisdiction citation is a failure.
    failures = {
        "abstention_accuracy": report["abstention_accuracy"] == 1.0,
        "jurisdiction_accuracy": report["jurisdiction_accuracy"] == 1.0,
        "ip_type_accuracy": report["ip_type_accuracy"] == 1.0,
        "top_citation_accuracy": report["top_citation_accuracy"] >= 0.85,
        "quote_integrity": report["quote_integrity"] == 1.0,
        "firewall_integrity": report["firewall_integrity"] == 1.0,
    }
    report["checks"] = failures
    report["verdict"] = "PASS" if all(failures.values()) else "FAIL"

    if out_path:
        out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    _print_report(report)
    return report


def _print_report(report: dict[str, Any]) -> None:
    print(f"[eval] {report['total']} cases — verdict {report['verdict']}")
    print(f"{'metric':28s} {'value':>7s}  ok")
    for k in (
        "abstention_accuracy",
        "jurisdiction_accuracy",
        "ip_type_accuracy",
        "top_citation_accuracy",
        "quote_integrity",
        "firewall_integrity",
    ):
        ok = report["checks"][k]
        print(f"  {k:26s} {report[k]:>7.3f}  {'OK' if ok else 'FAIL'}")
    cal = report["calibration"]
    print(
        f"  calibration: in-scope {cal['in_scope_min']}-{cal['in_scope_max']}, "
        f"out-of-scope {cal['out_of_scope_min']}-{cal['out_of_scope_max']}, separation {cal['separation']}"
    )
    print(f"  faithfulness (lexical heuristic): {report['faithfulness_heuristic_mean']}")

    bad = [
        r
        for r in report["cases"]
        if r.get("error")
        or not r.get("abstain_ok", True)
        or not r.get("top_ok", True)
        or not r.get("quote_ok", True)
        or not r.get("ip_type_ok", True)
    ]
    if bad:
        print("\n[failures]")
        for r in bad:
            if r.get("error"):
                print(f"  {r['id']}: {r['error']}")
                continue
            bits = []
            if not r.get("abstain_ok"):
                bits.append(f"abstain={r['abstained']} want={r['want_abstain']} (conf {r['confidence']})")
            if not r.get("ip_type_ok"):
                bits.append(f"ip_type={r['ip_type']}")
            if not r.get("top_ok"):
                bits.append(f"top_doc={r['top_doc']} want={r['expect_top_doc']}")
            if not r.get("quote_ok"):
                bits.append(f"bad_quotes={r['bad_quotes']} unverifiable={r['unverifiable_quotes']}")
            print(f"  {r['id']}: {'; '.join(bits)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--golden", required=True)
    ap.add_argument("--out", required=False)
    args = ap.parse_args()
    report = evaluate(pathlib.Path(args.golden), pathlib.Path(args.out) if args.out else None)
    sys.exit(0 if report["verdict"] == "PASS" else 1)


if __name__ == "__main__":
    main()
