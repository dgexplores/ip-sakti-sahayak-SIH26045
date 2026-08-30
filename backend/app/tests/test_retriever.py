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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query,jurisdiction,expect_doc_id",
    [
        ("trademark brand name registration", Jurisdiction.INDIA, "trade_marks_act_1999"),
        ("copyright textbook compilation", Jurisdiction.INDIA, "copyright_act_1957"),
        ("trade secret confidential recipe NDA", Jurisdiction.INDIA, "trade_secrets_india"),
        ("design packaging bottle ornamental", Jurisdiction.INDIA, "designs_act_2000"),
        ("Divya Pharmacy benefit sharing Indian entity", Jurisdiction.INDIA, "case_law_india"),
        ("turmeric neem patent revocation prior art", Jurisdiction.INTERNATIONAL, "case_law_international"),
        ("EU THMPD DSHEA export market herbal", Jurisdiction.INTERNATIONAL, "export_market_access"),
    ],
)
async def test_offline_path_serves_the_real_corpus(query, jurisdiction, expect_doc_id):
    """The no-DB path must retrieve from corpus/, not a hardcoded span list.

    It used to return one of five hardcoded chunks, so every document added
    after that list was written was unreachable whenever Postgres was down,
    which is the default demo path. A trademark or case-law question was then
    answered from the Patents Act and TKDL at high confidence: a wrong
    citation stated confidently, the exact failure this project exists to stop.
    """
    out = await retrieve_all([0.0] * 384, jurisdiction, top_k_each=7, query=query)
    assert out, f"no chunks retrieved for {query!r}"
    assert out[0].doc_id == expect_doc_id, f"{query!r} -> {out[0].doc_id}"
    assert all(c.jurisdiction == jurisdiction.value for c in out), "jurisdiction leak"
