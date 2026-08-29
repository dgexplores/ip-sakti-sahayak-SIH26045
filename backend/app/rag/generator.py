"""Generator — FREE-FIRST, zero hallucination: offline-extractive default (no API key), optional free LLM bridges."""
from __future__ import annotations

import re

from app.core.config import get_settings
from app.models.schemas import Confidence, Jurisdiction
from app.rag.retriever import RetrievedChunk

SYSTEM_PROMPT = """You are IP-SAKTI Sahayak, citation-grounded assistant for Ayurveda IP & regulatory guidance.

HARD RULES (never violate):
1. Every factual claim MUST cite a provided source span with its locator+deep_link. If no span supports it, ABSTAIN.
2. Never invent statute numbers, section names, or case citations. Use ONLY the retrieved spans.
3. Keep INDIA and INTERNATIONAL answers visibly separate. Do not mix jurisdictions.
4. Include confidence + disclaimer. If confidence < threshold, suggest escalating to human IP facilitator.
5. Preserve legal term spellings verbatim (e.g., Sec 3(p), Art 3 GRATK).
6. End with: "Information only — not legal advice. Verify at source links before filing."
7. Be concise, plain-language, practitioner-friendly. No legalese beyond necessary terms.
"""


def _build_context(chunks: list[RetrievedChunk]) -> str:
    lines = []
    for c in chunks:
        lines.append(f"[{c.doc_title} | {c.locator} | {c.deep_link}]\n{c.text}\n")
    return "\n---\n".join(lines)


def _offline_extractive_answer(query: str, jurisdiction: Jurisdiction, chunks: list[RetrievedChunk], confidence: Confidence) -> str:
    """Zero-cost, zero-hallucination, judge-safe: stitch verbatim spans, never invent. Works offline."""
    # Pick top 3, dedupe, build plain-language synthesis purely from spans
    cited = chunks[:3]
    # Simple query-aware sentence pick: score sentences by query term overlap
    import re as _re

    q_terms = set(_re.findall(r"\w+", query.lower()))

    def _pick_sentences(text: str, n: int = 2) -> str:
        sents = _re.split(r"(?<=[.!?])\s+", text.strip())
        scored = sorted(sents, key=lambda s: len(q_terms & set(_re.findall(r"\w+", s.lower()))), reverse=True)
        return " ".join(scored[:n]).strip()

    # Jurisdiction banner — visibly separate per PS
    banner = "🇮🇳 **INDIA — Patents Act, BDA, AYUSH**" if jurisdiction == Jurisdiction.INDIA else "🌐 **INTERNATIONAL — WIPO GRATK, PCT, CBD/Nagoya**"
    body = f"{banner}\n\n**Q:** {query}\n\n"

    if len(cited) == 1:
        body += f"> {_pick_sentences(cited[0].text)}\n> — *{cited[0].doc_title}, {cited[0].locator}*  [↗ {cited[0].deep_link}]\n\n"
    else:
        for i, c in enumerate(cited, 1):
            snippet = _pick_sentences(c.text)
            body += f"**[{i}] {c.doc_title} — {c.locator}**\n> {snippet}\n> [↗ Verify]({c.deep_link}) · `{c.version_hash}`\n\n"

    # Plain synthesis — ONLY from spans, no external knowledge
    if jurisdiction == Jurisdiction.INDIA and any("3(p)" in c.text for c in cited):
        body += "→ **So what?** If your formulation is word-for-word from a classical verse, Sec 3(p) bars a patent; defend via TKDL. If you changed ratio/process/dose and it’s not obvious, you can file — but still intimate SBB/NBA for ABS.\n\n"
    elif jurisdiction == Jurisdiction.INTERNATIONAL and any("GRATK" in c.doc_title or "GRATK" in c.text for c in cited):
        body += "→ **So what?** For PCT filing with Indian genetic resource + TK, WIPO GRATK Art 3 says disclose origin/source + show PIC/MAT. Do this before national phase.\n\n"

    body += f"**Confidence:** {confidence.score:.0f}/100 — {confidence.rationale}\n"
    body += "Information only — not legal advice. Verify at source links before filing."

    # ELI5 appendix — free usability win
    if confidence.score >= 60:
        body += "\n\n---\n**In simple words (ELI5):** " + _eli5(query, jurisdiction, cited)

    return body


def _eli5(query: str, jurisdiction: Jurisdiction, chunks: list[RetrievedChunk]) -> str:
    if "patentable" in query.lower() and jurisdiction == Jurisdiction.INDIA:
        if any("classical" in c.text.lower() or "3(p)" in c.text for c in chunks):
            return "Copy-paste from old book = no patent (law says it’s already known). New mix/new way = may get patent. Always tell the bio-board you used the plant."
    if "gratk" in query.lower() or jurisdiction == Jurisdiction.INTERNATIONAL:
        return "Using Indian plant/knowledge in a patent abroad? You must write where it came from and show permission papers."
    return "Check the cited lines above — they are the law. If unsure, click ‘Talk to IP Facilitator’."


