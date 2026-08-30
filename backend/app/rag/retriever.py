"""Retrievers — 4 parallel sources with jurisdiction filter. Each is swappable."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass

from app.core.config import get_settings
from app.models.schemas import Citation, Jurisdiction


@dataclass(frozen=True)
class RetrievedChunk:
    id: str
    doc_id: str
    doc_title: str
    source_type: str
    jurisdiction: str
    text: str
    locator: str
    deep_link: str
    version_hash: str
    score: float


# ── Vector search helper (shared) ─────────────────────
async def _vector_search(query_embedding: list[float], jurisdiction: Jurisdiction, source_filter: str | None, top_k: int) -> list[RetrievedChunk]:
    s = get_settings()
    if not s.database_url:
        return _mock_chunks(jurisdiction, source_filter, top_k)

    if s.vector_store == "qdrant":
        try:
            return await _qdrant_search(query_embedding, jurisdiction, source_filter, top_k)
        except Exception:
            return _mock_chunks(jurisdiction, source_filter, top_k)
    # pgvector: connection/query failures (DB offline, table missing) fall back to
    # mock chunks inside _pgvector_search itself, keeping the demo alive without a DB.
    return await _pgvector_search(query_embedding, jurisdiction, source_filter, top_k)


async def _pgvector_search(emb: list[float], jurisdiction: Jurisdiction, source_filter: str | None, top_k: int) -> list[RetrievedChunk]:
    import psycopg  # type: ignore[import]

    from app.core.config import get_settings

    s = get_settings()
    dsn = s.database_url.replace("postgresql+psycopg://", "postgresql://")
    # synchronous — called via to_thread
    import anyio

    def _run() -> list[RetrievedChunk]:
        with psycopg.connect(dsn) as conn:
            with conn.cursor() as cur:
                # cosine distance: 1 - cosine similarity; pgvector <#> = cosine distance
                where = "WHERE jurisdiction = %s"
                params: list = [jurisdiction.value, str(emb)]
                if source_filter:
                    where += " AND source_type = %s"
                    params.insert(1, source_filter)
                # embedding param is last
                cur.execute(
                    f"""
                    SELECT id, doc_id, doc_title, source_type, jurisdiction, text, locator, deep_link, version_hash,
                           1 - (embedding <=> %s::vector) AS score
                    FROM corpus_chunks
                    {where}
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (str(emb), jurisdiction.value if not source_filter else jurisdiction.value, source_filter, str(emb), top_k)  # type: ignore[arg-type]
                    if source_filter
                    else (str(emb), jurisdiction.value, str(emb), top_k),
                )
                rows = cur.fetchall()
                return [
                    RetrievedChunk(
                        id=r[0], doc_id=r[1], doc_title=r[2], source_type=r[3], jurisdiction=r[4],
                        text=r[5], locator=r[6], deep_link=r[7], version_hash=r[8], score=float(r[9]),
                    )
                    for r in rows
                ]

    # Actually simpler: run sync directly if we are already in thread
    # Fallback mock if DB missing table
    try:
        return await anyio.to_thread.run_sync(_run)
    except Exception:
        return _mock_chunks(jurisdiction, source_filter, top_k)


async def _qdrant_search(emb: list[float], jurisdiction: Jurisdiction, source_filter: str | None, top_k: int) -> list[RetrievedChunk]:
    from qdrant_client import QdrantClient  # type: ignore[import]
    from qdrant_client.models import FieldCondition, Filter, MatchValue  # type: ignore[import]

    s = get_settings()
    client = QdrantClient(url=s.qdrant_url)
    must = [FieldCondition(key="jurisdiction", match=MatchValue(value=jurisdiction.value))]
    if source_filter:
        must.append(FieldCondition(key="source_type", match=MatchValue(value=source_filter)))
    flt = Filter(must=must)
    res = client.search(collection_name=s.qdrant_collection, query_vector=emb, query_filter=flt, limit=top_k)
    return [
        RetrievedChunk(
            id=p.payload.get("id", str(p.id)),  # type: ignore[union-attr]
            doc_id=p.payload.get("doc_id", ""),  # type: ignore[union-attr]
            doc_title=p.payload.get("doc_title", ""),  # type: ignore[union-attr]
            source_type=p.payload.get("source_type", "statute"),  # type: ignore[union-attr]
            jurisdiction=p.payload.get("jurisdiction", jurisdiction.value),  # type: ignore[union-attr]
            text=p.payload.get("text", ""),  # type: ignore[union-attr]
            locator=p.payload.get("locator", ""),  # type: ignore[union-attr]
            deep_link=p.payload.get("deep_link", ""),  # type: ignore[union-attr]
            version_hash=p.payload.get("version_hash", ""),  # type: ignore[union-attr]
            score=float(p.score),
        )
        for p in res
    ]


