"""Reranker — Cohere rerank when key available, else score-sort fallback."""
from __future__ import annotations

from app.core.config import get_settings
from app.rag.retriever import RetrievedChunk


async def rerank(query: str, chunks: list[RetrievedChunk], top_k: int = 8) -> list[RetrievedChunk]:
    if not chunks:
        return []
    s = get_settings()
    if s.cohere_api_key:
        try:
            import cohere  # type: ignore[import]

            co = cohere.AsyncClient(s.cohere_api_key)
            res = await co.rerank(model="rerank-english-v3.0", query=query, documents=[c.text for c in chunks], top_n=top_k)
            return [chunks[r.index] for r in res.results]
        except Exception:
            pass
    # fallback: already scored by vector similarity
    return sorted(chunks, key=lambda c: c.score, reverse=True)[:top_k]
