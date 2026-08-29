"""SQLModel tables — minimal for MVP; pgvector via raw SQL where needed."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, String
from sqlmodel import Field, SQLModel

# pgvector type is registered via `pgvector.sqlalchemy.Vector` at runtime
try:
    from pgvector.sqlalchemy import Vector  # type: ignore[import]

    _vector = Vector  # noqa: N816
except Exception:  # local dev without pgvector installed
    _vector = None  # type: ignore[assignment]


class CorpusChunk(SQLModel, table=True):
    __tablename__ = "corpus_chunks"  # type: ignore[assignment]

    id: str = Field(primary_key=True, description="doc_id#chunk_id")
    doc_id: str = Field(index=True)
    doc_title: str
    source_type: str
    jurisdiction: str
    chunk_index: int
    text: str
    locator: str  # e.g., "Sec 3(p) — p.4"
    deep_link: str = ""
    version_hash: str = ""
    sha256: str = ""
    # embedding stored as pgvector when available; else fallback JSON
    # declared dynamically so model import never crashes
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"  # type: ignore[assignment]

    event_id: str = Field(primary_key=True)
    session_id: str = Field(index=True)
    query: str
    jurisdiction: str
    citation_ids: str = Field(default="[]")  # JSON array
    confidence: float = 0
    corpus_version: str = ""
    consent_id: Optional[str] = Field(default=None)
    paid_db_accessed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EscalationTicket(SQLModel, table=True):
    __tablename__ = "escalation_tickets"  # type: ignore[assignment]

    ticket_id: str = Field(primary_key=True)
    session_id: str = Field(index=True)
    query: str
    jurisdiction: str
    reason: str
    trace_json: str = Field(default="{}")
    consent_id: Optional[str] = None
    status: str = Field(default="open")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
