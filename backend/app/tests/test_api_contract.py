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

def test_chat_abstain_for_nonsense():
    r = client.post("/api/v1/chat", json={"query": "write a poem about mango unrelated", "jurisdiction": "india"})
    assert r.status_code == 200
    j = r.json()
    # nonsense should either abstain or low confidence
    assert j["confidence"]["score"] < 70 or j["confidence"]["abstain"] is True or "don't have a grounded answer" in j["answer"].lower()

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
