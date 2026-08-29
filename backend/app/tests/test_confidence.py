from app.rag.confidence import compute_confidence
from app.rag.retriever import RetrievedChunk

def _c(score=0.9, source="statute"):
    return RetrievedChunk(id="c1", doc_id="c1", doc_title="T", source_type=source, jurisdiction="india", text="t", locator="l", deep_link="http://x", version_hash="a", score=score)

def test_abstain_no_chunks():
    c = compute_confidence([], has_abstention_signal=False)
    assert c.abstain is True
    assert c.score == 12

def test_abstain_signal():
    c = compute_confidence([_c()], has_abstention_signal=True)
    assert c.abstain is True

def test_high_confidence():
    chunks = [_c(0.92, "statute"), _c(0.88, "registry"), _c(0.85, "treaty")]
    c = compute_confidence(chunks)
    assert c.score > 70
    assert c.abstain is False

def test_low_score_abstains():
    chunks = [_c(0.66, "statute")]
    c = compute_confidence(chunks)
    assert c.abstain is True or c.score < 70

def test_never_100():
    chunks = [_c(0.99), _c(0.99), _c(0.99)]
    c = compute_confidence(chunks)
    assert c.score <= 96
