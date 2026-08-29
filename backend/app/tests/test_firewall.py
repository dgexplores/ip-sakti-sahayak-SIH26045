from app.rag.jurisdiction_firewall import firewall_check
from app.rag.retriever import RetrievedChunk
from app.models.schemas import Jurisdiction

def _chunk(jurisdiction="india", id="c1"):
    return RetrievedChunk(id=id, doc_id=id, doc_title="T", source_type="statute", jurisdiction=jurisdiction, text="sec 3p text", locator="Sec 3(p)", deep_link="http://x", version_hash="abc", score=0.9)

def test_clean_india():
    r = firewall_check("Is churna patentable under Sec 3(p)?", Jurisdiction.INDIA, [_chunk("india"), _chunk("india", "c2")])
    assert r["status"] == "clean"
    assert r["foreign_ratio"] == 0

def test_leak_filtered():
    chunks = [_chunk("india"), _chunk("international", "c2"), _chunk("international", "c3"), _chunk("india", "c4")]
    r = firewall_check("India Sec 3(p) query", Jurisdiction.INDIA, chunks)
    assert r["foreign_ratio"] == 0.5
    assert r["status"] in ("leak_warning", "filtered")

def test_mixed_query_flag():
    r = firewall_check("India Sec 3(p) vs WIPO GRATK PCT", Jurisdiction.INDIA, [_chunk("india")])
    assert r["mixed_query"] is True
    assert r["status"] == "mixed_query"

def test_international_request():
    r = firewall_check("WIPO GRATK Art 3", Jurisdiction.INTERNATIONAL, [_chunk("international")])
    assert r["status"] == "clean"
