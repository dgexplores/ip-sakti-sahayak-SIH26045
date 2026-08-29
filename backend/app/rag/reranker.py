"""Reranker — FREE-FIRST: local CrossEncoder, zero API cost. Cohere only if key present."""
from __future__ import annotations

from app.rag.retriever import RetrievedChunk

# Lazy singleton — loads ~80MB cross-encoder once, CPU-friendly
_RERANKER = None
_RERANKER_FAILED = False


def _get_cross_encoder():  # type: ignore[no-untyped-def]
    global _RERANKER, _RERANKER_FAILED
    if _RERANKER is not None:
        return _RERANKER
    if _RERANKER_FAILED:
        return None
    try:
        from sentence_transformers import CrossEncoder  # type: ignore[import]

        # ms-marco-MiniLM is MIT, 80MB, best free reranker for legal retrieval
        _RERANKER = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", max_length=512)
        return _RERANKER
    except Exception:
        _RERANKER_FAILED = True
        return None


async def rerank(query: str, chunks: list[RetrievedChunk], top_k: int = 8) -> list[RetrievedChunk]:
    if not chunks:
        return []
    # 1) Try Cohere only if key present (paid optional)
    from app.core.config import get_settings

    s = get_settings()
    if s.cohere_api_key:
        try:
            import cohere  # type: ignore[import]

            co = cohere.AsyncClient(s.cohere_api_key)
            res = await co.rerank(model="rerank-english-v3.0", query=query, documents=[c.text for c in chunks], top_n=top_k)
            return [chunks[r.index] for r in res.results]
        except Exception:
            pass

    # 2) FREE: local CrossEncoder (offline, no billing, better than pure vector sort)
    ce = _get_cross_encoder()
    if ce is not None:
        try:
            import anyio  # type: ignore[import]

            pairs = [(query, c.text) for c in chunks]

            def _score() -> list[float]:
                return ce.predict(pairs).tolist()  # type: ignore[union-attr]

            scores: list[float] = await anyio.to_thread.run_sync(_score)  # type: ignore[arg-type]
            scored = sorted(zip(chunks, scores), key=lambda x: x[1], reverse=True)
            return [c for c, _ in scored[:top_k]]
        except Exception:
            pass

    # 3) FREE fallback: TF-IDF lexical + vector hybrid (zero deps, zero cost)
    try:
        return _lexical_rerank(query, chunks, top_k)
    except Exception:
        return sorted(chunks, key=lambda c: c.score, reverse=True)[:top_k]


def _lexical_rerank(query: str, chunks: list[RetrievedChunk], top_k: int) -> list[RetrievedChunk]:
    """BM25-inspired lexical bonus — free, no model, penalizes off-topic."""
    import re
    import math

    q_terms = set(re.findall(r"\w+", query.lower()))
    # simple idf: log(N / df) approximated as 1 for MVP
    def _score(c: RetrievedChunk) -> float:
        c_terms = re.findall(r"\w+", c.text.lower())
        overlap = len(q_terms & set(c_terms))
        # lexical 0-1 + 0.7*vector score
        return (overlap / max(1, len(q_terms))) * 0.6 + c.score * 0.7

    return sorted(chunks, key=_score, reverse=True)[:top_k]
