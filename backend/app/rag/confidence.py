"""Confidence — heuristic truthful, not over-confident. Abstention gate."""
from __future__ import annotations

from app.models.schemas import Confidence
from app.rag.retriever import RetrievedChunk


def compute_confidence(chunks: list[RetrievedChunk], has_abstention_signal: bool = False) -> Confidence:
    if not chunks:
        return Confidence(score=12, rationale="No grounding chunks found — abstaining.", abstain=True)
    if has_abstention_signal:
        return Confidence(score=45, rationale="Jurisdiction mixed or classification uncertain — needs clarification.", abstain=True)

    top = chunks[0].score if chunks else 0
    # map vector score (0.7–0.95) → 0–100, dampened
    base = max(0, min(1, (top - 0.65) / 0.30))  # 0.65→0, 0.95→1
    # penalize if few sources or single source type
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
        f"Top score {top:.2f} over {len(chunks)} chunks, {diversity} source type(s). "
        + ("Below threshold — abstaining." if abstain else "Grounded in statute/registry spans.")
    )
    return Confidence(score=float(score), rationale=rationale, abstain=abstain)
