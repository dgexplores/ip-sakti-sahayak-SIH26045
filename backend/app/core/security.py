"""DPDP-aligned minimal security — no over-engineering."""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone

from pydantic import BaseModel


class ConsentRecord(BaseModel):
    consent_id: str
    purpose: str
    granted_at: datetime
    data_principal_id: str  # pseudonymized
    retention_days: int = 365

    @staticmethod
    def new(purpose: str, principal_hint: str = "anon") -> "ConsentRecord":
        # pseudonymize principal — never store raw identifier
        pseudonym = hashlib.sha256(principal_hint.encode()).hexdigest()[:16]
        return ConsentRecord(
            consent_id=f"consent_{uuid.uuid4().hex[:12]}",
            purpose=purpose,
            granted_at=datetime.now(timezone.utc),
            data_principal_id=pseudonym,
        )


def hash_ip(ip: str) -> str:
    return hashlib.sha256(ip.encode()).hexdigest()[:16]
