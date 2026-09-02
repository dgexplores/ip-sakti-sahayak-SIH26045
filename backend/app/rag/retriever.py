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
async def _vector_search(query_embedding: list[float], jurisdiction: Jurisdiction, source_filter: str | None, top_k: int, query: str = "") -> list[RetrievedChunk]:
    s = get_settings()
    if not s.database_url:
        return _mock_chunks(jurisdiction, source_filter, top_k, query)

    if s.vector_store == "qdrant":
        try:
            return await _qdrant_search(query_embedding, jurisdiction, source_filter, top_k)
        except Exception:
            return _mock_chunks(jurisdiction, source_filter, top_k, query)
    # pgvector: connection/query failures (DB offline, table missing) fall back to
    # the offline corpus index inside _pgvector_search itself, keeping the demo
    # alive without a DB.
    return await _pgvector_search(query_embedding, jurisdiction, source_filter, top_k, query)


async def _pgvector_search(emb: list[float], jurisdiction: Jurisdiction, source_filter: str | None, top_k: int, query: str = "") -> list[RetrievedChunk]:
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

    # Fall back to the offline corpus index if the DB is down or the table is missing.
    try:
        return await anyio.to_thread.run_sync(_run)
    except Exception:
        return _mock_chunks(jurisdiction, source_filter, top_k, query)


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


_OFFLINE_INDEX: list[RetrievedChunk] | None = None
_IDF: dict[str, float] | None = None

# Function words carry no retrieval signal but inflate the query-term denominator.
_STOPWORDS = frozenset(
    """a an and are as at be by can could do does for from how i if in is it my
    of on or our should that the their they this to was we what when where which
    who will with would you your""".split()
)


def _build_offline_index() -> list[RetrievedChunk]:
    """Chunk the real corpus once, in memory, for the no-database path.

    This used to be a hardcoded list of five spans. It drifted badly from the
    actual corpus: every document added after it was written was invisible
    whenever Postgres was unreachable, which is the default demo path the
    README advertises as "offline, zero setup". A trademark or case-law
    question then got confidently answered from the Patents Act and TKDL,
    a wrong citation at high confidence, which is exactly the failure this
    project exists to prevent. Reading the manifest keeps corpus/ the single
    source of truth for both the DB and the offline path.
    """
    from app.core.corpus import CORPUS_DIR, corpus_documents
    from app.pipelines.ingest.chunker import chunk_text
    from app.pipelines.ingest.loader import load_file

    index: list[RetrievedChunk] = []
    for meta in corpus_documents(limit=None):
        path = CORPUS_DIR / meta.get("file", "")
        if not path.exists():
            continue
        try:
            doc = load_file(path, meta)
        except Exception:
            continue
        for chunk in chunk_text(doc.text, doc.doc_id):
            index.append(
                RetrievedChunk(
                    id=chunk.chunk_id,
                    doc_id=doc.doc_id,
                    doc_title=doc.title,
                    source_type=doc.source_type,
                    jurisdiction=doc.jurisdiction,
                    text=chunk.text,
                    locator=chunk.locator,
                    deep_link=doc.deep_link,
                    version_hash=doc.version_hash,
                    score=0.0,
                )
            )
    return index


def _offline_index() -> list[RetrievedChunk]:
    global _OFFLINE_INDEX
    if _OFFLINE_INDEX is None:
        _OFFLINE_INDEX = _build_offline_index()
    return _OFFLINE_INDEX


def _tokens(text: str) -> set[str]:
    """Lowercase word tokens, with a trailing plural stripped.

    Statute titles are plural ("Patents Act", "Designs Act") while people ask
    in the singular ("can I patent this"). Without folding the two, an exact
    match on "patent" missed the Patents Act title entirely and the Act tied
    with every other document that merely mentions the word. Applied to both
    sides, so the comparison stays symmetric.
    """
    import re

    out = set()
    for t in re.findall(r"\w+", text.lower()):
        out.add(t)
        if len(t) > 3 and t.endswith("s") and not t.endswith("ss"):
            out.add(t[:-1])
    return out


def _chunk_terms(c: RetrievedChunk) -> set[str]:
    return _tokens(f"{c.doc_title} {c.text}")


def _title_terms(c: RetrievedChunk) -> set[str]:
    return _tokens(c.doc_title)


# Standard field boosting: a term in the document title is much stronger
# evidence than the same term in the body. A document titled "Patents Act" is
# *about* patents, whereas the Designs Act only mentions the word to say a
# formulation's recipe falls outside it. Those neighbouring-concept sentences
# are what a corpus needs to disambiguate itself for a reader, and they are
# exactly what misleads a body-only match, so the title has to outweigh them.
_TITLE_BOOST = 2.5


