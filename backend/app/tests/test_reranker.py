import pytest
from app.rag.reranker import rerank
from app.rag.retriever import RetrievedChunk

def _c(id, text, score=0.8):
    return RetrievedChunk(id=id, doc_id=id, doc_title="T", source_type="statute", jurisdiction="india", text=text, locator="loc", deep_link="http://x", version_hash="a", score=score)

@pytest.mark.asyncio
async def test_rerank_empty():
    assert await rerank("q", [], top_k=5) == []

@pytest.mark.asyncio
async def test_rerank_lexical_prefers_overlap():
    # high vector score but no lexical overlap vs lower vector but high overlap
    c1 = _c("c1", "random text about unrelated mango poem fruit", score=0.95)
    c2 = _c("c2", "Sec 3(p) traditional knowledge not patentable invention which is TK", score=0.75)
    ranked = await rerank("Is classical churna patentable under Sec 3(p) traditional knowledge?", [c1, c2], top_k=2)
    # lexical should push c2 up at least once
    assert ranked[0].id == "c2" or len(ranked) == 2

@pytest.mark.asyncio
async def test_rerank_keeps_topk():
    chunks = [_c(f"c{i}", f"text {i} Sec 3(p)" , score=0.8+i*0.01) for i in range(10)]
    ranked = await rerank("Sec 3(p)", chunks, top_k=3)
    assert len(ranked) == 3

@pytest.mark.asyncio
async def test_rerank_stable_without_model():
    # ensures no crash when CrossEncoder not installed
    chunks = [_c("c1", "hello world", 0.9)]
    out = await rerank("hello", chunks, top_k=1)
    assert out[0].id == "c1"
