"""Audit logger — structured trace of what the system did, with the query kept for escalation.

A note on what "DPDP-aligned" does and does not mean here. The docstring used to
say "pseudonymized", which was not true of this file: `query` is stored verbatim
(capped at 500 characters) because an escalation ticket has to carry the question
to the facilitator who will answer it. The pseudonymisation lives one level up —
`ConsentRecord` hashes the data principal, and the read route returns the trace
without the query text. Storing a free-text question is not anonymous, so the
privacy notice says so rather than implying otherwise.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import structlog

from app.core.config import get_settings
from app.models.schemas import AuditEvent, Jurisdiction

logger = structlog.get_logger("audit")

# Free-text questions are personal data. Bound what is retained.
_QUERY_RETENTION_CHARS = 500


class AuditLogger:
    """Writes to DB when available, always to structured log."""

    async def log(
        self,
        session_id: str,
        query: str,
        jurisdiction: Jurisdiction,
        citation_ids: list[str],
        confidence: float,
        corpus_version: str,
        consent_id: str | None = None,
        paid_db_accessed: bool = False,
    ) -> AuditEvent:
        event = AuditEvent(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            session_id=session_id,
            query=query[:_QUERY_RETENTION_CHARS],
            jurisdiction=jurisdiction,
            citations=citation_ids,
            confidence=confidence,
            corpus_version=corpus_version,
            consent_id=consent_id,
            created_at=datetime.now(timezone.utc),
            paid_db_accessed=paid_db_accessed,
        )
        # structured log (always) — deliberately without the query text, so the
        # log stream is not a second copy of it
        logger.info(
            "audit.chat",
            event_id=event.event_id,
            session_id=session_id,
            jurisdiction=jurisdiction.value,
            citation_count=len(citation_ids),
            confidence=confidence,
            corpus_version=corpus_version,
            paid_db_accessed=paid_db_accessed,
        )
        # best-effort DB write, offloaded so it never blocks the event loop
        if get_settings().enable_audit:
            import anyio

            def _write() -> None:
                import psycopg  # type: ignore[import]

                dsn = get_settings().database_url.replace("postgresql+psycopg://", "postgresql://")
                with psycopg.connect(dsn, autocommit=True) as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            CREATE TABLE IF NOT EXISTS audit_logs (
                                event_id TEXT PRIMARY KEY, session_id TEXT, query TEXT, jurisdiction TEXT,
                                citation_ids TEXT, confidence DOUBLE PRECISION, corpus_version TEXT,
                                consent_id TEXT, paid_db_accessed BOOLEAN, created_at TIMESTAMPTZ
                            )
                            """
                        )
                        cur.execute(
                            "INSERT INTO audit_logs VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                            (
                                event.event_id,
                                event.session_id,
                                event.query,
                                event.jurisdiction.value,
                                json.dumps(event.citations),
                                event.confidence,
                                event.corpus_version,
                                event.consent_id,
                                event.paid_db_accessed,
                                event.created_at,
                            ),
                        )

            try:
                await anyio.to_thread.run_sync(_write)
            except Exception as e:
                logger.warning("audit.db_write_failed", error=str(e))
        return event

    async def log_escalation(self, ticket_id: str, session_id: str, trace: dict) -> None:
        logger.info("audit.escalate", ticket_id=ticket_id, session_id=session_id, trace_keys=list(trace.keys()))
        import anyio

        def _write() -> None:
            import psycopg  # type: ignore[import]

            dsn = get_settings().database_url.replace("postgresql+psycopg://", "postgresql://")
            with psycopg.connect(dsn, autocommit=True) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS escalation_tickets (
                            ticket_id TEXT PRIMARY KEY, session_id TEXT, query TEXT, jurisdiction TEXT,
                            reason TEXT, trace_json TEXT, consent_id TEXT, status TEXT, created_at TIMESTAMPTZ
                        )
                        """
                    )
                    cur.execute(
                        "INSERT INTO escalation_tickets VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                        (
                            ticket_id,
                            session_id,
                            trace.get("query", ""),
                            trace.get("jurisdiction", ""),
                            trace.get("reason", ""),
                            json.dumps(trace),
                            trace.get("consent_id"),
                            "open",
                            datetime.now(timezone.utc),
                        ),
                    )

        try:
            await anyio.to_thread.run_sync(_write)
        except Exception as e:
            logger.warning("audit.escalation_db_failed", error=str(e))


audit_logger = AuditLogger()
