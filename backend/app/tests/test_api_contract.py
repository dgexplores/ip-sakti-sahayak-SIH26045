"""Contract tests — guarantees PS must-haves, win conditions."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_has_version():
    r = client.get("/health")
    assert r.status_code == 200
    j = r.json()
    assert j["status"] == "ok"
    assert "version" in j

def test_corpus_version():
    r = client.get("/api/v1/corpus/version")
    assert r.status_code == 200
    j = r.json()
    assert "corpus_version" in j
    assert "document_count" in j
    assert j["document_count"] >= 10

def test_chat_contract_india_never_misses_fields():
    r = client.post("/api/v1/chat", json={"query": "Is classical churna patentable under Sec 3(p)?", "jurisdiction": "india"})
    assert r.status_code == 200
    j = r.json()
    # contract: all PS fields
    for k in ("answer", "jurisdiction", "citations", "confidence", "corpus_version", "disclaimer"):
        assert k in j, f"missing {k}"
    assert j["jurisdiction"] == "india"
    assert isinstance(j["citations"], list) and len(j["citations"]) > 0
    # citations shape
    c = j["citations"][0]
    for ck in ("id", "title", "span_text", "deep_link", "locator", "version_hash"):
        assert ck in c
    # confidence
    assert 0 <= j["confidence"]["score"] <= 100
    assert "not legal advice" in j["disclaimer"].lower()
    assert "Information only" in j["answer"] or "information" in j["answer"].lower()
    # free tier
    assert "free_tier" in j
    # firewall
    assert "firewall" in j

def test_chat_firewall_mixed_query():
    r = client.post("/api/v1/chat", json={"query": "India Sec 3(p) vs WIPO GRATK PCT mixed", "jurisdiction": "india"})
    assert r.status_code == 200
    j = r.json()
    assert j["firewall"] is not None
    assert j["firewall"]["mixed_query"] is True or j["firewall"]["status"] == "mixed_query"

def test_chat_eli5_mode():
    r = client.post("/api/v1/chat", json={"query": "Is classical churna patentable under Sec 3(p)?", "jurisdiction": "india", "explain_simple": True})
    assert r.status_code == 200
    j = r.json()
    assert j["answer_simple"] is not None
    assert len(j["answer_simple"]) > 10

def test_chat_eli5_false_no_simple():
    r = client.post("/api/v1/chat", json={"query": "Is classical churna patentable under Sec 3(p)?", "jurisdiction": "india", "explain_simple": False})
    assert r.status_code == 200
    assert r.json()["answer_simple"] is None

def test_chat_abstains_for_out_of_scope():
    """Out-of-scope must abstain, not merely score under 70.

    The assertion used to be `score < 70 or abstain or "don't have a grounded
    answer" in answer` — three ways to pass, none of which required the system to
    actually refuse to answer, so a confidently wrong answer would have satisfied
    it as long as its score was 69.
    """
    r = client.post("/api/v1/chat", json={"query": "write a poem about mango unrelated", "jurisdiction": "india"})
    assert r.status_code == 200
    j = r.json()
    assert j["confidence"]["abstain"] is True
    assert j["escalate_suggested"] is True
    assert "don’t have a grounded answer" in j["answer"]
    assert j["citations"] == [] or j["confidence"]["score"] < 50


def test_chat_answers_the_flagship_question():
    """The demo question the project leads with must answer, and answer from the
    Patents Act.

    This is the regression that matters most. A hardcoded 0.62 relevance floor met
    a gate needing ~0.86, so this question abstained at confidence 24.7 — the one
    question the README advertises was the one the system refused. It then, once
    it did answer, led with the Trade Marks Act because that document contains the
    word "recipe".
    """
    r = client.post("/api/v1/chat", json={"query": "Can I patent my grandmother's churna recipe?", "jurisdiction": "india"})
    assert r.status_code == 200
    j = r.json()
    assert j["confidence"]["abstain"] is False, j["confidence"]
    assert j["confidence"]["score"] > 55, j["confidence"]
    assert j["citations"], "an answer must carry citations"
    assert j["citations"][0]["title"].lower().startswith("patents act"), j["citations"][0]["title"]
    assert any("patents_act_1970" in c["id"] or "Patents Act" in c["title"] for c in j["citations"])


def test_chat_never_cites_the_other_jurisdiction():
    """The headline guarantee, asserted on the artefact the reader sees.

    The firewall's leak branches were unreachable dead code because the retriever
    pre-filtered by jurisdiction, so this could not be tested at all.
    """
    for query, jur, foreign in (
        ("Is classical churna patentable under Sec 3(p)?", "india", "international"),
        ("What is the WIPO GRATK disclosure requirement?", "international", "india"),
    ):
        j = client.post("/api/v1/chat", json={"query": query, "jurisdiction": jur}).json()
        for c in j["citations"]:
            assert c["source_type"] != "treaty" or jur == "international", c
        assert j["jurisdiction"] == jur
        assert j["firewall"]["status"] in ("clean", "filtered", "leak_warning", "mixed_query")


def test_firewall_reports_contamination_it_removed():
    """The firewall must have real work to do, and must say so.

    `foreign_ratio` was structurally always 0.0, so the verdict was always
    "clean" and the project's unique win was unobservable.
    """
    j = client.post(
        "/api/v1/chat",
        json={"query": "Is classical churna patentable under Sec 3(p)?", "jurisdiction": "india"},
    ).json()
    fw = j["firewall"]
    assert fw["status"] != "clean" or fw["foreign_ratio"] > 0
    assert fw["foreign_ratio"] > 0, "retrieval must offer both regimes for the firewall to act on"


def test_chat_eli5_works_even_when_abstaining():
    """Simple mode used to be silently skipped whenever the answer abstained, so
    a reader who asked for plain language on an unanswerable question got None."""
    r = client.post(
        "/api/v1/chat",
        json={"query": "asdfgh qwerty zxcvb", "jurisdiction": "india", "explain_simple": True},
    )
    assert r.status_code == 200
    j = r.json()
    assert j["answer_simple"] is not None
    assert len(j["answer_simple"]) > 10


def test_chat_flags_a_toggle_mismatch():
    """An international question under the India toggle must be flagged, not
    silently answered as though the reader had asked about India."""
    j = client.post(
        "/api/v1/chat",
        json={"query": "What is the WIPO GRATK disclosure requirement?", "jurisdiction": "india"},
    ).json()
    assert "toggle" in j["answer"].lower()

def test_chat_formulation_flow():
    r = client.post("/api/v1/chat", json={
        "query": "Classify my formulation: classical vs proprietary",
        "jurisdiction": "india",
        "formulation": {"q_source_text": True, "q_novelty": False, "q_category": "classical"}
    })
    assert r.status_code == 200
    j = r.json()
    assert j["formulation_result"] is not None
    assert j["formulation_result"]["category"] == "classical"

def test_formulation_questions_endpoint():
    r = client.get("/api/v1/formulation-questions")
    assert r.status_code == 200
    assert len(r.json()["questions"]) == 3

def test_classify_contract():
    r = client.post("/api/v1/classify", json={"query": "BDA 2023 ABS benefit sharing for export"})
    assert r.status_code == 200
    j = r.json()
    for k in ("jurisdiction", "ip_type", "confidence", "needs_formulation_flow"):
        assert k in j

def test_escalate_creates_ticket():
    r = client.post("/api/v1/escalate", json={"session_id": "sess_test_123", "query": "need help Sec 3(p)", "reason": "low confidence", "jurisdiction": "india"})
    assert r.status_code == 200
    assert r.json()["ticket_id"].startswith("tick_")

def test_chat_never_conflates_jurisdiction():
    # ask india, ensure returned jurisdiction stays india even if query mentions international term
    r = client.post("/api/v1/chat", json={"query": "WIPO GRATK disclosure but answer only for India Patents Act", "jurisdiction": "india"})
    assert r.json()["jurisdiction"] == "india"
    r2 = client.post("/api/v1/chat", json={"query": "Sec 3(p) India but answer for International PCT", "jurisdiction": "international"})
    assert r2.json()["jurisdiction"] == "international"

def test_chat_language_param():
    r = client.post("/api/v1/chat", json={"query": "Is classical churna patentable?", "jurisdiction": "india", "language": "hi"})
    assert r.status_code == 200
    # should not crash, returns answer (translated via Bhashini mock)
    assert "answer" in r.json()


# ── Quoted law vs our own words ───────────────────────
# The product's entire claim is that a reader can tell the statute apart from
# what we say about it. Three system notices ("Jurisdiction firewall:", "Check
# the toggle:", "Paid database:") were emitted as blockquotes, so they rendered
# in the same grey quote box as the statutory spans.

_NOTICES = ("Jurisdiction firewall:", "Check the toggle:", "Paid database:")


def test_system_notices_are_not_dressed_as_quoted_law():
    """Each notice must appear, and must not be a blockquote."""
    payloads = [
        # firewall filtered (foreign chunks removed from an India answer)
        {"query": "Is classical churna patentable under Sec 3(p)?", "jurisdiction": "india"},
        # toggle mismatch: an international question answered under the India toggle
        {"query": "What is the WIPO GRATK disclosure requirement?", "jurisdiction": "india"},
        # mixed query, plus an explicit request for the paid database
        {"query": "India Sec 3(p) vs WIPO GRATK PCT mixed", "jurisdiction": "india", "allow_paid_db": True},
    ]
    seen: set[str] = set()
    for payload in payloads:
        answer = client.post("/api/v1/chat", json=payload).json()["answer"]
        for line in answer.splitlines():
            for notice in _NOTICES:
                if notice in line:
                    seen.add(notice)
                    assert not line.lstrip().startswith(">"), (
                        f"system notice rendered as a blockquote: {line!r}"
                    )
    assert "Jurisdiction firewall:" in seen, "firewall notice never appeared"
    assert "Check the toggle:" in seen, "mismatch notice never appeared"


def test_every_blockquote_in_an_answer_is_quoted_law():
    """No blockquote may be anything but a verbatim corpus span.

    Calls the eval's own `unverifiable_quotes`, so the unit suite and `make eval`
    cannot drift into disagreeing about what counts as a quotation. (An earlier
    version of this test checked set membership against the whole corpus instead
    of substring containment against the cited chunks, which made it fail on
    perfectly good quotes.)
    """
    from app.eval.ragas_eval import _quoted_spans, _source_texts, cited_texts_of, unverifiable_quotes

    sources = _source_texts()
    assert sources, "offline index is empty — cannot verify quotes"

    for query, jur in (
        ("Is classical churna patentable under Sec 3(p)?", "india"),
        ("What is the WIPO GRATK disclosure requirement?", "international"),
        ("Do I need NBA approval to source aloe vera from Kerala?", "india"),
    ):
        body = client.post("/api/v1/chat", json={"query": query, "jurisdiction": jur}).json()
        answer, citations = body["answer"], body["citations"]
        assert _quoted_spans(answer), f"{query!r} produced no quoted span at all"
        bad, unverifiable = unverifiable_quotes(answer, cited_texts_of(citations, sources))
        assert not bad, f"{query!r} quoted something that is not in the cited source: {bad}"
        assert unverifiable == 0, f"{query!r} had {unverifiable} quote(s) with no cited text to check against"


def test_answer_body_does_not_repeat_the_confidence_rationale():
    """The API returns `confidence.rationale` as a field and the UI renders it
    under the confidence bar. Printing the same sentence inside the answer body
    showed the reader it twice."""
    j = client.post(
        "/api/v1/chat",
        json={"query": "Is classical churna patentable under Sec 3(p)?", "jurisdiction": "india"},
    ).json()
    rationale = j["confidence"]["rationale"]
    assert rationale
    assert rationale not in j["answer"], "confidence rationale duplicated into the answer body"


def test_citation_heading_leads_with_the_provision():
    """Manifest titles are long and descriptive, so title-then-locator produced a
    three-em-dash run-on that buried the provision deciding the question. The
    heading is now the locator, with the document title on the line beneath."""
    j = client.post(
        "/api/v1/chat",
        json={"query": "Is classical churna patentable under Sec 3(p)?", "jurisdiction": "india"},
    ).json()
    first = j["citations"][0]
    lines = j["answer"].splitlines()
    head_i = next(i for i, ln in enumerate(lines) if ln.startswith("**1."))
    heading, subheading = lines[head_i], lines[head_i + 1]
    assert first["locator"] in heading, (heading, first["locator"])
    # The document title is not in the heading line, only on the line below it.
    assert first["title"] not in heading, heading
    assert first["title"] in subheading, (subheading, first["title"])
