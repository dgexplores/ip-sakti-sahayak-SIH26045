"""Chat API. Typed, jurisdiction-hard, citation-grounded, audit-logged."""
from __future__ import annotations

import time
import uuid

from fastapi import APIRouter, Request

from app.core.config import get_settings
from app.core.corpus import corpus_version
from app.core.logging import get_logger
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
logger = get_logger("chat")


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
        except Exception as e:
            logger.warning("chat.asr_failed", session_id=session_id, error=str(e))

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
    retrieved = await retrieve_all(q_emb, jurisdiction, top_k_each=settings.retrieve_top_k // 4 + 2, query=query)
    # 5b. Jurisdiction firewall — unique win: enforce hard split, filter leaks, surface verdict
    fw = firewall_check(query, jurisdiction, retrieved)
    if fw["status"] in ("leak_warning", "filtered"):
        retrieved = [c for c in retrieved if c.jurisdiction == jurisdiction.value] or retrieved
    # 6. Rerank (free-first: local CrossEncoder)
    # Reranked on the original question, not the bridged one. Bridging appends
    # keywords, and a bag of terms is good input for lexical matching but bad
    # input for a cross-encoder trained on natural questions: feeding it the
    # bridged form measurably moved two Hindi questions from a correct
    # citation to a wrong one.
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

    # 8. Confidence + abstention — free, robust: also detect out-of-scope (poem/joke/mango) via lexical overlap
    is_out_of_scope = False
    try:
        import re

        OUT_OF_SCOPE = re.compile(r"\b(poem|poetry|joke|story|song|recipe for food|mango poem|write a poem)\b", re.I)
        if OUT_OF_SCOPE.search(query):
            is_out_of_scope = True
        # also if classifier says UNKNOWN + no formulation + no IP keyword + query short generic → likely out of scope
        if cls.ip_type.value == "unknown" and not cls.needs_formulation_flow and len(query.split()) < 8:
            # Bridged, so an Indic-script question is compared on terms the
            # English corpus can actually contain.
            from app.rag.retriever import bridge_query

            q_terms = set(re.findall(r"\w+", bridge_query(query).lower()))
            top_text = " ".join(c.text.lower() for c in ranked[:2])
            top_terms = set(re.findall(r"\w+", top_text))
            overlap = len(q_terms & top_terms) / max(1, len(q_terms))
            if overlap < 0.18:
                is_out_of_scope = True
    except Exception as e:
        logger.warning("chat.out_of_scope_check_failed", session_id=session_id, error=str(e))
    abstention_signal = has_mismatch or (not paid.allowed and "paid" in query.lower()) or is_out_of_scope
    confidence = compute_confidence(ranked, has_abstention_signal=abstention_signal)
    # if paid blocked, append note but don't fail
    citations: list[Citation] = to_citations(ranked[:5])

    # 9. Generate (free-first: offline-extractive, zero hallucination)
    answer = await generate_answer(query, jurisdiction, ranked[:6], confidence, language=req.language)
    if fw["status"] != "clean":
        answer = f"> **Jurisdiction firewall:** {fw['message']}\n\n" + answer
    if not paid.allowed and req.allow_paid_db:
        answer = f"> **Paid database:** {paid.reason}\n\n" + answer

    # 10. Bhashini translate/TTS if non-English (preserve legal terms)
    audio_b64: str | None = None  # not in response schema yet; kept for stage 3 header
    if req.language != "en" and not confidence.abstain:
        try:
            answer = await translate(answer, source_lang="en", target_lang=req.language)
        except Exception as e:
            logger.warning("chat.translate_failed", session_id=session_id, error=str(e))

    cv = corpus_version()
    escalate = confidence.abstain or confidence.score < 55

    # 10b. ELI5 synthesis (free) when requested
    answer_simple = None
    if req.explain_simple and not confidence.abstain:
        # reuse offline ELI5 logic via generator helper (inline to avoid extra LLM call)
        try:
            from app.rag.generator import _eli5  # type: ignore[import]
            answer_simple = _eli5(query, jurisdiction, ranked[:3])
        except Exception as e:
            logger.warning("chat.eli5_failed", session_id=session_id, error=str(e))
            answer_simple = "In simple words: check the cited laws above, they decide patent/ABS. Unsure? Escalate."

    # 11. Audit (DPDP: pseudonymized, consent-aware)
    try:
        await audit_logger.log(
            session_id=session_id,
            query=query,
            jurisdiction=jurisdiction,
            citation_ids=[c.id for c in citations],
            confidence=confidence.score,
            corpus_version=cv,
            consent_id=req.consent_id,
            paid_db_accessed=paid.allowed,
        )
    except Exception as e:
        logger.warning("chat.audit_failed", session_id=session_id, error=str(e))

    latency_ms = int((time.perf_counter() - t0) * 1000)
    free_tier = settings.llm_provider == "offline" and settings.embedding_provider == "local"

    return ChatResponse(
        answer=answer,
        answer_simple=answer_simple,
        jurisdiction=jurisdiction,
        citations=citations,
        confidence=confidence,
        corpus_version=cv,
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
