"""Calibration tests for the abstention gate.

These pin the *behaviour* of the gate, not just its arithmetic. The old suite
asserted `c.abstain is True or c.score < 70`, which is true for almost any input
and therefore could not fail — it named a behaviour it never checked.
"""
from app.rag.confidence import compute_confidence
from app.rag.retriever import RetrievedChunk


def _c(score=0.9, source="statute", doc_id="c1"):
    return RetrievedChunk(
        id=doc_id, doc_id=doc_id, doc_title="T", source_type=source, jurisdiction="india",
        text="t", locator="l", deep_link="http://x", version_hash="a", score=score,
    )


def _spread(top: float) -> list[RetrievedChunk]:
    """Three chunks across three source types, so only the top score varies."""
    return [_c(top, "statute", "a"), _c(top * 0.95, "registry", "b"), _c(top * 0.9, "treaty", "c")]


def test_abstain_no_chunks():
    c = compute_confidence([], has_abstention_signal=False)
    assert c.abstain is True
    assert c.score == 12


def test_abstain_signal():
    c = compute_confidence([_c()], has_abstention_signal=True)
    assert c.abstain is True


def test_high_confidence_answers():
    c = compute_confidence(_spread(0.92))
    assert c.score > 70
    assert c.abstain is False


def test_measured_in_scope_floor_answers():
    """The weakest in-scope question measured on this corpus must not abstain.

    The gate was previously 0.70 against a relevance scale whose ceiling was
    ~0.95, so it demanded a relevance almost no real question reached and the
    flagship demo question abstained at confidence 24.7. The relevance value here
    is the measured floor of the in-scope band, not a chosen constant.
    """
    c = compute_confidence(_spread(0.44))
    assert c.score >= 70, c.score
    assert c.abstain is False


def test_measured_out_of_scope_ceiling_abstains():
    """The best out-of-scope question measured on this corpus must abstain.

    0.08 is the measured ceiling of the out-of-scope band — the closest an
    unrelated question got to the corpus.
    """
    c = compute_confidence(_spread(0.08))
    assert c.score < 45, c.score
    assert c.abstain is True


def test_gate_sits_between_the_two_bands():
    """The separation is the whole justification for the threshold value.

    `confidence_threshold` is 0.45 because it falls inside this gap. If a change
    ever narrows the gap to the point where the gate is no longer inside it, the
    threshold has to be re-measured rather than assumed.
    """
    in_scope = compute_confidence(_spread(0.44)).score
    out_of_scope = compute_confidence(_spread(0.08)).score
    assert out_of_scope < 45 <= in_scope
    assert in_scope - out_of_scope >= 25


def test_no_shared_terms_relevance_abstains():
    """A chunk sharing nothing with the query scores 0.0, not a comfortable floor.

    The offline retriever used to hardcode `0.62 + (raw / ceiling) * 0.33`, so a
    chunk with zero term overlap still scored 0.62 and looked like a match.
    """
    c = compute_confidence(_spread(0.0))
    assert c.abstain is True


def test_low_k_is_penalised():
    """One chunk is weaker grounding than three, and the score must say so."""
    one = compute_confidence([_c(0.8, "statute", "a")])
    three = compute_confidence(_spread(0.8))
    assert one.score < three.score


def test_never_100():
    c = compute_confidence([_c(0.99), _c(0.99), _c(0.99)])
    assert c.score <= 96
