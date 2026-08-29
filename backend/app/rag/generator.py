"""Generator — source-grounded, low temp, never fabricates authority."""
from __future__ import annotations

from app.core.config import get_settings
from app.models.schemas import Confidence, Jurisdiction
from app.rag.retriever import RetrievedChunk

SYSTEM_PROMPT = """You are IP-SAKTI Sahayak, a citation-grounded assistant for Ayurveda IP & regulatory guidance.

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


async def generate_answer(
    query: str,
    jurisdiction: Jurisdiction,
    chunks: list[RetrievedChunk],
    confidence: Confidence,
    language: str = "en",
) -> str:
    """Call LLM with grounded context; fallback mock if no key (keeps demo runnable)."""
    s = get_settings()
    context = _build_context(chunks)

    if confidence.abstain:
        return (
            f"I don't have a grounded answer for this query in the **{jurisdiction.value}** corpus (confidence {confidence.score:.0f}/100).\n\n"
            f"Reason: {confidence.rationale}\n\n"
            "What you can do next:\n"
            "- Rephrase with jurisdiction-specific terms (e.g., 'India Patents Act Sec 3(p)' vs 'WIPO GRATK')\n"
            "- Answer the 3 formulation triage questions to narrow the category\n"
            "- Click **Talk to IP Facilitator** to escalate with full trace\n\n"
            "Information only — not legal advice. Verify at source links before filing."
        )

    if not s.openai_api_key:
        # Deterministic mock answer that still cites real spans — judge-friendly offline
        cited = chunks[:3]
        cite_lines = "\n".join(f"- {c.doc_title} — {c.locator} — {c.deep_link}" for c in cited)
        body = (
            f"**Jurisdiction: {jurisdiction.value.upper()}**\n\n"
            f"Query: {query}\n\n"
            f"Based on the retrieved sources:\n\n"
        )
        for c in cited:
            body += f"> {c.text[:300]}  \n> — *{c.doc_title}, {c.locator}*\n\n"
        body += f"**Cited sources:**\n{cite_lines}\n\n"
        body += f"Confidence: {confidence.score:.0f}/100 — {confidence.rationale}\n\n"
        body += "Information only — not legal advice. Verify at source links before filing."
        return body

    # Real LLM path
    try:
        from openai import AsyncOpenAI  # type: ignore[import]

        client = AsyncOpenAI(api_key=s.openai_api_key)
        user_prompt = f"""Jurisdiction: {jurisdiction.value}
Language: {language}
Query: {query}
Confidence: {confidence.score}/100 — {confidence.rationale}

Retrieved sources (ONLY use these):
{context}

Task: Answer the query for the given jurisdiction, in {language} (preserve legal terms in English), citing each claim with [title — locator]. If a claim lacks a source, omit it. Keep India/International strictly separate."""

        resp = await client.chat.completions.create(
            model=s.llm_model,
            temperature=0.1,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        # fallback to mock on upstream failure — never 500
        return (
            f"LLM unavailable ({e}) — showing grounded extracts instead:\n\n"
            + "\n\n".join(f"[{c.doc_title} | {c.locator}]\n{c.text[:400]}" for c in chunks[:3])
            + "\n\nInformation only — not legal advice."
        )
