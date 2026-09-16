"""Confidence — heuristic truthful, not over-confident. Abstention gate."""
from __future__ import annotations

from app.models.schemas import Confidence
from app.rag.retriever import RetrievedChunk

# Shape of the relevance → confidence curve.
#
# Every retriever reports an absolute 0..1 relevance where 0 means the chunk
# shares no term with the query. That value is honest but it is not linear in
# trustworthiness: a chunk covering a third of the question's discriminating
# terms is far more than a third of the way to a grounded answer. Raising
# relevance to a sub-1 exponent stretches the low end, so the score keeps
# resolution where the decision is actually being made instead of collapsing
# everything above the mid-point onto 96.
#
# The curve is deliberately the *same* for both retrieval backends. Offline
# lexical relevance and pgvector cosine similarity sit on different scales, but
# both are 0..1 with 0 meaning "unrelated", so one curve avoids maintaining two
# calibrations that silently drift apart.
_RELEVANCE_EXPONENT = 0.65


def compute_confidence(chunks: list[RetrievedChunk], has_abstention_signal: bool = False) -> Confidence:
    if not chunks:
        return Confidence(score=12, rationale="No grounding chunks found — abstaining.", abstain=True)
    if has_abstention_signal:
        return Confidence(score=45, rationale="Jurisdiction mixed or classification uncertain — needs clarification.", abstain=True)

    top = chunks[0].score if chunks else 0
    relevance = max(0.0, min(1.0, top))
    if relevance <= 0.0:
        # Zero relevance means no retrieved span shares a term with the question.
        # There is no grounding to be diverse about, so the grounding-quality
        # bonuses below do not apply — awarding them here would turn "we found
        # three irrelevant source types" into a double-digit score.
        return Confidence(
            score=5,
            rationale="No retrieved span shares a term with the question — nothing to ground an answer in.",
            abstain=True,
        )
    base = relevance ** _RELEVANCE_EXPONENT
    # reward a spread of source types — a statute plus a registry plus a treaty
    # is better grounded than three chunks of the same document
    diversity = len({c.source_type for c in chunks})
    diversity_bonus = min(0.15, (diversity - 1) * 0.07)
    # penalize low-k
    k_penalty = 0 if len(chunks) >= 3 else -0.20
    raw = (base + diversity_bonus + k_penalty) * 100
    score = max(5, min(96, round(raw, 1)))
    # never claim 100
    if score > 96:
        score = 96

    from app.core.config import get_settings

    threshold = get_settings().confidence_threshold * 100
    abstain = score < threshold
    rationale = (
        f"Top relevance {top:.2f} over {len(chunks)} chunks, {diversity} source type(s). "
        + ("Below threshold — abstaining." if abstain else "Grounded in statute/registry spans.")
    )
    return Confidence(score=float(score), rationale=rationale, abstain=abstain)
