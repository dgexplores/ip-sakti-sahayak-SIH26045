import pytest
from app.rag.generator import _offline_extractive_answer, _eli5
from app.models.schemas import Jurisdiction, Confidence
from app.rag.retriever import RetrievedChunk

def _c(title="Patents Act Sec 3(p)", text="An invention which, in effect, is traditional knowledge is not patentable. Sec 3(p) bars it.", locator="Sec 3(p)", jurisdiction="india"):
    return RetrievedChunk(id="c1", doc_id="c1", doc_title=title, source_type="statute", jurisdiction=jurisdiction, text=text, locator=locator, deep_link="https://example.com", version_hash="abc123", score=0.91)

def _conf(score=85, abstain=False):
    return Confidence(score=score, rationale="grounded", abstain=abstain)

def test_offline_india_contains_banner():
    ans = _offline_extractive_answer("Is classical churna patentable?", Jurisdiction.INDIA, [_c()], _conf())
    assert "INDIA" in ans
    assert "Information only" in ans
    assert "Sec 3(p)" in ans

def test_offline_international_gratk():
    c = _c(title="WIPO GRATK 2024", text="Disclosure requirement Art 3: disclose country of origin.", locator="Art 3", jurisdiction="international")
    ans = _offline_extractive_answer("WIPO GRATK disclosure?", Jurisdiction.INTERNATIONAL, [c], _conf())
    assert "INTERNATIONAL" in ans
    assert "Art 3" in ans

def test_offline_abstain_not_called_here_but_conf():
    # generator's abstain path is in generate_answer, not offline helper
    c = _c()
    low = _conf(score=12, abstain=True)
    # offline should still produce answer; abstain handled upstream
    ans = _offline_extractive_answer("q", Jurisdiction.INDIA, [c], low)
    assert "Information only" in ans

def test_eli5_simple():
    c = _c()
    s = _eli5("Is classical churna patentable?", Jurisdiction.INDIA, [c])
    assert "Copy-paste" in s or "no patent" in s.lower()

def test_eli5_gratk():
    c = _c(title="GRATK", text="x", jurisdiction="international")
    s = _eli5("GRATK PCT?", Jurisdiction.INTERNATIONAL, [c])
    assert "permission" in s.lower() or "where it came from" in s.lower()

@pytest.mark.asyncio
async def test_generate_answer_offline_path():
    from app.rag.generator import generate_answer
    chunks = [_c(), _c(title="BDA", text="NBA approval required", locator="Sec 7", jurisdiction="india")]
    conf = _conf(score=82)
    ans = await generate_answer("Is novel extract patentable?", Jurisdiction.INDIA, chunks, conf)
    assert "INDIA" in ans
    assert "Information only" in ans

@pytest.mark.asyncio
async def test_generate_abstain_path():
    from app.rag.generator import generate_answer
    chunks = []
    conf = Confidence(score=12, rationale="no chunks", abstain=True)
    ans = await generate_answer("write a poem", Jurisdiction.INDIA, chunks, conf)
    assert "have a grounded answer" in ans  # handles ’ vs '
