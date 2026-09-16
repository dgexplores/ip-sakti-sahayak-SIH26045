import pytest

from app.models.schemas import IPType
from app.rag.reranker import _blend, _lexical_rerank, order_by_ip_type, rerank
from app.rag.retriever import RetrievedChunk


def _c(id, text, score=0.8, doc_id=None):
    return RetrievedChunk(
        id=id, doc_id=doc_id or id, doc_title="T", source_type="statute", jurisdiction="india",
        text=text, locator="loc", deep_link="http://x", version_hash="a", score=score,
    )


@pytest.mark.asyncio
async def test_rerank_empty():
    assert await rerank("q", [], top_k=5) == []


def test_lexical_rerank_prefers_overlap_over_vector_score():
    """High vector score with no lexical overlap must lose to lower score with overlap.

    Tested against `_lexical_rerank` directly rather than through `rerank`, so the
    assertion does not silently become vacuous when the optional CrossEncoder is
    installed and a different code path runs. The old version of this test ended
    in `or len(ranked) == 2`, which is true whenever two chunks go in — it could
    never fail.
    """
    c1 = _c("c1", "random text about unrelated mango poem fruit", score=0.95)
    c2 = _c("c2", "Sec 3(p) traditional knowledge not patentable invention which is TK", score=0.75)
    ranked = _lexical_rerank("Is classical churna patentable under Sec 3(p) traditional knowledge?", [c1, c2], top_k=2)
    assert ranked[0].id == "c2"
    assert ranked[1].id == "c1"


def test_lexical_rerank_writes_scores_back_and_stays_sorted():
    """The returned list must be sorted by its own `score` field.

    `compute_confidence` reads `chunks[0].score`. The reranker used to reorder the
    list while leaving each chunk's original score untouched, so the list was not
    sorted by the field the confidence gate read.
    """
    chunks = [_c(f"c{i}", f"Sec 3(p) text number {i}", score=0.5 + i * 0.01) for i in range(5)]
    ranked = _lexical_rerank("Sec 3(p)", chunks, top_k=5)
    scores = [c.score for c in ranked]
    assert scores == sorted(scores, reverse=True)


def test_lexical_rerank_scores_stay_in_range():
    """Weights used to sum to 1.3, which could print "Top score 1.27" at the user."""
    chunks = [_c(f"c{i}", "Sec 3(p) traditional knowledge", score=0.99) for i in range(3)]
    for c in _lexical_rerank("Sec 3(p) traditional knowledge", chunks, top_k=3):
        assert 0.0 <= c.score <= 1.0


def test_blend_is_absolute_not_min_max():
    """A uniformly bad candidate set must score badly.

    Min-max normalisation forced the best candidate to the top of the range no
    matter how irrelevant it was: eleven zero-match chunks blended to a top
    relevance of 0.785 and a confidence of 59/100.
    """
    bad = [_c(f"c{i}", "unrelated filler text", score=0.0) for i in range(5)]
    blended = _blend(bad, [-9.0, -8.5, -9.5, -8.0, -9.2], top_k=5)
    assert max(c.score for c in blended) < 0.35, [c.score for c in blended]


def test_blend_rewards_a_genuine_match():
    good = [_c("g", "Sec 3(p) traditional knowledge", score=0.9)]
    blended = _blend(good, [4.0], top_k=1)
    assert blended[0].score > 0.8


@pytest.mark.asyncio
async def test_rerank_keeps_topk():
    chunks = [_c(f"c{i}", f"text {i} Sec 3(p)", score=0.8 + i * 0.01) for i in range(10)]
    ranked = await rerank("Sec 3(p)", chunks, top_k=3)
    assert len(ranked) == 3


@pytest.mark.asyncio
async def test_rerank_stable_without_model():
    # ensures no crash when CrossEncoder is not installed
    chunks = [_c("c1", "hello world", 0.9)]
    out = await rerank("hello", chunks, top_k=1)
    assert out[0].id == "c1"


# ── IP-type presentation ordering ─────────────────────
def test_order_by_ip_type_leads_with_the_questions_own_law():
    """Lexical ranking puts a doc that shares a word above the provision that decides.

    Reproduces the flagship defect: the Trade Marks Act ranked first for a patent
    question because it contains the word "recipe", while Sec 3(p) of the Patents
    Act — which shares no content word with the query — ranked third. The
    international case law is absent here because the firewall has already removed
    it for an India request, which is the order the chat route applies.
    """
    ranked = [
        _c("a", "a classical formulation's own name", score=0.57, doc_id="trade_marks_act_1999"),
        _c("c", "an invention which in effect is traditional knowledge", score=0.28, doc_id="patents_act_1970"),
        _c("d", "food labelling and claims", score=0.25, doc_id="fssai_aahar_2022"),
    ]
    ordered = order_by_ip_type(ranked, IPType.PATENT)
    assert [c.doc_id for c in ordered] == ["patents_act_1970", "trade_marks_act_1999", "fssai_aahar_2022"]


def test_order_by_ip_type_never_drops_a_span():
    ranked = [_c(str(i), "text", doc_id=f"doc{i}") for i in range(6)]
    assert len(order_by_ip_type(ranked, IPType.PATENT)) == len(ranked)


def test_order_by_ip_type_is_a_noop_for_unknown():
    ranked = [_c("a", "x", doc_id="trade_marks_act_1999"), _c("b", "y", doc_id="patents_act_1970")]
    assert [c.doc_id for c in order_by_ip_type(ranked, IPType.UNKNOWN)] == ["trade_marks_act_1999", "patents_act_1970"]
    assert [c.doc_id for c in order_by_ip_type(ranked, None)] == ["trade_marks_act_1999", "patents_act_1970"]


def test_order_by_ip_type_falls_back_when_no_type_docs_retrieved():
    """If the classifier's documents were not retrieved, keep the ranking as-is."""
    ranked = [_c("a", "x", doc_id="trade_marks_act_1999"), _c("b", "y", doc_id="fssai_aahar_2022")]
    assert [c.doc_id for c in order_by_ip_type(ranked, IPType.COPYRIGHT)] == ["trade_marks_act_1999", "fssai_aahar_2022"]
