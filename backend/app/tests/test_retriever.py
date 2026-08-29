import pytest
from app.rag.retriever import to_citations, RetrievedChunk, retrieve_all
from app.models.schemas import Jurisdiction

def _c(id="c1", jurisdiction="india"):
    return RetrievedChunk(id=id, doc_id=id, doc_title="Patents Act Sec 3p", source_type="statute", jurisdiction=jurisdiction, text="span text here", locator="Sec 3(p)", deep_link="https://example.com", version_hash="abc", score=0.9)

def test_to_citations_maps():
    cs = to_citations([_c()])
    assert cs[0].id == "cite_c1"
    assert cs[0].locator == "Sec 3(p)"
    assert cs[0].deep_link == "https://example.com"

@pytest.mark.asyncio
async def test_retrieve_all_mock_fallback():
    # without DB, should return mock chunks
    vec = [0.1]*384
    out = await retrieve_all(vec, Jurisdiction.INDIA, top_k_each=2)
    assert len(out) > 0
    # should dedupe
    ids = [c.id for c in out]
    assert len(ids) == len(set(ids))
    # sorted by score desc
    scores = [c.score for c in out]
    assert scores == sorted(scores, reverse=True)

@pytest.mark.asyncio
async def test_retrieve_international():
    vec = [0.1]*384
    out = await retrieve_all(vec, Jurisdiction.INTERNATIONAL, top_k_each=2)
    assert len(out) > 0