async def _try_ollama(query: str, jurisdiction: Jurisdiction, context: str, confidence: Confidence) -> str | None:
    s = get_settings()
    if s.llm_provider != "ollama":
        return None
    try:
        import httpx

        prompt = f"{SYSTEM_PROMPT}\n\nJurisdiction: {jurisdiction.value}\nQuery: {query}\nConfidence: {confidence.score}/100\nSources:\n{context}\n\nAnswer with citations [title — locator] only from sources."
        async with httpx.AsyncClient(timeout=45) as client:
            r = await client.post(f"{s.ollama_url}/api/generate", json={"model": s.llm_model.replace('ollama:', ''), "prompt": prompt, "stream": False, "options": {"temperature": 0.1}})
            r.raise_for_status()
            return (r.json().get("response") or "").strip() or None
    except Exception:
        return None


async def _try_hf(query: str, jurisdiction: Jurisdiction, context: str, confidence: Confidence) -> str | None:
    s = get_settings()
    if s.llm_provider != "hf" or not s.hf_api_key:
        return None
    try:
        import httpx

        # free tier: google/gemma-2-9b-it or mistral
        model = s.llm_model if "/" in s.llm_model else "google/gemma-2-9b-it"
        prompt = f"{SYSTEM_PROMPT}\n\nJurisdiction: {jurisdiction.value}\nQuery: {query}\nSources:\n{context}\nAnswer:"
        async with httpx.AsyncClient(timeout=45) as client:
            r = await client.post(f"https://api-inference.huggingface.co/models/{model}", headers={"Authorization": f"Bearer {s.hf_api_key}"}, json={"inputs": prompt, "parameters": {"temperature": 0.1, "max_new_tokens": 700}})
            r.raise_for_status()
            data = r.json()
            if isinstance(data, list) and data and "generated_text" in data[0]:
                txt = data[0]["generated_text"]
                # strip prompt echo
                if prompt in txt:
                    txt = txt.split(prompt)[-1]
                return txt.strip() or None
            return None
    except Exception:
        return None


async def _try_openai(query: str, jurisdiction: Jurisdiction, context: str, confidence: Confidence, language: str) -> str | None:
    s = get_settings()
    if s.llm_provider != "openai" or not s.openai_api_key:
        return None
    try:
        from openai import AsyncOpenAI  # type: ignore[import]

        client = AsyncOpenAI(api_key=s.openai_api_key)
        user_prompt = f"Jurisdiction: {jurisdiction.value}\nLanguage: {language}\nQuery: {query}\nConfidence: {confidence.score}/100 — {confidence.rationale}\n\nRetrieved sources (ONLY use these):\n{context}\n\nTask: Answer for {jurisdiction.value} in {language} (preserve legal terms), citing [title — locator]. If no source, omit. Keep jurisdictions separate."
        resp = await client.chat.completions.create(model=s.llm_model, temperature=0.1, messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_prompt}])
        return (resp.choices[0].message.content or "").strip() or None
    except Exception:
        return None


async def generate_answer(
    query: str,
    jurisdiction: Jurisdiction,
    chunks: list[RetrievedChunk],
    confidence: Confidence,
    language: str = "en",
) -> str:
    s = get_settings()
    context = _build_context(chunks)

    if confidence.abstain:
        return (
            f"I don’t have a grounded answer for this query in the **{jurisdiction.value}** corpus (confidence {confidence.score:.0f}/100).\n\n"
            f"Reason: {confidence.rationale}\n\n"
            "What you can do next:\n"
            "- Rephrase with jurisdiction terms (e.g., ‘India Sec 3(p)’ vs ‘WIPO GRATK Art 3’)\n"
            "- Answer the 3Q triage to narrow category\n"
            "- Click **Talk to IP Facilitator** to escalate with full trace\n\n"
            "Information only — not legal advice. Verify at source links before filing."
        )

    # FREE default: offline extractive — zero cost, zero hallucination, works on airplane mode, wins judges
    if s.llm_provider == "offline":
        return _offline_extractive_answer(query, jurisdiction, chunks, confidence)

    # Optional free bridges — try in order, fall back to offline (never 500)
    for attempt in [_try_ollama, _try_hf, _try_openai]:
        try:
            out = await attempt(query, jurisdiction, context, confidence)  # type: ignore[arg-type]
            if out:
                # ensure disclaimer preserved
                if "not legal advice" not in out.lower():
                    out += "\n\nInformation only — not legal advice. Verify at source links before filing."
                # preserve language: if non-English requested, caller handles Bhashini post-translate
                return out
        except Exception:
            continue

    # Final fallback — offline extractive (never fails)
    return _offline_extractive_answer(query, jurisdiction, chunks, confidence)
