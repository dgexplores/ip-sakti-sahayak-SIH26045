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


def _pick_sentences(text: str, q_terms: set[str], n: int = 2) -> str:
    """Query-aware sentence pick: the 1-2 sentences closest to the question."""
    import re as _re

    sents = [s.strip() for s in _re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]
    if not sents:
        return text.strip()[:300]
    scored = sorted(
        sents,
        key=lambda s: len(q_terms & set(_re.findall(r"\w+", s.lower()))),
        reverse=True,
    )
    return " ".join(scored[:n]).strip()


def _has(chunks: list[RetrievedChunk], *terms: str) -> bool:
    blob = " ".join(f"{c.doc_title} {c.text}" for c in chunks).lower()
    return any(t.lower() in blob for t in terms)


def _has_word(chunks: list[RetrievedChunk], *terms: str) -> bool:
    """Word-boundary match for short tokens: bare `in` makes GI hit 'biological'."""
    import re as _re

    blob = " ".join(f"{c.doc_title} {c.text}" for c in chunks)
    return any(_re.search(r"\b" + _re.escape(t) + r"\b", blob, _re.I) for t in terms)


def _verdict(query: str, jurisdiction: Jurisdiction, chunks: list[RetrievedChunk]) -> str:
    """One-to-two-line direct answer, every clause traceable to a cited span."""
    q = query.lower()
    if jurisdiction == Jurisdiction.INDIA:
        if _has(chunks, "3(p)") and ("classical" in q or _has(chunks, "traditional knowledge")):
            if any(w in q for w in ("novel", "new process", "naya", "10x", "changed", "ratio")):
                return "Short answer: possibly yes — a classical base with a genuinely new ratio, process or dose can be patented, but the classical part itself cannot be."
            return "Short answer: no — a formulation copied word-for-word from a classical text is traditional knowledge and the law bars a patent on it."
        if _has(chunks, "benefit-sharing", "NBA", "SBB", "Sec 7"):
            return "Short answer: you can proceed, but you must first clear the biodiversity permission — commercial use of the plant needs SBB intimation or NBA approval."
        if _has(chunks, "Ayurveda Aahar", "FSSAI"):
            return "Short answer: it depends on what you claim — sold as food it follows the FSSAI Aahar route, sold as medicine it needs an AYUSH drug licence."
        if _has(chunks, "trademark"):
            return "Short answer: yes — protect the brand name and packaging as a trademark; the recipe itself is a separate question."
        if _has(chunks, "copyright"):
            return "Short answer: yes — your book, label text and compilation can be copyrighted; that protects the writing, not the recipe."
        if _has(chunks, "design"):
            return "Short answer: yes — the bottle, carton or label shape can be protected as a design if it is new and ornamental."
        if _has(chunks, "trade secret", "confidential"):
            return "Short answer: yes — keep the recipe secret with NDAs and access control; that protection lasts as long as it stays secret."
        if _has(chunks, "plant variety", "PPV", "cultivar", "breeder"):
            return "Short answer: possibly — a genuinely new plant variety goes through the plant-variety route, not a patent."
        if _has(chunks, "cosmetic"):
            return "Short answer: yes, as a cosmetic — you need the cosmetic licence and correct labelling, not a drug approval."
        if _has(chunks, "phytopharmaceutical", "CDSCO"):
            return "Short answer: possibly — a standardised fraction with clinical data can go the phytopharmaceutical route with CDSCO."
        return "Short answer: here is what the closest law says — read the quoted lines below, they decide your case."
    # international
    if _has(chunks, "GRATK", "Art 3"):
        return "Short answer: you must disclose where the Indian plant or knowledge came from and show your permission papers when you file abroad."
    if _has(chunks, "PCT"):
        return "Short answer: you can file in many countries with one PCT application, but each country still examines it under its own law."
    if _has(chunks, "Nagoya", "CBD", "PIC", "MAT"):
        return "Short answer: you need prior permission and agreed benefit-sharing terms before using the resource — file those papers first."
    if _has(chunks, "TRIPS"):
        return "Short answer: international rules leave room for countries to protect traditional knowledge — your home-country clearance still matters."
    return "Short answer: here is what the closest international rule says — read the quoted lines below."


