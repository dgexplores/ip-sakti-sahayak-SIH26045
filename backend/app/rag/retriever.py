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


# ── Vector backend readiness ──────────────────────────
#
# Why this exists: the chat route embedded every query before calling the
# retriever, and the retriever then discovered whether the database was reachable.
# On the offline path — the default, and the one the README advertises as "zero
# setup" — that embedding was computed, loaded an ~80MB sentence-transformer, and
# was never read, because `_offline_search` scores lexically. The README even
# documents the symptom ("First question is slow. The MiniLM embedding model loads
# on the first request") without connecting it to the cause.
#
# A negative result is cached only briefly, because in Docker Compose the backend
# can start before Postgres accepts connections; caching "unreachable" for the
# life of the process would silently pin a correctly-configured deployment to the
# lexical path forever.
_PROBE_TTL_SECONDS = 30.0
_probe_cache: tuple[float, bool] | None = None


def _dsn_hostport(dsn: str) -> tuple[str, int]:
    from urllib.parse import urlparse

    parsed = urlparse(dsn.replace("postgresql+psycopg://", "postgresql://"))
    return parsed.hostname or "localhost", parsed.port or 5432


def _tcp_reachable(host: str, port: int, timeout: float = 0.25) -> bool:
    import socket

    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _vector_backend_reachable() -> bool:
    """Whether the configured vector store can actually be connected to."""
    global _probe_cache
    import time

    now = time.monotonic()
    if _probe_cache is not None:
        checked_at, reachable = _probe_cache
        if reachable or (now - checked_at) < _PROBE_TTL_SECONDS:
            return reachable

    s = get_settings()
    if not s.database_url:
        reachable = False
    elif s.vector_store == "qdrant":
        reachable = _tcp_reachable(*_dsn_hostport(s.qdrant_url))
    else:
        reachable = _tcp_reachable(*_dsn_hostport(s.database_url))

    _probe_cache = (now, reachable)
    return reachable


def reset_vector_probe_cache() -> None:
    """Clear the cached probe. Used by tests, and after a config change."""
    global _probe_cache
    _probe_cache = None


async def _embed_query(query: str) -> list[float]:
    from app.pipelines.ingest.embedder import get_embedder

    return (await get_embedder().embed([query]))[0]


# ── Vector search helper (shared) ─────────────────────
async def _vector_search(query_embedding: list[float] | None, jurisdiction: Jurisdiction | None, source_filter: str | None, top_k: int, query: str = "") -> list[RetrievedChunk]:
    """Search one source-type pool. `jurisdiction=None` searches both regimes.

    `query_embedding=None` means "embed it if you need it". The offline path never
    needs it, so passing None is what keeps a keyword-only deployment from loading
    an embedding model at all.

    The chat route deliberately asks for both regimes and lets the firewall narrow
    the result, so that the firewall is doing real work rather than restating a
    filter the retriever already applied.
    """
    s = get_settings()
    if not s.database_url or not _vector_backend_reachable():
        return _offline_search(jurisdiction, source_filter, top_k, query)

    if s.vector_store == "qdrant":
        try:
            emb = query_embedding if query_embedding is not None else await _embed_query(query)
            return await _qdrant_search(emb, jurisdiction, source_filter, top_k)
        except Exception as e:
            _log_retrieval_fallback("qdrant", e)
            return _offline_search(jurisdiction, source_filter, top_k, query)
    # pgvector: connection/query failures (DB offline, table missing) fall back to
    # the offline corpus index inside _pgvector_search itself, keeping the demo
    # alive without a DB.
    return await _pgvector_search(query_embedding, jurisdiction, source_filter, top_k, query)


def _log_retrieval_fallback(backend: str, exc: Exception) -> None:
    """A silent fallback hides a dead semantic index behind slightly worse answers."""
    from app.core.logging import get_logger

    get_logger("retriever").warning("retrieval.fallback", backend=backend, error=str(exc))


