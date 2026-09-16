"""Chat API. Typed, jurisdiction-hard, citation-grounded, audit-logged."""
from __future__ import annotations

import re
import time
import uuid

from fastapi import APIRouter, Request

from app.core.config import get_settings
from app.core.corpus import corpus_version
from app.core.logging import get_logger
from app.models.schemas import ChatRequest, ChatResponse, Citation, Confidence, Jurisdiction
from app.rag.classifier import classify_query
from app.rag.confidence import compute_confidence
from app.rag.formulation import FORMULATION_QUESTIONS, evaluate_formulation
from app.rag.generator import _eli5, generate_answer
from app.rag.jurisdiction_firewall import filter_by_firewall, firewall_check
from app.rag.reranker import order_by_ip_type, rerank
from app.rag.retriever import retrieve_all, to_citations
from app.services.audit import audit_logger
from app.services.bhashini import asr, translate
from app.services.paid_connector import check_paid_access

router = APIRouter()
logger = get_logger("chat")

# Questions with no IP or Ayurveda content at all. This is a guard rail for the
# obvious cases ("write me a poem"); the confidence gate is what actually decides
# abstention, and it is calibrated against the corpus rather than against this
# list.
_OUT_OF_SCOPE = re.compile(r"\b(poem|poetry|joke|story|song|recipe for food|mango poem|write a poem)\b", re.I)


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request) -> ChatResponse:
    t0 = time.perf_counter()
    settings = get_settings()
    session_id = req.session_id or f"sess_{uuid.uuid4().hex[:10]}"

    # 1. Bhashini ASR if audio provided. A failure here is logged and the typed
    #    query is used instead of a fabricated transcript.
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
    jurisdiction = req.jurisdiction
    # The toggle decides what we answer for, but the question's own wording is
    # checked against it. Passing the toggle in as a hint made the classifier echo
    # it straight back, so the old `cls.jurisdiction != req.jurisdiction` test was
    # false by construction and could never fire. Only a strong textual signal
    # counts, so a question containing no jurisdiction words raises no false alarm.
    has_mismatch = (
        cls.inferred_jurisdiction is not None
        and cls.inferred_jurisdiction != req.jurisdiction
        and cls.inferred_jurisdiction_confidence >= 0.85
    )

    # 3. Paid DB guard
    paid = check_paid_access(req.allow_paid_db, req.consent_id)

    # 4. No embedding here. The retriever embeds lazily, and only after confirming a
    #    vector backend is reachable. Embedding unconditionally meant the offline
    #    path — the default demo path — loaded an ~80MB sentence-transformer on the
    #    first question of every session for a vector that `_offline_search` never
    #    reads. That is the documented "first question is slow".

    # 5. Retrieve across BOTH regimes, on purpose, and let the firewall narrow it.
    #    Filtering here as well is what made the firewall's leak branches
    #    unreachable: `foreign_ratio` was structurally always 0.0, so the project's
    #    headline guarantee could never be observed working. The per-pool budget is
    #    widened because roughly half of what comes back will be discarded.
    per_pool = settings.retrieve_top_k // 4 + 4
    retrieved = await retrieve_all(
        None,
        None,
        top_k_each=per_pool,
        query=query,
        ip_type=cls.ip_type.value,
    )

    # 5b. Jurisdiction firewall — unique win: enforce the hard split, report the verdict
    fw = firewall_check(query, jurisdiction, retrieved)
    retrieved = filter_by_firewall(retrieved, jurisdiction)

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

    # 8. Confidence + abstention. The gate is calibrated against the corpus (see
    #    `confidence_threshold` in config), so this block only needs to add the
    #    signals the score cannot see: a jurisdiction mismatch and a query with no
    #    IP or Ayurveda subject matter at all.
    is_out_of_scope = bool(_OUT_OF_SCOPE.search(query))
    if not is_out_of_scope and cls.ip_type.value == "unknown" and not ranked:
        # Nothing retrieved at all and no IP keyword — there is no subject matter
        # to answer from. The word-count heuristic that used to sit here
        # (`len(query.split()) < 8`) let every longer out-of-scope question
        # through; the honest relevance score now handles those, so this only
        # covers the empty-retrieval case.
        is_out_of_scope = True

    abstention_signal = has_mismatch or (not paid.allowed and "paid" in query.lower()) or is_out_of_scope
    # Scored on the reranked list, before the IP-type reordering below, so that
    # presenting the question's own branch of law first cannot flatter the score.
    confidence = compute_confidence(ranked, has_abstention_signal=abstention_signal)

    # 8b. Lead with the law that answers the question. Lexical ranking puts a
    #     document that merely shares a word with the query above the provision
    #     that decides it; the classifier's IP type corrects that at presentation
    #     time. See `order_by_ip_type`.
    presented = order_by_ip_type(ranked, cls.ip_type)
    citations: list[Citation] = to_citations(presented[:5])

    # 9. Generate (free-first: offline-extractive, zero hallucination)
    answer = await generate_answer(
        query, jurisdiction, presented[:6], confidence, language=req.language, ip_type=cls.ip_type
    )
    # System notices are bold paragraphs, NOT blockquotes.
    #
    # These three lines used to be emitted with a leading ">", so they rendered
    # in the same grey quote block as the statutory spans. The product's whole
    # claim is that you can tell quoted law from our own words; three notices
    # dressed as quotations broke exactly that. Bold-with-a-label reads as
    # commentary; only the statute spans are quoted.
    if fw["status"] != "clean":
        answer = f"**Jurisdiction firewall:** {fw['message']}\n\n" + answer
    if has_mismatch:
        answer = (
            f"**Check the toggle:** your question reads as **{cls.inferred_jurisdiction.value}** law, "
            f"but the toggle is set to **{req.jurisdiction.value}**. The answer below stays strictly "
            f"{req.jurisdiction.value} — switch the toggle to see the other regime.\n\n"
        ) + answer
    if not paid.allowed and req.allow_paid_db:
        answer = f"**Paid database:** {paid.reason}\n\n" + answer

    # 10. Bhashini translate/TTS if non-English (preserve legal terms)
    if req.language != "en" and not confidence.abstain:
        try:
            answer = await translate(answer, source_lang="en", target_lang=req.language)
        except Exception as e:
            logger.warning("chat.translate_failed", session_id=session_id, error=str(e))

    cv = corpus_version()
    escalate = confidence.abstain or confidence.score < 55

    # 10b. ELI5 synthesis (free) when requested. Previously this was skipped
    #      whenever the answer abstained, so a reader who asked for plain language
    #      on a question we could not answer got nothing back and no explanation.
    answer_simple = None
    if req.explain_simple:
        if confidence.abstain:
            answer_simple = (
                f"In simple words: we don’t have a {jurisdiction.value} law in the corpus that answers "
                "this one, so we are not guessing. Try rephrasing, or tap ‘Talk to IP Facilitator’."
            )
        else:
            answer_simple = _eli5(query, jurisdiction, ranked[:3], cls.ip_type)

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
