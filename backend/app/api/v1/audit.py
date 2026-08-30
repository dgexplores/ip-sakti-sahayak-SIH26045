from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.logging import get_logger
from app.models.schemas import EscalateRequest, EscalateResponse
from app.services.audit import audit_logger

router = APIRouter()
logger = get_logger("audit_api")


@router.post("/escalate", response_model=EscalateResponse)
async def escalate(req: EscalateRequest) -> EscalateResponse:
    ticket_id = f"tick_{uuid.uuid4().hex[:10]}"
    trace = {
        "query": req.query,
        "jurisdiction": req.jurisdiction.value,
        "reason": req.reason,
        "citations": [c.model_dump() for c in req.citations],
        "consent_id": req.consent_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await audit_logger.log_escalation(ticket_id, req.session_id, trace)
    return EscalateResponse(ticket_id=ticket_id)


@router.get("/audit/{session_id}")
async def get_audit(session_id: str) -> dict:
    """Best-effort read of a session's audit trail. Returns empty when the DB is offline."""
    import anyio

    def _read() -> list[dict]:
        import json
        import psycopg

        from app.core.config import get_settings

        dsn = get_settings().database_url.replace("postgresql+psycopg://", "postgresql://")
        with psycopg.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT event_id, query, jurisdiction, citation_ids, confidence, corpus_version, created_at "
                    "FROM audit_logs WHERE session_id=%s ORDER BY created_at DESC LIMIT 20",
                    (session_id,),
                )
                rows = cur.fetchall()
                return [
                    {
                        "event_id": r[0], "query": r[1], "jurisdiction": r[2],
                        "citation_ids": json.loads(r[3] or "[]"), "confidence": r[4],
                        "corpus_version": r[5], "created_at": str(r[6]),
                    }
                    for r in rows
                ]

    try:
        events = await anyio.to_thread.run_sync(_read)
        return {"session_id": session_id, "events": events}
    except Exception as e:
        logger.warning("audit.read_failed", session_id=session_id, error=str(e))
        return {"session_id": session_id, "events": [], "note": "audit trail unavailable right now"}