async def _pgvector_search(emb: list[float] | None, jurisdiction: Jurisdiction | None, source_filter: str | None, top_k: int, query: str = "") -> list[RetrievedChunk]:
    s = get_settings()
    dsn = s.database_url.replace("postgresql+psycopg://", "postgresql://")
    # synchronous — called via to_thread
    import anyio

    # Embed only now that we know the backend is reachable.
    if emb is None:
        emb = await _embed_query(query)

    def _run() -> list[RetrievedChunk]:
        # Imported inside the call so a missing driver degrades to the offline
        # path instead of raising out of retrieve_all and 500-ing the request.
        import psycopg  # type: ignore[import]

        with psycopg.connect(dsn) as conn:
            with conn.cursor() as cur:
                # cosine distance: 1 - cosine similarity; pgvector <#> = cosine distance
                clauses: list[str] = []
                params: list = []
                if jurisdiction is not None:
                    clauses.append("jurisdiction = %s")
                    params.append(jurisdiction.value)
                if source_filter:
                    clauses.append("source_type = %s")
                    params.append(source_filter)
                where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
                cur.execute(
                    f"""
                    SELECT id, doc_id, doc_title, source_type, jurisdiction, text, locator, deep_link, version_hash,
                           1 - (embedding <=> %s::vector) AS score
                    FROM corpus_chunks
                    {where}
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (str(emb), *params, str(emb), top_k),
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
    except Exception as e:
        _log_retrieval_fallback("pgvector", e)
        return _offline_search(jurisdiction, source_filter, top_k, query)


async def _qdrant_search(emb: list[float] | None, jurisdiction: Jurisdiction | None, source_filter: str | None, top_k: int) -> list[RetrievedChunk]:
    from qdrant_client import QdrantClient  # type: ignore[import]
    from qdrant_client.models import FieldCondition, Filter, MatchValue  # type: ignore[import]

    s = get_settings()
    client = QdrantClient(url=s.qdrant_url)
    must = []
    if jurisdiction is not None:
        must.append(FieldCondition(key="jurisdiction", match=MatchValue(value=jurisdiction.value)))
    if source_filter:
        must.append(FieldCondition(key="source_type", match=MatchValue(value=source_filter)))
    flt = Filter(must=must) if must else None
    res = client.search(collection_name=s.qdrant_collection, query_vector=emb, query_filter=flt, limit=top_k)
    return [
        RetrievedChunk(
            id=p.payload.get("id", str(p.id)),  # type: ignore[union-attr]
            doc_id=p.payload.get("doc_id", ""),  # type: ignore[union-attr]
            doc_title=p.payload.get("doc_title", ""),  # type: ignore[union-attr]
            source_type=p.payload.get("source_type", "statute"),  # type: ignore[union-attr]
            jurisdiction=p.payload.get("jurisdiction", ""),  # type: ignore[union-attr]
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
#
# The list has to be broad, because a *missing* function word is not neutral: it
# gets an IDF weight like any other term, and in a 2,700-word corpus a word like
# "like" is rare enough to look discriminating. "What will the weather be like in
# Paris tomorrow?" retrieved the Drugs & Cosmetics Act at relevance 0.49 — the
# whole match was the word "like" — and the confidence gate then answered a
# weather question from the drugs statute.
_STOPWORDS = frozenset(
    """a about above after again against all also am an and any are as at be
    because been before being below between both but by can could did do does
    doing down during each few for from further had has have he her here hers
    him his how i if in into is it its just like me more most much must my no
    nor not now of off on once only or other our out over own same she should
    so some such than that the their them then there these they this those
    through to too under until up us very was we were what when where which
    while who why will with would you your""".split()
)

# How many of the question's terms have to exist somewhere in the corpus before
# the offline lexical retriever treats the question as answerable at all.
#
# Measured over the golden set: every out-of-scope question matches at most one
# term anywhere in the corpus ("like" for the weather question, "good" for the
# restaurant one, nothing at all for the rest), while every in-scope question
# matches at least two. A question whose vocabulary is essentially absent from the
# corpus cannot be grounded in it, and reporting relevance 0 for it is more honest
# than letting one stray function word carry a score. Applies only to this lexical
# path — a real embedding would make the same judgement from the vectors.
_MIN_CORPUS_TERMS = 2


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


# Field boosting: a term in the document title is stronger evidence than the
# same term in the body. A document titled "Patents Act" is *about* patents,
# whereas the Designs Act only mentions the word to say a formulation's recipe
# falls outside it. Those neighbouring-concept sentences are what a corpus needs
# to disambiguate itself for a reader, and they are exactly what misleads a
# body-only match, so the title has to count for more.
#
# Expressed as a fraction added to term coverage, not as a multiplier. As a
# multiplier it interacted with the normalising denominator so badly that every
# score was squeezed into a narrow band with a hard floor, which is what made
# the confidence gate unreachable (see _relevance below).
_TITLE_BOOST = 0.30


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


def _offline_search(
    jurisdiction: Jurisdiction | None,
    source_filter: str | None,
    top_k: int,
    query: str = "",
) -> list[RetrievedChunk]:
    """Offline retrieval over the real corpus. Keeps the demo honest with no DB/keys.

    Scored lexically rather than by vector: deterministic, needs no model, and
    the reranker already uses the same approach as its own final fallback.

    Renamed from `_mock_chunks`. The old name was actively misleading: nothing
    here is mocked, and it is the default retrieval path, so a reader had to open
    the body to find out whether the offline answers were real. They are — every
    chunk comes from `_offline_index()`, which is built from `corpus/`.

    `jurisdiction=None` returns candidates from both regimes. The chat route asks
    for that so the jurisdiction firewall has something real to filter — a
    firewall is only meaningful if contamination can actually reach it.
    """
    import re

    pool = [
        c for c in _offline_index()
        if jurisdiction is None or c.jurisdiction == jurisdiction.value
    ]
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
        # No usable query terms, so relevance is genuinely unknown. Report a true
        # zero rather than a comfortable default; the confidence gate then
        # abstains, which is the correct outcome for "asdfgh".
        return [RetrievedChunk(**{**c.__dict__, "score": 0.0}) for c in pool[:top_k]]

    idf = _idf()
    # Does the question share any vocabulary with the corpus at all? If not, the
    # question is out of the corpus's scope and no chunk can ground an answer.
    # Checked before scoring so that a single stray function word cannot produce a
    # confident-looking match.
    if sum(1 for t in q_terms if t in idf) < _MIN_CORPUS_TERMS:
        return [RetrievedChunk(**{**c.__dict__, "score": 0.0}) for c in pool[:top_k]]

    weights = {t: idf.get(t, 1.0) for t in q_terms}
    q_total = sum(weights.values()) or 1.0

    def _relevance(c: RetrievedChunk) -> float:
        """IDF-weighted fraction of the query this chunk covers, plus a title boost.

        This replaces a formula that compressed every result into [0.62, 0.95]
        with a hardcoded floor. Two consequences of that floor: a chunk sharing
        *no* term with the query still scored 0.62, and the confidence gate
        (which maps relevance onto 0-100) needed ~0.86 to clear its threshold,
        which almost nothing reached. The flagship demo question therefore
        abstained. An honest 0..1 coverage scale fixes both ends.
        """
        hit = q_terms & _chunk_terms(c)
        title_hit = q_terms & _title_terms(c)
        # A term the corpus uses everywhere ("india") carries little weight; a
        # rare discriminating term ("churna") carries a lot.
        coverage = sum(weights[t] for t in hit) / q_total
        title_coverage = sum(weights[t] for t in title_hit) / q_total
        return min(1.0, coverage + _TITLE_BOOST * title_coverage)

    scored = sorted(((_relevance(c), c) for c in pool), key=lambda t: t[0], reverse=True)
    return [
        RetrievedChunk(**{**c.__dict__, "score": round(rel, 4)})
        for rel, c in scored[:top_k]
    ]


# ── retrievers (public) ───────────────────────────────
async def statute_retriever(emb: list[float] | None, jurisdiction: Jurisdiction | None, top_k: int = 8, query: str = "") -> list[RetrievedChunk]:
    return await _vector_search(emb, jurisdiction, source_filter="statute", top_k=top_k, query=query)


async def tkdl_retriever(emb: list[float] | None, jurisdiction: Jurisdiction | None, top_k: int = 6, query: str = "") -> list[RetrievedChunk]:
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


async def registry_retriever(emb: list[float] | None, jurisdiction: Jurisdiction | None, top_k: int = 6, query: str = "") -> list[RetrievedChunk]:
    return await _vector_search(emb, jurisdiction, source_filter="registry", top_k=top_k, query=query)


async def case_law_retriever(emb: list[float] | None, jurisdiction: Jurisdiction | None, top_k: int = 6, query: str = "") -> list[RetrievedChunk]:
    return await _vector_search(emb, jurisdiction, source_filter="case_law", top_k=top_k, query=query)


async def rule_treaty_retriever(emb: list[float] | None, jurisdiction: Jurisdiction | None, top_k: int = 6, query: str = "") -> list[RetrievedChunk]:
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


# Which documents actually answer which kind of question.
#
# The classifier already decides the IP type, so the retriever can use that
# rather than re-deriving it from keyword soup. Kept as a modest additive boost
# so it reorders near-ties and cannot override a strong lexical match. The
# reranker reads the same table for its presentation ordering, so the two cannot
# disagree about which documents are canonical for a type.
IP_TYPE_DOCS: dict[str, frozenset[str]] = {
    # GRATK belongs to patents as well as to ABS: it is the disclosure-of-origin
    # requirement attached to a patent application, so a question about GRATK is a
    # patent question. Leaving it out of this set demoted its own treaty document
    # — the best match at 0.80 — behind patent documents scoring 0.28.
    "patent": frozenset({"patents_act_1970", "patents_rules_2024", "pct_system", "tkdl_guidelines", "case_law_international", "wipo_gratk_2024"}),
    "gi": frozenset({"gi_act_1999", "inpass_gi_registry_guide", "trips_agreement"}),
    "trademark": frozenset({"trade_marks_act_1999", "madrid_hague_budapest"}),
    "copyright": frozenset({"copyright_act_1957"}),
    "design": frozenset({"designs_act_2000", "madrid_hague_budapest"}),
    "trade_secret": frozenset({"trade_secrets_india"}),
    "plant_variety": frozenset({"ppvfr_act_2001", "bda_2023"}),
    "abs": frozenset({"bda_2023", "cbd_nagoya", "case_law_india", "wipo_gratk_2024"}),
    "regulatory": frozenset({"fssai_aahar_2022", "drugs_cosmetics_act", "magic_remedies_act", "ayurveda_pharmacopoeia", "export_market_access"}),
}
_IP_TYPE_BOOST = 0.15


async def retrieve_all(emb: list[float] | None, jurisdiction: Jurisdiction | None, top_k_each: int = 8, query: str = "", ip_type: str | None = None) -> list[RetrievedChunk]:
    """Parallel fan-out — LangGraph node in stage 2, simple asyncio.gather in MVP.

    Pass `jurisdiction=None` to gather candidates from both regimes. The chat
    route does that on purpose: it retrieves across the whole corpus and lets
    `firewall_check` narrow the result, which is the only arrangement in which
    the firewall does anything. Filtering here as well made the firewall's leak
    branches unreachable — `foreign_ratio` was structurally always 0.0, so the
    project's headline guarantee could never be observed working.

    `ip_type` is the classifier's verdict on what kind of question this is, and
    it nudges the matching corpus up the ranking. Without it, "Can I patent my
    grandmother's churna recipe?" was answered from the Trade Marks Act, because
    that document happens to contain the word "recipe" and this corpus is far too
    small for the word "patent" to dominate on its own.
    """
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

    if ip_type:
        preferred = IP_TYPE_DOCS.get(ip_type, frozenset())
        if preferred:
            seen = {
                cid: RetrievedChunk(**{**c.__dict__, "score": round(min(1.0, c.score + _IP_TYPE_BOOST), 4)})
                if c.doc_id in preferred else c
                for cid, c in seen.items()
            }

    merged = sorted(seen.values(), key=lambda x: x.score, reverse=True)
    return merged


def to_citations(chunks: list[RetrievedChunk]) -> list[Citation]:
    # Full chunk text, never truncated: the generator quotes from c.text, so a
    # [:400] cut let answers cite sentences the shown citation does not contain
    # (measured live: a real Sec 2(1)(j) line past the cut). True text, but
    # unverifiable in the UI. Chunks are ≤800 tokens by construction.
    return [
        Citation(
            id=f"cite_{c.id}",
            source_type=c.source_type,  # type: ignore[arg-type]
            title=c.doc_title,
            span_text=c.text,
            deep_link=c.deep_link,
            locator=c.locator,
            version_hash=c.version_hash,
        )
        for c in chunks
    ]