# Devanagari and Tamil domain words mapped to the English the corpus is written
# in. The interface is in the reader's script, so they type in it, but the
# statutes are English: without this bridge a Hindi question scored near zero
# against every document and the assistant abstained on questions it holds the
# answer to. Terms are appended, never substituted, so a mixed-script question
# still matches on whatever English it already contains.
_TERM_BRIDGE = {
    # Hindi
    "पेटेंट": "patent", "पेटेन्ट": "patent",
    "नुस्खा": "formulation recipe", "नुस्खे": "formulation recipe",
    "दवा": "drug medicine", "दवाई": "drug medicine",
    "चूर्ण": "churna", "अश्वगंधा": "ashwagandha",
    "कानून": "law act", "कानूनी": "legal",
    "पौधा": "plant", "पौधे": "plant", "जड़ी": "herb",
    "अनुमति": "approval permission", "मंज़ूरी": "approval permission",
    "मंजूरी": "approval permission",
    "ट्रेडमार्क": "trademark", "ब्रांड": "brand trademark",
    "कॉपीराइट": "copyright", "किताब": "book text",
    "डिज़ाइन": "design", "डिजाइन": "design", "पैकेजिंग": "packaging",
    "पुराना": "classical traditional", "पुराने": "classical traditional",
    "पुरानी": "classical traditional",
    "नया": "novel new", "नई": "novel new", "नये": "novel new",
    "बेचना": "sell", "बेच": "sell", "निर्यात": "export",
    "विदेश": "international foreign", "भारत": "india",
    "आहार": "food aahar", "खाद्य": "food",
    "कॉस्मेटिक": "cosmetic", "सौंदर्य": "cosmetic",
    "जैव": "biological", "विविधता": "diversity",
    "गुप्त": "secret confidential", "रहस्य": "secret",
    "किसान": "farmer", "बीज": "seed variety",
    # Tamil
    "பேட்டன்ட்": "patent", "காப்புரிமை": "patent",
    "மருந்து": "formulation medicine", "சூரணம்": "churna",
    "சட்டம்": "law act", "தாவரம்": "plant", "மூலிகை": "herb",
    "அனுமதி": "approval permission",
    "வர்த்தக": "trademark", "முத்திரை": "trademark",
    "பதிப்புரிமை": "copyright", "புத்தகம்": "book text",
    "வடிவமைப்பு": "design", "பேக்கேஜிங்": "packaging",
    "பழைய": "classical traditional", "புதிய": "novel new",
    "விற்க": "sell", "ஏற்றுமதி": "export",
    "வெளிநாடு": "international foreign", "இந்தியா": "india",
    "உணவு": "food", "அழகுசாதன": "cosmetic",
    "ரகசிய": "secret confidential", "விதை": "seed variety",
}


def bridge_query(query: str) -> str:
    """Append English equivalents for Indic domain words found in the query.

    A keyword bridge, not translation. It is enough to retrieve the right
    statute, which is what the corpus can answer with. Real translation arrives
    with a Bhashini key and replaces this.
    """
    extra = [en for indic, en in _TERM_BRIDGE.items() if indic in query]
    return f"{query} {' '.join(extra)}" if extra else query


def _idf() -> dict[str, float]:
    """Inverse document frequency over the offline chunks.

    Counting matched terms equally made "india" worth as much as "patentable",
    and in a corpus that is mostly Indian law the first word separates nothing.
    "Is classical churna patentable in India?" tied four documents at the same
    score and surfaced the Plant Varieties and Designs Acts, because they happen
    to contain "classical" and "india". Weighting each term by how rare it is
    puts the discriminating word in front.
    """
    global _IDF
    if _IDF is None:
        import math
        from collections import Counter

        chunks = _offline_index()
        df: Counter[str] = Counter()
        for c in chunks:
            df.update(_chunk_terms(c))
        n = max(1, len(chunks))
        _IDF = {t: math.log(n / (1 + d)) + 1.0 for t, d in df.items()}
    return _IDF