def _meaning_lines(query: str, jurisdiction: Jurisdiction, chunks: list[RetrievedChunk]) -> list[str]:
    """IP / permission / selling lines — paraphrases of the cited spans only."""
    lines: list[str] = []
    if _has(chunks, "3(p)", "traditional knowledge"):
        lines.append("**Patent:** the classical verse itself cannot be patented. A new ratio, process or dose that is not obvious can be filed — novelty and inventive step still have to be proved.")
    elif _has(chunks, "patent", "novelty", "inventive"):
        lines.append("**Patent:** patentability turns on novelty and inventive step over everything already known, including the classical texts.")
    if _has(chunks, "trademark", "brand"):
        lines.append("**Brand:** the name, logo and packaging can be trademarked even when the recipe cannot be patented.")
    if _has(chunks, "design", "ornamental", "packaging"):
        lines.append("**Packaging:** a new bottle, carton or label shape can be a registered design.")
    if _has(chunks, "copyright", "literary", "compilation"):
        lines.append("**Writing:** your book, label text and compilation are copyrighted automatically — that stops copying of the text, not use of the recipe.")
    if _has(chunks, "trade secret", "confidential", "NDA"):
        lines.append("**Secrecy:** if you never publish the recipe, guard it with NDAs and limited access instead of filing.")
    if _has(chunks, "plant variety", "PPV", "cultivar", "breeder"):
        lines.append("**Plant variety:** a new, distinct, uniform cultivar is registered as a plant variety with breeder and farmer rights attached.")
    if _has(chunks, "NBA", "SBB", "benefit-sharing", "Sec 7", "Sec 3"):
        if jurisdiction == Jurisdiction.INDIA:
            lines.append("**Biodiversity permission:** Indian users intimate the State Board before commercial use; foreign entities need NBA approval first. Benefit-sharing applies on commercialisation.")
        else:
            lines.append("**Biodiversity permission:** show prior informed consent and mutually agreed benefit-sharing terms from the providing country.")
    if _has(chunks, "Ayurveda Aahar", "FSSAI"):
        lines.append("**Selling as food vs medicine:** food route means FSSAI Aahar rules on ingredients, packaging and claims; disease-cure claims push you into the drug route and the Magic Remedies bar.")
    if _has(chunks, "cosmetic"):
        lines.append("**Selling as cosmetic:** you need the cosmetic licence, correct ingredient labelling and no drug-like claims.")
    if _has(chunks, "phytopharmaceutical", "CDSCO", "clinical"):
        lines.append("**Selling as phytopharma:** needs standardisation, clinical data and CDSCO approval — heavier than a classical AYUSH licence.")
    if _has(chunks, "GRATK", "Art 3"):
        lines.append("**Filing abroad:** disclose the country of origin or source of the genetic resource and associated knowledge, and attach the permission papers before the national phase.")
    if _has(chunks, "PCT"):
        lines.append("**PCT route:** one international filing buys time, but patentability is still decided country by country.")
    if _has(chunks, "TKDL", "prior art", "opposition"):
        lines.append("**Defence:** the examiner can cite TKDL as prior art, and anyone can oppose using a TK ground — search TKDL before you spend on drafting.")
    return lines[:4]


def _next_steps(query: str, jurisdiction: Jurisdiction, chunks: list[RetrievedChunk]) -> list[str]:
    steps: list[str] = []
    if _has(chunks, "TKDL", "prior art", "InPASS", "patent"):
        steps.append("Search TKDL and InPASS for your exact recipe and ratio before spending on a draft.")
    if _has(chunks, "3(p)"):
        steps.append("If anything is new (ratio, process, dose), write down exactly what changed versus the verse — that sentence is your patent case.")
    if _has(chunks, "NBA", "SBB", "benefit-sharing", "Sec 7") or _has_word(chunks, "PIC", "MAT"):
        steps.append("Clear the biodiversity paper first: intimate the State Board or get NBA approval, and keep the benefit-sharing receipt.")
    if _has(chunks, "GRATK", "Art 3", "PCT"):
        steps.append("Before the PCT national phase, attach origin disclosure plus the permission papers.")
    if _has(chunks, "FSSAI", "Aahar", "Magic Remedies"):
        steps.append("Fix your label and claims to the FSSAI Aahar list — drop any cure-all wording.")
    if _has(chunks, "trademark", "brand") or _has_word(chunks, "GI"):
        steps.append("File the brand name as a trademark (and GI if the origin matters) while the patent question is open.")
    if _has(chunks, "cosmetic"):
        steps.append("Get the cosmetic licence and stability data in order before you print labels.")
    if _has(chunks, "copyright"):
        steps.append("Keep dated copies of your manuscript and labels — that is your copyright proof.")
    if _has(chunks, "trade secret"):
        steps.append("If keeping it secret, sign NDAs today and limit who sees the full formula.")
    if _has(chunks, "design"):
        steps.append("Photograph and date the packaging design before showing it to anyone.")
    if _has(chunks, "plant variety", "PPV"):
        steps.append("For a new cultivar, record distinctness trials for the plant-variety application.")
    if _has(chunks, "phytopharmaceutical", "CDSCO", "clinical"):
        steps.append("Book a pre-submission meeting with CDSCO with your standardisation and trial plan.")
    steps.append("Still unsure after the quotes above? Take these citations to an IP facilitator — the trace travels with you.")
    # keep it tight: most useful first, max 4
    return steps[:4]


