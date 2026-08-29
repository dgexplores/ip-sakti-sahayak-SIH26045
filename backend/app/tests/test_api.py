import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_chat_india():
    r = client.post("/api/v1/chat", json={"query": "Is classical churna patentable under Sec 3(p)?", "jurisdiction": "india"})
    assert r.status_code == 200
    j = r.json()
    assert j["jurisdiction"] == "india"
    assert "citations" in j
    assert "confidence" in j
    assert "corpus_version" in j
    assert "Information only" in j["answer"] or "information" in j["answer"].lower()

def test_chat_international():
    r = client.post("/api/v1/chat", json={"query": "WIPO GRATK disclosure requirement for PCT filing with genetic resource", "jurisdiction": "international"})
    assert r.status_code == 200
    assert r.json()["jurisdiction"] == "international"

def test_classify():
    r = client.post("/api/v1/classify", json={"query": "BDA 2023 ABS benefit sharing for export"})
    assert r.status_code == 200
    assert "ip_type" in r.json()

def test_escalate():
    r = client.post("/api/v1/escalate", json={"session_id": "sess_test", "query": "need help", "reason": "low confidence", "jurisdiction": "india"})
    assert r.status_code == 200
    assert "ticket_id" in r.json()