def _mock_chunks(jurisdiction: Jurisdiction, source_filter: str | None, top_k: int) -> list[RetrievedChunk]:
    """Offline mock — keeps frontend demoable with no DB/keys."""
    base = [
        ("patents_act_3p", "Patents Act, 1970 — Sec 3(p)", "statute", "india", "An invention which, in effect, is traditional knowledge or an aggregation or duplication of known properties of traditionally known component(s) — is not patentable. [Sec 3(p)]", "Sec 3(p) — p.4", "https://ipindia.gov.in/writereaddata/portal/ev/sections/ps3.html", "a1b2c3d4e5f6", 0.91),
        ("bda_2023_s7", "Biological Diversity Act, 2023 — Sec 7", "statute", "india", "Access to biological resources and associated traditional knowledge for commercial utilization requires prior intimation to SBB / approval of NBA with benefit-sharing.", "Sec 7 — p.12", "https://nbaindia.org/act2023", "a1b2c3d4e5f6", 0.88),
        ("gratk_2024_art3", "WIPO GRATK Treaty 2024 — Art 3", "treaty", "international", "Disclosure requirement: patent applicants shall disclose the origin/source of genetic resources and associated traditional knowledge where the invention is based on them.", "Art 3 — p.2", "https://www.wipo.int/treaties/en/text-gratk", "b2c3d4e5f6a1", 0.87),
        ("tkdl_pointer", "TKDL Prior-Art Pointer", "registry", "india", "TKDL must be searched before filing claims on formulations derived from codified TK; examiner may cite TKDL as prior art to reject obviousness/novelty.", "TKDL guideline — p.1", "https://www.tkdl.res.in", "c3d4e5f6a1b2", 0.82),
        ("fssai_aahar_2022", "FSSAI Ayurveda Aahar Regulations 2022", "rule", "india", "Ayurveda Aahar means food recipes described in authoritative Ayurveda texts, with permitted additives and claim restrictions under Food Safety Act.", "Reg 3(1) — p.3", "https://fssai.gov.in/aahar", "a1b2c3d4e5f6", 0.79),
    ]
    filtered = [r for r in base if r[2] == source_filter] if source_filter else base
    filtered = [r for r in filtered if r[3] == jurisdiction.value] or filtered  # fallback to any if mismatch for mock
    return [
        RetrievedChunk(id=r[0], doc_title=r[1], source_type=r[2], jurisdiction=r[3], text=r[4], locator=r[5], deep_link=r[6], version_hash=r[7], score=r[8], doc_id=r[0])
        for r in filtered[:top_k]
    ]


# ── 4 retrievers (public) ─────────────────────────────
async def statute_retriever(emb: list[float], jurisdiction: Jurisdiction, top_k: int = 8) -> list[RetrievedChunk]:
    return await _vector_search(emb, jurisdiction, source_filter="statute", top_k=top_k)


async def tkdl_retriever(emb: list[float], jurisdiction: Jurisdiction, top_k: int = 6) -> list[RetrievedChunk]:
    # TKDL is india-only; for international, return pointer
    if jurisdiction == Jurisdiction.INTERNATIONAL:
        return [c for c in _mock_chunks(jurisdiction, None, 10) if "tkdl" in c.id.lower()][:top_k]
    return await _vector_search(emb, jurisdiction, source_filter="registry", top_k=top_k)


async def registry_retriever(emb: list[float], jurisdiction: Jurisdiction, top_k: int = 6) -> list[RetrievedChunk]:
    return await _vector_search(emb, jurisdiction, source_filter="registry", top_k=top_k)


async def case_law_retriever(emb: list[float], jurisdiction: Jurisdiction, top_k: int = 6) -> list[RetrievedChunk]:
    return await _vector_search(emb, jurisdiction, source_filter="case_law", top_k=top_k)


async def retrieve_all(emb: list[float], jurisdiction: Jurisdiction, top_k_each: int = 8) -> list[RetrievedChunk]:
    """Parallel fan-out — LangGraph node in stage 2, simple asyncio.gather in MVP."""
    results = await asyncio.gather(
        statute_retriever(emb, jurisdiction, top_k_each),
        tkdl_retriever(emb, jurisdiction, top_k_each),
        registry_retriever(emb, jurisdiction, top_k_each),
        case_law_retriever(emb, jurisdiction, top_k_each),
    )
    # flatten + dedupe by id, keep highest score
    seen: dict[str, RetrievedChunk] = {}
    for lst in results:
        for c in lst:
            if c.id not in seen or c.score > seen[c.id].score:
                seen[c.id] = c
    merged = sorted(seen.values(), key=lambda x: x.score, reverse=True)
    return merged


def to_citations(chunks: list[RetrievedChunk]) -> list[Citation]:
    return [
        Citation(
            id=f"cite_{c.id}",
            source_type=c.source_type,  # type: ignore[arg-type]
            title=c.doc_title,
            span_text=c.text[:400],
            deep_link=c.deep_link,
            locator=c.locator,
            version_hash=c.version_hash,
        )
        for c in chunks
    ]
