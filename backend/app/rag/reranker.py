"""Reranker — FREE-FIRST: local CrossEncoder, zero API cost. Cohere only if key present."""
from __future__ import annotations

import os

from app.models.schemas import IPType
from app.rag.retriever import IP_TYPE_DOCS, RetrievedChunk

# Lazy singleton — loads ~80MB cross-encoder once, CPU-friendly
_RERANKER = None
_RERANKER_FAILED = False


def _get_cross_encoder():  # type: ignore[no-untyped-def]
    global _RERANKER, _RERANKER_FAILED
    if os.environ.get("SKIP_ML_MODELS"):
        # Same 512MB-container reason as embedder.py: fall through to the
        # zero-dep lexical rerank below. Deterministic, no download.
        return None
    if _RERANKER is not None:
        return _RERANKER
    if _RERANKER_FAILED:
        return None
    try:
        from sentence_transformers import CrossEncoder  # type: ignore[import]

        # ms-marco-MiniLM is MIT, 80MB, best free reranker for legal retrieval
        from app.pipelines.ingest.embedder import _load_cached

        _RERANKER = _load_cached(
            CrossEncoder, "cross-encoder/ms-marco-MiniLM-L-6-v2", max_length=512
        )
        return _RERANKER
    except Exception:
        _RERANKER_FAILED = True
        return None


def order_by_ip_type(chunks: list[RetrievedChunk], ip_type: IPType | None) -> list[RetrievedChunk]:
    """Present the law that answers the question first — a stable partition, not a re-score.

    Both the retriever and this reranker rank on lexical overlap, and lexical
    overlap answers "which text uses the question's words", not "which text answers
    the question". The two diverge badly on this corpus. For "Can I patent my
    grandmother's churna recipe?" the Trade Marks Act ranked first, because it
    contains the word "recipe" in a sentence about classical product names, while
    the provision that actually decides the question — Sec 3(p) of the Patents Act —
    shares no content word with the query at all and scored a third of its
    relevance. The answer then led with trademark law on a patent question.

    The classifier already knows the question is about patents, so its documents
    are moved to the front. Nothing is dropped and no score is altered: off-type
    spans keep their relative order immediately behind the on-type ones, so a
    question that genuinely spans two regimes still shows both — it just no longer
    leads with the one that was asked about second.

    Confidence is computed before this runs, on the score-ordered list, so
    reordering the presentation cannot flatter or deflate the score.
    """
    if ip_type is None or ip_type == IPType.UNKNOWN:
        return list(chunks)
    preferred = IP_TYPE_DOCS.get(ip_type.value, frozenset())
    if not preferred:
        return list(chunks)
    on_type = [c for c in chunks if c.doc_id in preferred]
    off_type = [c for c in chunks if c.doc_id not in preferred]
    # `on_type` empty means the classifier's documents were not retrieved at all;
    # returning off_type alone preserves the original order.
    return on_type + off_type


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
            return _blend(chunks, scores, top_k)
        except Exception:
            pass

    # 3) FREE fallback: TF-IDF lexical + vector hybrid (zero deps, zero cost)
    try:
        return _lexical_rerank(query, chunks, top_k)
    except Exception:
        return sorted(chunks, key=lambda c: c.score, reverse=True)[:top_k]


def _blend(chunks: list[RetrievedChunk], ce_scores: list[float], top_k: int) -> list[RetrievedChunk]:
    """Combine the retriever's score with the CrossEncoder's, and write the result back.

    Two problems this fixes. First, the reranker used to reorder the list while
    leaving each chunk's original `score` untouched, so the returned list was no
    longer sorted by score and `compute_confidence`, which reads `chunks[0]`,
    was scoring whichever chunk the reranker happened to promote. Second,
    ms-marco-MiniLM is trained on general web search, not Indian statute, and
    on its own it demoted the Patents Act to fourth for "is classical churna
    patentable", promoting the Plant Varieties Act because that text happens to
    mention Ashwagandha. Blending keeps the reranker's semantic judgement
    without letting it discard a strong retrieval signal.

    The CrossEncoder's score is squashed to 0..1 absolutely, not min-max
    normalised within the candidate set. Min-max normalisation was the bug: it
    guarantees the best candidate always lands at the top of the range no matter
    how bad it is, so a page of entirely irrelevant chunks still produced a
    confident-looking score. Eleven identical zero-match chunks blended to a
    top relevance of 0.785 and a confidence of 59/100. ms-marco is reasonably
    calibrated in absolute terms — strongly negative logits for unrelated text,
    positive for relevant — so an absolute squash preserves that signal and lets
    a bad candidate set score badly, which is the whole point of having a
    confidence gate.
    """
    import math

    blended: list[tuple[float, RetrievedChunk]] = []
    for c, raw in zip(chunks, ce_scores):
        ce_abs = 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, float(raw)))))
        score = round(0.5 * c.score + 0.5 * ce_abs, 4)
        blended.append((score, c))
    blended.sort(key=lambda t: t[0], reverse=True)
    return [RetrievedChunk(**{**c.__dict__, "score": s}) for s, c in blended[:top_k]]


def _lexical_rerank(query: str, chunks: list[RetrievedChunk], top_k: int) -> list[RetrievedChunk]:
    """BM25-inspired lexical bonus — free, no model, penalizes off-topic.

    Writes the combined score back onto each chunk, for the same reason
    `_blend` does: returning a reordered list whose chunks still carry their
    pre-rerank scores leaves the list unsorted by its own `score` field, and
    `compute_confidence` reads `chunks[0].score`. The weights sum to 1.0 so the
    result stays inside the 0..1 range the confidence mapping assumes — the
    previous pair summed to 1.3 and could print "Top score 1.27" at the user.

    Terms are bridged, stopword-dropped and ascii-filtered exactly like the
    retriever's own query terms. Scoring the rerank on raw query words while
    retrieval scores on bridged ones demoted good hits for Indic questions —
    the two stages must agree on what the question says.
    """
    from app.rag.retriever import _STOPWORDS, bridge_query

    import re

    q_terms = {t for t in set(re.findall(r"\w+", bridge_query(query).lower())) - _STOPWORDS if t.isascii()}
    if not q_terms:
        return sorted(chunks, key=lambda c: c.score, reverse=True)[:top_k]

    def _score(c: RetrievedChunk) -> float:
        c_terms = set(re.findall(r"\w+", c.text.lower()))
        overlap = len(q_terms & c_terms) / len(q_terms)
        # the retriever's absolute relevance stays dominant; lexical overlap
        # only breaks ties between candidates it already considers comparable
        return 0.75 * c.score + 0.25 * overlap

    scored = sorted(((_score(c), c) for c in chunks), key=lambda t: t[0], reverse=True)
    return [RetrievedChunk(**{**c.__dict__, "score": round(s, 4)}) for s, c in scored[:top_k]]
