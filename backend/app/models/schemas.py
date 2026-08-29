"""Pydantic contracts — single source of truth for API + pipelines."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────
class Jurisdiction(str, Enum):
    INDIA = "india"
    INTERNATIONAL = "international"


class IPType(str, Enum):
    PATENT = "patent"
    GI = "gi"
    TRADEMARK = "trademark"
    COPYRIGHT = "copyright"
    DESIGN = "design"
    TRADE_SECRET = "trade_secret"
    PLANT_VARIETY = "plant_variety"
    ABS = "abs"  # Biological Diversity Act
    REGULATORY = "regulatory"  # Drugs/Cosmetics/FSSAI
    UNKNOWN = "unknown"


class FormulationCategory(str, Enum):
    CLASSICAL = "classical"  # First Schedule, Sec 3(p) bar
    PROPRIETARY = "proprietary"
    PHYTOPHARMACEUTICAL = "phytopharmaceutical"
    NEW_DRUG = "new_drug"
    AYURVEDA_AAHAR = "ayurveda_aahar"
    COSMETIC = "cosmetic"
    UNKNOWN = "unknown"


# ── Citation (triple rule) ─────────────────────────────
class Citation(BaseModel):
    """Every claim must map to one of these."""

    id: str = Field(description="cite_<hash>")
    source_type: Literal["statute", "rule", "treaty", "registry", "case_law", "pharmacopoeia"]
    title: str  # e.g., "Patents Act, 1970 — Sec 3(p)"
    span_text: str = Field(description="verbatim quoted span, not paraphrase")
    deep_link: str = Field(description="URL to official source")
    locator: str = Field(description="e.g., 'Sec 3(p) — p.4 para 2' or 'InPASS ID 12345'")
    version_hash: str = Field(description="corpus git hash at ingest time")


class Confidence(BaseModel):
    score: float = Field(ge=0, le=100, description="0–100")
    rationale: str
    abstain: bool = False


# ── Formulation flow ───────────────────────────────────
class FormulationAnswer(BaseModel):
    q_source_text: bool | None = None  # Is it in classical text?
    q_novelty: bool | None = None  # Novel ingredient/process?
    q_category: FormulationCategory | None = None

    def is_complete(self) -> bool:
        return None not in (self.q_source_text, self.q_novelty, self.q_category)


class FormulationResult(BaseModel):
    category: FormulationCategory
    posture_table: dict[str, str]  # column → value, e.g., {"IP": "Sec 3(p) bar ...", "ABS": "Required ..."}
    next_steps: list[str]
    citations: list[Citation]


# ── Chat ───────────────────────────────────────────────
class ChatRequest(BaseModel):
    query: str = Field(min_length=2, max_length=4000)
    jurisdiction: Jurisdiction = Field(description="hard toggle — never inferred silently")
    language: str = Field(default="en", description="BCP-47, e.g., en, hi, ta")
    session_id: str | None = None
    formulation: FormulationAnswer | None = None
    allow_paid_db: bool = False
    consent_id: str | None = None
    explain_simple: bool = Field(default=False, description="ELI5 mode — plain language, win for non-lawyers")
    audio_base64: str | None = None


class ChatResponse(BaseModel):
    answer: str
    answer_simple: str | None = Field(default=None, description="ELI5 version when requested")
    jurisdiction: Jurisdiction
    citations: list[Citation]
    confidence: Confidence
    corpus_version: str
    escalate_suggested: bool = False
    escalate_ticket_id: str | None = None
    formulation_result: FormulationResult | None = None
    firewall: dict | None = Field(default=None, description="jurisdiction firewall verdict")
    disclaimer: str = Field(
        default="Information only — not legal advice. Verify at source links before filing."
    )
    latency_ms: int | None = None
    free_tier: bool = Field(default=True, description="true = zero-cost path used, no paid API billed")


class ClassifyResponse(BaseModel):
    jurisdiction: Jurisdiction
    ip_type: IPType
    confidence: float
    needs_formulation_flow: bool


# ── Corpus / Audit ─────────────────────────────────────
class CorpusDocMeta(BaseModel):
    doc_id: str
    title: str
    source_type: str
    jurisdiction: Jurisdiction
    effective_date: str  # ISO
    version_hash: str
    sha256: str
    chunk_count: int = 0


class AuditEvent(BaseModel):
    event_id: str
    session_id: str
    query: str
    jurisdiction: Jurisdiction
    citations: list[str]  # citation ids
    confidence: float
    corpus_version: str
    consent_id: str | None
    created_at: datetime
    paid_db_accessed: bool = False


class EscalateRequest(BaseModel):
    session_id: str
    query: str
    reason: str
    jurisdiction: Jurisdiction
    citations: list[Citation] = []
    consent_id: str | None = None


class EscalateResponse(BaseModel):
    ticket_id: str
    status: Literal["created"] = "created"
    message: str = "Facilitator will review with full trace. You will be notified."
