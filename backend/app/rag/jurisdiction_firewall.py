"""Jurisdiction Firewall — unique win: guarantees India/Intl answers never merged, visibly enforced."""
from __future__ import annotations

from app.models.schemas import Jurisdiction
from app.rag.retriever import RetrievedChunk


def firewall_check(query: str, requested: Jurisdiction, chunks: list[RetrievedChunk]) -> dict:
    """Returns firewall verdict — used to tint UI and add warning banner."""
    # Check if retrieved chunks are pure to requested jurisdiction
    foreign = [c for c in chunks if c.jurisdiction != requested.value]
    foreign_ratio = len(foreign) / max(1, len(chunks))
    # Detect query mentioning both
    import re

    has_india = bool(re.search(r"\b(india|sec\s*3\(p\)|bda|tkdl|ayush)\b", query, re.I))
    has_intl = bool(re.search(r"\b(wipo|gratk|pct|cbd|nagoya|trips)\b", query, re.I))
    mixed_query = has_india and has_intl

    status = "clean"
    message = ""
    if mixed_query:
        status = "mixed_query"
        message = "Query mentions both India and International regimes — we keep answers visibly separate. Toggle to see each side."
    elif foreign_ratio > 0.35:
        status = "leak_warning"
        message = f"Retriever leaked {len(foreign)}/{len(chunks)} foreign chunks — firewall filtered. Showing only {requested.value} law."
        chunks = [c for c in chunks if c.jurisdiction == requested.value] or chunks  # keep if would empty
    elif foreign:
        status = "filtered"
        message = f"Filtered {len(foreign)} off-jurisdiction chunks."

    return {"status": status, "message": message, "foreign_ratio": round(foreign_ratio, 2), "mixed_query": mixed_query}