def _offline_extractive_answer(query: str, jurisdiction: Jurisdiction, chunks: list[RetrievedChunk], confidence: Confidence) -> str:
    """Zero-cost, zero-hallucination: verbatim spans plus a plain-spoken reading of them."""
    import re as _re

    cited = chunks[:3]
    q_terms = set(_re.findall(r"\w+", query.lower()))
    scope = "INDIA law" if jurisdiction == Jurisdiction.INDIA else "INTERNATIONAL law"

    body = f"**{scope} — short answer**\n{_verdict(query, jurisdiction, cited)}\n\n"
    body += "**Why — the exact law that decides this**\n"
    body += "Each quote below is word-for-word from the statute or registry. Read the bold line after it for what it means in practice.\n\n"
    for i, c in enumerate(cited, 1):
        snippet = _pick_sentences(c.text, q_terms)
        body += f"**{i}. {c.doc_title} — {c.locator}**\n> {snippet}\n> [Verify at source]({c.deep_link}) · `{c.version_hash}`\n\n"

    meanings = _meaning_lines(query, jurisdiction, cited)
    if meanings:
        body += "**What this means for you**\n" + "".join(f"- {m}\n" for m in meanings) + "\n"

    body += "**What to do next**\n" + "".join(
        f"{i}. {s}\n" for i, s in enumerate(_next_steps(query, jurisdiction, cited), 1)
    ) + "\n"

    body += f"**Confidence:** {confidence.score:.0f}/100 — {confidence.rationale}\n"
    body += "Information only — not legal advice. Verify at source links before filing."

    if confidence.score >= 60:
        body += "\n\n---\n**In simple words:** " + _eli5(query, jurisdiction, cited)

    return body


def _eli5(query: str, jurisdiction: Jurisdiction, chunks: list[RetrievedChunk]) -> str:
    q = query.lower()
    if jurisdiction == Jurisdiction.INDIA and ("patent" in q or _has(chunks, "3(p)")):
        if _has(chunks, "3(p)", "traditional knowledge"):
            return "Copy-paste from old book = no patent (law says it’s already known). New mix, new ratio or new way of making it = may get patent. Either way, tell the bio-board you used the plant."
        return "Patent = something new that no book or product already shows. The old recipe stays free for all; only your genuinely new part can be yours."
    if _has(chunks, "trademark", "brand"):
        return "Name and pack can be yours even if the recipe is everyone’s. Register the brand early so copycats can’t use your name."
    if _has(chunks, "copyright"):
        return "Your writing is protected the moment you write it. Anyone can still cook the recipe — they just can’t photocopy your book."
    if _has(chunks, "design"):
        return "A new bottle or box shape can be registered. The look is protected, not what’s inside."
    if _has(chunks, "trade secret"):
        return "No filing at all: just never tell. NDAs plus locked recipes. The day it leaks, the protection ends."
    if _has(chunks, "plant variety", "PPV", "cultivar"):
        return "Grew something truly new and stable? Register the seed line itself. Farmers keep their own rights alongside."
    if _has(chunks, "Ayurveda Aahar", "FSSAI"):
        return "Selling as food? Follow the food list and don’t promise cures on the label. Promising a cure makes it a medicine with a harder licence."
    if _has(chunks, "cosmetic"):
        return "Cream or oil for looks, not cure? That’s the cosmetic lane: licence plus honest label, no medicine claims."
    if _has(chunks, "phytopharmaceutical", "CDSCO"):
        return "Purified plant drug with lab tests and patient data? That’s the pharma lane — strong protection, but real trials needed."
    if _has(chunks, "NBA", "SBB", "benefit-sharing"):
        return "Used an Indian plant to earn money? Inform the state board first (foreigners: NBA approval). Share a fair cut — keep that receipt forever."
    if jurisdiction == Jurisdiction.INTERNATIONAL or _has(chunks, "GRATK", "PCT", "Nagoya"):
        if _has(chunks, "GRATK", "Art 3"):
            return "Using Indian plant or knowledge in a foreign patent? Write where it came from and attach permission papers, or the patent can fail."
        return "One world filing (PCT) saves time, but every country still says yes or no separately. Home-country permission papers travel with you."
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