def _mock_chunks(
    jurisdiction: Jurisdiction,
    source_filter: str | None,
    top_k: int,
    query: str = "",
) -> list[RetrievedChunk]:
    """Offline retrieval over the real corpus. Keeps the demo honest with no DB/keys.

    Scored lexically rather than by vector: deterministic, needs no model, and
    the reranker already uses the same approach as its own final fallback.
    """
    import re

    pool = [c for c in _offline_index() if c.jurisdiction == jurisdiction.value]
    if source_filter:
        pool = [c for c in pool if c.source_type == source_filter]
    if not pool:
        return []

    # Drop function words before scoring. Leaving them in dilutes the overlap
    # ratio, so "Can I copyright my Ayurveda textbook?" scored barely above an
    # unrelated chunk and the confidence gate then abstained on a correct hit.
    # Drop tokens the corpus cannot possibly contain. The statutes are English,
    # so leaving the original Devanagari or Tamil words in the denominator made
    # 71% of a Hindi question's weight dead, and every answer fell under the
    # confidence gate even when the right statute was retrieved first.
    q_terms = {t for t in _tokens(bridge_query(query)) - _STOPWORDS if t.isascii()}
    if not q_terms:
        return list(pool[:top_k])

    idf = _idf()
    weights = {t: idf.get(t, 1.0) for t in q_terms}

    def _raw(c: RetrievedChunk) -> float:
        hit = q_terms & _chunk_terms(c)
        base = sum(weights[t] for t in hit)
        in_title = sum(weights[t] for t in (q_terms & _title_terms(c)))
        return base + _TITLE_BOOST * in_title

    # Normalise against the best score this query could possibly achieve, not
    # against the best match in this pool. retrieve_all merges five separate
    # retriever pools and sorts the union, so a pool-relative score is not
    # comparable across them: the top hit of a sparse pool would tie with the
    # top hit of a rich one at 0.95 and the merge order became arbitrary. An
    # absolute denominator also removes the earlier need to clamp at 1.0, which
    # was itself collapsing distinct matches onto an identical score.
    ceiling = sum(weights.values()) * (1.0 + _TITLE_BOOST) or 1.0
    scored = sorted(((_raw(c), c) for c in pool), key=lambda t: t[0], reverse=True)
    return [
        RetrievedChunk(**{**c.__dict__, "score": round(0.62 + (raw / ceiling) * 0.33, 3)})
        for raw, c in scored[:top_k]
    ]


# ── retrievers (public) ───────────────────────────────
async def statute_retriever(emb: list[float], jurisdiction: Jurisdiction, top_k: int = 8, query: str = "") -> list[RetrievedChunk]:
    return await _vector_search(emb, jurisdiction, source_filter="statute", top_k=top_k, query=query)


async def tkdl_retriever(emb: list[float], jurisdiction: Jurisdiction, top_k: int = 6, query: str = "") -> list[RetrievedChunk]:
    """TKDL and other registry records, within the requested jurisdiction only.

    This used to inject India-jurisdiction TKDL chunks into international
    results. That worked against the jurisdiction firewall, which is the
    project's central guarantee: the firewall counted those very chunks as a
    foreign "leak" and warned about them, so the retriever was manufacturing
    the contamination the firewall then reported. The international side gets
    its TKDL context from `case_law_international` (turmeric and neem) and
    `wipo_gratk_2024`, both correctly tagged international.
    """
    return await _vector_search(emb, jurisdiction, source_filter="registry", top_k=top_k, query=query)


async def registry_retriever(emb: list[float], jurisdiction: Jurisdiction, top_k: int = 6, query: str = "") -> list[RetrievedChunk]:
    return await _vector_search(emb, jurisdiction, source_filter="registry", top_k=top_k, query=query)


async def case_law_retriever(emb: list[float], jurisdiction: Jurisdiction, top_k: int = 6, query: str = "") -> list[RetrievedChunk]:
    return await _vector_search(emb, jurisdiction, source_filter="case_law", top_k=top_k, query=query)


async def rule_treaty_retriever(emb: list[float], jurisdiction: Jurisdiction, top_k: int = 6, query: str = "") -> list[RetrievedChunk]:
    """Rules, treaties and pharmacopoeial standards.

    Without this the retrievers above only cover statute, registry and case_law,
    so rule, treaty and pharmacopoeia documents (2024 Patent Rules, FSSAI, GRATK,
    PCT, TRIPS, export-market access) could never be retrieved at all.
    """
    results = await asyncio.gather(
        _vector_search(emb, jurisdiction, source_filter="rule", top_k=top_k, query=query),
        _vector_search(emb, jurisdiction, source_filter="treaty", top_k=top_k, query=query),
        _vector_search(emb, jurisdiction, source_filter="pharmacopoeia", top_k=top_k, query=query),
    )
    return [c for lst in results for c in lst]


async def retrieve_all(emb: list[float], jurisdiction: Jurisdiction, top_k_each: int = 8, query: str = "") -> list[RetrievedChunk]:
    """Parallel fan-out — LangGraph node in stage 2, simple asyncio.gather in MVP."""
    results = await asyncio.gather(
        statute_retriever(emb, jurisdiction, top_k_each, query),
        tkdl_retriever(emb, jurisdiction, top_k_each, query),
        registry_retriever(emb, jurisdiction, top_k_each, query),
        case_law_retriever(emb, jurisdiction, top_k_each, query),
        rule_treaty_retriever(emb, jurisdiction, top_k_each, query),
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
