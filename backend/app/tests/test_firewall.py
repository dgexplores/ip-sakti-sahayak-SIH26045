from app.models.schemas import Jurisdiction
from app.rag.jurisdiction_firewall import filter_by_firewall, firewall_check
from app.rag.retriever import RetrievedChunk


def _chunk(jurisdiction="india", id="c1", score=0.9):
    return RetrievedChunk(id=id, doc_id=id, doc_title="T", source_type="statute", jurisdiction=jurisdiction, text="sec 3p text", locator="Sec 3(p)", deep_link="http://x", version_hash="abc", score=score)


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


def test_leak_warning_fires_when_the_best_match_is_the_other_regime():
    """The dangerous case, and the only one worth calling a leak.

    Retrieval returns both regimes by design, so a verdict of "leak" merely
    because the pool held foreign candidates would fire on nearly every request
    and tell the reader nothing. What matters is the strongest candidate for the
    question belonging to the other side — usually a sign the toggle is wrong.
    """
    chunks = [
        _chunk("international", "c1", score=0.91),
        _chunk("india", "c2", score=0.40),
        _chunk("india", "c3", score=0.38),
    ]
    r = firewall_check("Is classical churna patentable?", Jurisdiction.INDIA, chunks)
    assert r["status"] == "leak_warning"
    assert "international" in r["message"]


def test_ordinary_contamination_is_reported_as_filtered_not_a_leak():
    """A foreign candidate that ranks below the answer's own law is not a leak."""
    chunks = [
        _chunk("india", "c1", score=0.91),
        _chunk("india", "c2", score=0.70),
        _chunk("international", "c3", score=0.30),
    ]
    r = firewall_check("Is classical churna patentable?", Jurisdiction.INDIA, chunks)
    assert r["status"] == "filtered"
    assert "Removed 1 of 3" in r["message"]


def test_filter_by_firewall_keeps_only_the_requested_regime():
    chunks = [_chunk("india", "c1"), _chunk("international", "c2"), _chunk("india", "c3")]
    kept = filter_by_firewall(chunks, Jurisdiction.INDIA)
    assert [c.id for c in kept] == ["c1", "c3"]


def test_filter_by_firewall_never_returns_nothing():
    """Answering from nothing is worse than answering off-jurisdiction, and the
    verdict still reports that the answer is off-jurisdiction."""
    chunks = [_chunk("international", "c1"), _chunk("international", "c2")]
    kept = filter_by_firewall(chunks, Jurisdiction.INDIA)
    assert len(kept) == 2
    r = firewall_check("Is classical churna patentable?", Jurisdiction.INDIA, chunks)
    assert r["status"] == "leak_warning"


def test_verdict_is_json_serialisable():
    """The verdict is embedded in the API response, so it cannot carry chunks."""
    import json

    chunks = [_chunk("india", "c1"), _chunk("international", "c2")]
    r = firewall_check("Is churna patentable?", Jurisdiction.INDIA, chunks)
    assert json.loads(json.dumps(r)) == r
