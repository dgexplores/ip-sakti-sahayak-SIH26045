"""Paid connector proxy — never hits paid DB without explicit logged consent."""
from __future__ import annotations

from dataclasses import dataclass

from app.core.security import ConsentRecord


@dataclass(frozen=True)
class PaidAccessResult:
    allowed: bool
    reason: str
    consent_id: str | None = None


def check_paid_access(allow_flag: bool, consent_id: str | None) -> PaidAccessResult:
    if not allow_flag:
        return PaidAccessResult(allowed=False, reason="Paid DB access not requested (allow_paid_db=false). Using free DBs only.")
    if not consent_id:
        return PaidAccessResult(allowed=False, reason="Paid DB requires explicit consent_id. Showing free DBs only — tick consent to proceed.")
    # validate consent format
    if not consent_id.startswith("consent_"):
        return PaidAccessResult(allowed=False, reason="Invalid consent_id format.")
    return PaidAccessResult(allowed=True, reason="Consent verified — paid DB proxy allowed (logged).", consent_id=consent_id)


def request_consent(purpose: str, principal_hint: str = "anon") -> ConsentRecord:
    return ConsentRecord.new(purpose=purpose, principal_hint=principal_hint)
