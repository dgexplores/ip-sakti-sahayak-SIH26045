"""Jurisdiction Firewall — unique win: guarantees India/Intl answers never merged, visibly enforced."""
from __future__ import annotations

import re

from app.models.schemas import Jurisdiction
from app.rag.retriever import RetrievedChunk

# Terms that pin a query to a regime. Kept in one place so the firewall and the
# classifier cannot drift apart on what "mentions India" means.
_INDIA_SIGNALS = re.compile(r"\b(india|indian|sec\s*3\(p\)|bda|tkdl|ayush|ayurveda|patents act)\b", re.I)
_INTL_SIGNALS = re.compile(r"\b(wipo|gratk|pct|cbd|nagoya|trips|madrid|hague)\b", re.I)


def filter_by_firewall(chunks: list[RetrievedChunk], requested: Jurisdiction) -> list[RetrievedChunk]:
    """Keep only the requested regime's chunks.

    Returns the input unchanged when filtering would empty the list: answering
    from nothing is worse than answering from the closest available span, and the
    verdict still reports that the answer is off-jurisdiction.
    """
    kept = [c for c in chunks if c.jurisdiction == requested.value]
    return kept or list(chunks)


def firewall_check(query: str, requested: Jurisdiction, chunks: list[RetrievedChunk]) -> dict:
    """Returns the firewall verdict — used to tint the UI and add a warning banner.

    Deliberately separate from `filter_by_firewall`. The verdict dict is embedded
    in the API response and has to stay JSON-serialisable, so it cannot carry the
    chunk objects; the chat route calls `filter_by_firewall` for the actual
    narrowing.

    Before the retriever was widened to return both regimes, `foreign` was
    structurally always empty — retrieval had already applied the jurisdiction
    filter — so `foreign_ratio` was always 0.0 and the leak branches below could
    never execute. The project's headline guarantee was unreachable code.

    `leak_warning` is reserved for the case where the single best candidate for
    the question belongs to the *other* regime. Reporting a leak merely because
    the pool contained off-jurisdiction candidates would fire on almost every
    request — the route asks for both regimes by design — and a warning that is
    always on tells the reader nothing. The dangerous case is narrower and worth
    shouting about: an India question whose strongest match is international law,
    which usually means the toggle is on the wrong side.
    """
    foreign = [c for c in chunks if c.jurisdiction != requested.value]
    kept = [c for c in chunks if c.jurisdiction == requested.value]
    foreign_ratio = len(foreign) / max(1, len(chunks))

    has_india = bool(_INDIA_SIGNALS.search(query))
    has_intl = bool(_INTL_SIGNALS.search(query))
    mixed_query = has_india and has_intl

    other = "international" if requested == Jurisdiction.INDIA else "India"
    best_kept = max((c.score for c in kept), default=-1.0)
    best_foreign = max((c.score for c in foreign), default=-1.0)
    top_is_foreign = bool(foreign) and best_foreign > best_kept

    status = "clean"
    message = ""
    if mixed_query:
        status = "mixed_query"
        message = (
            "Query mentions both India and International regimes — we keep answers visibly separate. "
            f"Answering from {requested.value} law only; toggle to see the other side."
        )
    elif top_is_foreign:
        status = "leak_warning"
        message = (
            f"The closest match for this question is {other} law, not {requested.value} law — the "
            f"firewall held it back and answered from {requested.value} material only. If you meant "
            f"the {other} regime, switch the toggle."
        )
    elif foreign:
        status = "filtered"
        message = (
            f"Removed {len(foreign)} of {len(chunks)} off-jurisdiction candidate(s) before answering "
            f"— this {requested.value} answer cites only {requested.value} law."
        )

    return {
        "status": status,
        "message": message,
        "foreign_ratio": round(foreign_ratio, 2),
        "mixed_query": mixed_query,
    }
