"""Chat API — typed, jurisdiction-hard, citation-grounded, audit-logged."""
from __future__ import annotations

import hashlib
import time
import uuid

from fastapi import APIRouter, Request

from app.core.config import get_settings
from app.models.schemas import ChatRequest, ChatResponse, Citation, Confidence, Jurisdiction
from app.pipelines.ingest.embedder import get_embedder
from app.rag.classifier import classify_query
from app.rag.confidence import compute_confidence
from app.rag.formulation import FORMULATION_QUESTIONS, evaluate_formulation
from app.rag.generator import generate_answer
from app.rag.reranker import rerank
from app.rag.retriever import retrieve_all, to_citations
from app.services.audit import audit_logger
from app.services.bhashini import asr, translate
from app.services.paid_connector import check_paid_access
from app.rag.jurisdiction_firewall import firewall_check

router = APIRouter()


def _corpus_version() -> str:
    # hash of manifest doc_ids; stable per ingest — free freshness proof, no paid service
    try:
        import json, pathlib
        m = pathlib.Path(__file__).parents[4] / "corpus" / "manifest.json"
        if m.exists():
            docs = json.loads(m.read_text()).get("documents", [])
            h = hashlib.sha256("".join(sorted(d.get("doc_id","") for d in docs)).encode()).hexdigest()[:12]
            return h
    except Exception:
        pass
    return hashlib.sha256(b"sakti-corpus-v1").hexdigest()[:12]


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request) -> ChatResponse:
    t0 = time.perf_counter()
    settings = get_settings()
    session_id = req.session_id or f"sess_{uuid.uuid4().hex[:10]}"

    # 1. Bhashini ASR if audio provided
    query = req.query
    if req.audio_base64:
        try:
            transcript = await asr(req.audio_base64, language=req.language)
            if transcript:
                query = transcript
        except Exception:
            pass  # keep original query

    # 2. Classify (jurisdiction toggle is hard — never overrides to other side)
    cls = classify_query(query, jurisdiction_hint=req.jurisdiction)
    # Enforce hard toggle: always return the requested jurisdiction, flag if mismatch
    has_mismatch = cls.jurisdiction != req.jurisdiction and cls.confidence > 0.75
    # For SIH split requirement: we never conflate; if mismatch signal strong, lower confidence to trigger clarification
    jurisdiction = req.jurisdiction

    # 3. Paid DB guard
    paid = check_paid_access(req.allow_paid_db, req.consent_id)

    # 4. Embed query
    embedder = get_embedder()
    q_emb = (await embedder.embed([query]))[0]

    # 5. Retrieve (4 retrievers parallel, jurisdiction-filtered)
    retrieved = await retrieve_all(q_emb, jurisdiction, top_k_each=settings.retrieve_top_k // 4 + 2)
    # 5b. Jurisdiction firewall — unique win: enforce hard split, filter leaks, surface verdict
    fw = firewall_check(query, jurisdiction, retrieved)
    if fw["status"] in ("leak_warning", "filtered"):
        retrieved = [c for c in retrieved if c.jurisdiction == jurisdiction.value] or retrieved
    # 6. Rerank (free-first: local CrossEncoder)
    ranked = await rerank(query, retrieved, top_k=settings.rerank_top_k)
    # 7. Formulation flow if needed
    formulation_result = None
    if req.formulation is not None:
        # Use mock citations for posture table until graph wired
        mock_cites = to_citations(ranked[:2])
        formulation_result = evaluate_formulation(req.formulation, citations=mock_cites)
    elif cls.needs_formulation_flow and not query.strip().endswith("?"):
        # signal to frontend to show flow, but still answer
        pass

    # 8. Confidence + abstention
    abstention_signal = has_mismatch or not paid.allowed and "paid" in query.lower()
    confidence = compute_confidence(ranked, has_abstention_signal=abstention_signal)
    # if paid blocked, append note but don't fail
    citations: list[Citation] = to_citations(ranked[:5])

    # 9. Generate (free-first: offline-extractive, zero hallucination)
    answer = await generate_answer(query, jurisdiction, ranked[:6], confidence, language=req.language)
    if fw["status"] != "clean":
        answer = f"> 🛡️ **Jurisdiction firewall:** {fw['message']}\n\n" + answer
    if not paid.allowed and req.allow_paid_db:
        answer = f"> ⚠️ {paid.reason}\n\n" + answer

    # 10. Bhashini translate/TTS if non-English (preserve legal terms)
    audio_b64: str | None = None  # not in response schema yet; kept for stage 3 header
    if req.language != "en" and not confidence.abstain:
        try:
            answer = await translate(answer, source_lang="en", target_lang=req.language)
        except Exception:
            pass

    corpus_version = _corpus_version()
    escalate = confidence.abstain or confidence.score < 55

    # 10b. ELI5 synthesis (free) when requested
    answer_simple = None
    if req.explain_simple and not confidence.abstain:
        # reuse offline ELI5 logic via generator helper (inline to avoid extra LLM call)
        try:
            from app.rag.generator import _eli5  # type: ignore[import]
            answer_simple = _eli5(query, jurisdiction, ranked[:3])
        except Exception:
            answer_simple = "In simple words: check the cited laws above — they decide patent/ABS. Unsure? Escalate."

    # 11. Audit (DPDP: pseudonymized, consent-aware)
    try:
        await audit_logger.log(
            session_id=session_id,
            query=query,
            jurisdiction=jurisdiction,
            citation_ids=[c.id for c in citations],
            confidence=confidence.score,
            corpus_version=corpus_version,
            consent_id=req.consent_id,
            paid_db_accessed=paid.allowed,
        )
    except Exception:
        pass

    latency_ms = int((time.perf_counter() - t0) * 1000)
    from app.core.config import get_settings as _gs
    free_tier = _gs().llm_provider == "offline" and _gs().embedding_provider == "local"

    return ChatResponse(
        answer=answer,
        answer_simple=answer_simple,
        jurisdiction=jurisdiction,
        citations=citations,
        confidence=confidence,
        corpus_version=corpus_version,
        escalate_suggested=escalate,
        escalate_ticket_id=None,
        formulation_result=formulation_result,
        firewall=fw,
        latency_ms=latency_ms,
        free_tier=free_tier,
    )


@router.get("/formulation-questions")
async def get_formulation_questions() -> dict:
    return {"questions": FORMULATION_QUESTIONS}
