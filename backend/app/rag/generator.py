"""Generator — FREE-FIRST, zero hallucination: offline-extractive default (no API key), optional free LLM bridges."""
from __future__ import annotations

import re

from app.core.config import get_settings
from app.models.schemas import Confidence, IPType, Jurisdiction
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


_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_WHITESPACE_RUN = re.compile(r"\s+")

# Corpus-authoring scaffolding rather than law: a bare source URL, a "Source:" or
# "Version hash:" label, a backticked hex digest. The loader strips the editorial
# fence these normally live in, but a line written outside it would otherwise be
# quoted verbatim as though it were the statute — which is exactly what happened
# with a fabricated version hash on the flagship question.
_METADATA_RE = re.compile(
    r"^\s*(source|link|see also|version hash|note)\s*:"
    r"|\bhttps?://"
    r"|`[0-9a-f]{8,}`",
    re.I,
)


def _is_metadata(sentence: str) -> bool:
    s = sentence.strip()
    if not s:
        return True
    # Length guard: a long paragraph that happens to mention a link is still law.
    return bool(_METADATA_RE.search(s)) and len(s) < 300


def _sentence_spans(text: str) -> list[tuple[int, int]]:
    """Offset pairs for each non-empty sentence, so a quote can be sliced out."""
    spans: list[tuple[int, int]] = []
    start = 0
    for m in _SENTENCE_SPLIT.finditer(text):
        spans.append((start, m.start()))
        start = m.end()
    spans.append((start, len(text)))
    return [(a, b) for a, b in spans if text[a:b].strip()]


def _pick_sentences(text: str, q_terms: set[str], n: int = 2) -> str:
    """The best-matching sentence plus its neighbours, in the document's own order.

    This used to score every sentence independently and concatenate the top two.
    That produced text which read like a quotation but was not one: the two
    sentences could come from opposite ends of the document, and the result was
    not a contiguous substring of the source. On the flagship demo question the
    resulting "quote" opened with a source URL and a fabricated version hash. For
    a tool whose entire claim is "we quote the exact line", the quote has to be
    the exact line — so this locates the best sentence and returns it together
    with its neighbours, sliced from the original text.

    Metadata spans are excluded from selection and trimmed from the edges of the
    window. Only the edges: trimming the interior would break the contiguity the
    rest of this function exists to guarantee.

    Runs of whitespace are collapsed for display, because the answer body wraps
    the quote in a markdown blockquote and an embedded newline would break it.
    The words themselves are untouched.
    """
    spans = _sentence_spans(text)
    if not spans:
        return _WHITESPACE_RUN.sub(" ", text).strip()[:300]

    def _is_meta(i: int) -> bool:
        return _is_metadata(text[spans[i][0]:spans[i][1]])

    def _score(i: int) -> int:
        s = text[spans[i][0]:spans[i][1]].lower()
        return len(q_terms & set(re.findall(r"\w+", s)))

    # Never select a metadata span as the anchor, unless that is all there is.
    candidates = [i for i in range(len(spans)) if not _is_meta(i)] or list(range(len(spans)))

    # Tie-break towards the earlier sentence: deterministic, and it tends to open
    # the quote with the section heading rather than a later aside.
    best = max(candidates, key=lambda i: (_score(i), -i))
    first = max(0, min(best - 1, len(spans) - n))
    last = min(first + n - 1, len(spans) - 1)
    while first <= last and _is_meta(first):
        first += 1
    while last >= first and _is_meta(last):
        last -= 1
    if first > last:
        non_meta = [i for i in range(len(spans)) if not _is_meta(i)]
        if not non_meta:
            return _WHITESPACE_RUN.sub(" ", text).strip()[:300]
        first = last = non_meta[0]
    return _WHITESPACE_RUN.sub(" ", text[spans[first][0]:spans[last][1]]).strip()


def _has(chunks: list[RetrievedChunk], *terms: str) -> bool:
    blob = " ".join(f"{c.doc_title} {c.text}" for c in chunks).lower()
    return any(t.lower() in blob for t in terms)


def _has_word(chunks: list[RetrievedChunk], *terms: str) -> bool:
    """Word-boundary match for short tokens: bare `in` makes GI hit 'biological'."""
    import re as _re

    blob = " ".join(f"{c.doc_title} {c.text}" for c in chunks)
    return any(_re.search(r"\b" + _re.escape(t) + r"\b", blob, _re.I) for t in terms)


def _has_doc(chunks: list[RetrievedChunk], *doc_ids: str) -> bool:
    """Whether a specific document is among the retrieved spans.

    Preferable to substring sniffing for "which regime is this": a document id is
    an exact fact about what was retrieved, whereas `"design" in blob` is true of
    any text that merely mentions the word.
    """
    return bool({c.doc_id for c in chunks} & set(doc_ids))


# A document that is unambiguously about one regime can stand in for the IP type
# when the classifier had no keyword signal. Only used as a fallback: the
# classifier's verdict is preferred, because it reflects the question rather than
# whatever the retriever happened to surface.
_DOC_IP_TYPE: dict[str, IPType] = {
    "patents_act_1970": IPType.PATENT,
    "patents_rules_2024": IPType.PATENT,
    "pct_system": IPType.PATENT,
    "trade_marks_act_1999": IPType.TRADEMARK,
    "copyright_act_1957": IPType.COPYRIGHT,
    "designs_act_2000": IPType.DESIGN,
    "trade_secrets_india": IPType.TRADE_SECRET,
    "gi_act_1999": IPType.GI,
    "ppvfr_act_2001": IPType.PLANT_VARIETY,
    "bda_2023": IPType.ABS,
    "cbd_nagoya": IPType.ABS,
    "fssai_aahar_2022": IPType.REGULATORY,
    "drugs_cosmetics_act": IPType.REGULATORY,
    "magic_remedies_act": IPType.REGULATORY,
}


# Last-resort fallback when a chunk carries neither a known doc_id nor a title
# we recognise (fixtures, or a new document before it is added to _DOC_IP_TYPE).
_TITLE_IP_HINTS: list[tuple[str, IPType]] = [
    ("patent", IPType.PATENT),
    ("pct", IPType.PATENT),
    ("trade secret", IPType.TRADE_SECRET),
    ("geographical indication", IPType.GI),
    ("plant variet", IPType.PLANT_VARIETY),
    ("trade mark", IPType.TRADEMARK),
    ("trademark", IPType.TRADEMARK),
    ("copyright", IPType.COPYRIGHT),
    ("biological diversity", IPType.ABS),
    ("design", IPType.DESIGN),
    ("fssai", IPType.REGULATORY),
]


def _effective_ip_type(ip_type: IPType | None, chunks: list[RetrievedChunk]) -> IPType:
    """The classifier's verdict when it has one, else inferred from what came back.

    Scans *all* retrieved chunks rather than only the top one. The top hit is
    often a supporting document — TKDL, the pharmacopoeia, a case report — which
    maps to no IP type at all, and reading only that chunk threw away a perfectly
    clear signal sitting one position below.
    """
    if ip_type is not None and ip_type != IPType.UNKNOWN:
        return ip_type
    for c in chunks:
        mapped = _DOC_IP_TYPE.get(c.doc_id)
        if mapped is not None:
            return mapped
    for c in chunks:
        title = c.doc_title.lower()
        for needle, mapped in _TITLE_IP_HINTS:
            if needle in title:
                return mapped
    return IPType.UNKNOWN


# Novelty signals. Word-bounded, and deliberately narrow: a bare "new" appears in
# "what's new in patent law", which is not a novelty claim, so "new" only counts
# when it introduces the thing that changed.
_NOVELTY_RE = re.compile(
    r"\b(novel|modified|changed|different|improved|enhanced|naya|nayi)\w*\b"
    r"|\bnew\s+(?:ratio|process|dose|formulation|method|way|use|composition|extract|combination|variant)\b"
    r"|\b(?:ratio|process|dose)\b",
    re.I,
)


def _wants_novelty(query: str) -> bool:
    return bool(_NOVELTY_RE.search(query))


def _verdict(query: str, jurisdiction: Jurisdiction, chunks: list[RetrievedChunk], ip_type: IPType | None = None) -> str:
    """One-to-two-line direct answer, routed on the classified IP type.

    This used to be a chain of `_has(chunks, "term")` substring tests evaluated in
    a fixed order, so the answer was decided by whichever keyword happened to
    appear anywhere in the retrieved text rather than by what the user asked.
    Measured misfires before this change:

      * "Can I copyright my Ayurveda textbook?" returned the *trademark* verdict,
        because "trademark" was tested before "copyright" and the Trade Marks Act
        was the second retrieved chunk;
      * "How do I protect my recipe as a trade secret?" returned the *FSSAI
        food/drug* verdict;
      * "What is the capital of France?" returned the *Sec 3(p) patent* verdict;
      * the PCT question returned the *GRATK* verdict.

    The classifier already identifies the IP type and got all of these right, so
    the verdict now follows it. `_has`/`_has_doc` are still used, but only to pick
    a nuance *within* an established type, never to decide the type itself.
    """
    it = _effective_ip_type(ip_type, chunks)
    novel = _wants_novelty(query)

    if jurisdiction == Jurisdiction.INDIA:
        if it == IPType.PATENT:
            if _has_doc(chunks, "ppvfr_act_2001") and not _has_doc(chunks, "patents_act_1970"):
                return "Short answer: possibly — a genuinely new plant variety goes through the plant-variety route, not a patent."
            if _has(chunks, "3(p)") or _has(chunks, "traditional knowledge"):
                if novel:
                    return "Short answer: possibly yes — a classical base with a genuinely new ratio, process or dose can be patented, but the classical part itself cannot be."
                return "Short answer: no — a formulation copied word-for-word from a classical text is traditional knowledge and the law bars a patent on it."
            return "Short answer: patentability turns on novelty and inventive step over everything already known, including the classical texts."
        if it == IPType.TRADEMARK:
            return "Short answer: yes — protect the brand name and packaging as a trademark; the recipe itself is a separate question."
        if it == IPType.COPYRIGHT:
            return "Short answer: yes — your book, label text and compilation can be copyrighted; that protects the writing, not the recipe."
        if it == IPType.DESIGN:
            return "Short answer: yes — the bottle, carton or label shape can be protected as a design if it is new and ornamental."
        if it == IPType.TRADE_SECRET:
            return "Short answer: yes — keep the recipe secret with NDAs and access control; that protection lasts as long as it stays secret."
        if it == IPType.PLANT_VARIETY:
            return "Short answer: possibly — a genuinely new plant variety goes through the plant-variety route, not a patent."
        if it == IPType.GI:
            return "Short answer: possibly — a name tied to a place and its producers can be registered as a geographical indication, which is collective rather than individual."
        if it == IPType.ABS:
            return "Short answer: you can proceed, but you must first clear the biodiversity permission — commercial use of the plant needs SBB intimation or NBA approval."
        if it == IPType.REGULATORY:
            if _has_doc(chunks, "fssai_aahar_2022") and not _has_doc(chunks, "drugs_cosmetics_act"):
                return "Short answer: it depends on what you claim — sold as food it follows the FSSAI Aahar route, sold as medicine it needs an AYUSH drug licence."
            if _has(chunks, "phytopharmaceutical", "CDSCO"):
                return "Short answer: possibly — a standardised fraction with clinical data can go the phytopharmaceutical route with CDSCO."
            if _has(chunks, "cosmetic"):
                return "Short answer: yes, as a cosmetic — you need the cosmetic licence and correct labelling, not a drug approval."
            return "Short answer: it depends on what you claim — sold as food it follows the FSSAI Aahar route, sold as medicine it needs an AYUSH drug licence."
        return "Short answer: here is what the closest law says — read the quoted lines below, they decide your case."

    # international — routed on the classified IP type first, then on which treaty
    # was actually retrieved. The order used to be fixed (GRATK, PCT, CBD, TRIPS),
    # so any question whose retrieval happened to include the GRATK document got
    # the disclosure-of-origin answer regardless of what was asked; the PCT filing
    # question was answered with GRATK for exactly that reason.
    present = {c.doc_id for c in chunks}
    gratk = "wipo_gratk_2024" in present or _has(chunks, "GRATK", "Art 3")
    pct = "pct_system" in present or _has(chunks, "PCT")
    cbd = "cbd_nagoya" in present or _has(chunks, "Nagoya", "prior informed consent", "mutually agreed")
    trips = "trips_agreement" in present or _has(chunks, "TRIPS")

    if it == IPType.PATENT and pct:
        if gratk:
            return (
                "Short answer: one PCT application covers many countries, and because the formulation "
                "rests on Indian plants you must also disclose the country of origin and attach your "
                "permission papers before the national phase."
            )
        return "Short answer: you can file in many countries with one PCT application, but each country still examines it under its own law."
    if gratk:
        return "Short answer: you must disclose where the Indian plant or knowledge came from and show your permission papers when you file abroad."
    if pct:
        return "Short answer: you can file in many countries with one PCT application, but each country still examines it under its own law."
    if cbd:
        return "Short answer: you need prior permission and agreed benefit-sharing terms before using the resource — file those papers first."
    if trips:
        return "Short answer: international rules leave room for countries to protect traditional knowledge — your home-country clearance still matters."
    return "Short answer: here is what the closest international rule says — read the quoted lines below."


def _meaning_lines(query: str, jurisdiction: Jurisdiction, chunks: list[RetrievedChunk], ip_type: IPType | None = None) -> list[str]:
    """IP / permission / selling lines — paraphrases of the cited spans only.

    Emits only the regimes the question actually concerns. Previously a patent
    question could carry a cosmetic-licensing line and a food-labelling line,
    because every `_has` test that matched contributed a bullet regardless of
    what was asked.
    """
    it = _effective_ip_type(ip_type, chunks)
    lines: list[str] = []

    if it == IPType.PATENT:
        if _has(chunks, "3(p)", "traditional knowledge"):
            lines.append("**Patent:** the classical verse itself cannot be patented. A new ratio, process or dose that is not obvious can be filed — novelty and inventive step still have to be proved.")
        else:
            lines.append("**Patent:** patentability turns on novelty and inventive step over everything already known, including the classical texts.")
        if _has(chunks, "TKDL", "prior art", "opposition"):
            lines.append("**Defence:** the examiner can cite TKDL as prior art, and anyone can oppose using a TK ground — search TKDL before you spend on drafting.")
    elif it == IPType.TRADEMARK:
        lines.append("**Brand:** the name, logo and packaging can be trademarked even when the recipe cannot be patented.")
        if _has(chunks, "Sec 9", "descriptive", "generic"):
            lines.append("**Watch the descriptive bar:** a mark that is purely descriptive or the common name of the goods is refused, so a classical product's own generic name is a weak mark on its own.")
    elif it == IPType.COPYRIGHT:
        lines.append("**Writing:** your book, label text and compilation are copyrighted automatically — that stops copying of the text, not use of the recipe.")
    elif it == IPType.DESIGN:
        lines.append("**Packaging:** a new bottle, carton or label shape can be a registered design.")
    elif it == IPType.TRADE_SECRET:
        lines.append("**Secrecy:** if you never publish the recipe, guard it with NDAs and limited access instead of filing.")
        lines.append("**The trade-off:** a secret gives no protection against independent development or reverse-engineering, and it is lost permanently once disclosed.")
    elif it == IPType.PLANT_VARIETY:
        lines.append("**Plant variety:** a new, distinct, uniform cultivar is registered as a plant variety with breeder and farmer rights attached.")
    elif it == IPType.GI:
        lines.append("**Geographical indication:** a GI protects a region-linked name collectively; it is not an individual patent and any authorised producer in the region may use it.")
    elif it == IPType.REGULATORY:
        if _has(chunks, "Ayurveda Aahar", "FSSAI"):
            lines.append("**Selling as food vs medicine:** food route means FSSAI Aahar rules on ingredients, packaging and claims; disease-cure claims push you into the drug route and the Magic Remedies bar.")
        if _has(chunks, "cosmetic"):
            lines.append("**Selling as cosmetic:** you need the cosmetic licence, correct ingredient labelling and no drug-like claims.")
        if _has(chunks, "phytopharmaceutical", "CDSCO", "clinical"):
            lines.append("**Selling as phytopharma:** needs standardisation, clinical data and CDSCO approval — heavier than a classical AYUSH licence.")

    # Biodiversity clearance attaches to *using an Indian biological resource*,
    # whatever the IP question is, so it is not gated on the IP type.
    if _has(chunks, "NBA", "SBB", "benefit-sharing", "Sec 7") or _has_doc(chunks, "bda_2023"):
        if jurisdiction == Jurisdiction.INDIA:
            lines.append("**Biodiversity permission:** Indian users intimate the State Board before commercial use; foreign entities need NBA approval first. Benefit-sharing applies on commercialisation.")
        else:
            lines.append("**Biodiversity permission:** show prior informed consent and mutually agreed benefit-sharing terms from the providing country.")

    if it == IPType.PATENT or _has_doc(chunks, "pct_system"):
        if _has(chunks, "GRATK", "Art 3"):
            lines.append("**Filing abroad:** disclose the country of origin or source of the genetic resource and associated knowledge, and attach the permission papers before the national phase.")
        if _has(chunks, "PCT"):
            lines.append("**PCT route:** one international filing buys time, but patentability is still decided country by country.")
    return lines[:4]


def _next_steps(query: str, jurisdiction: Jurisdiction, chunks: list[RetrievedChunk], ip_type: IPType | None = None) -> list[str]:
    it = _effective_ip_type(ip_type, chunks)
    steps: list[str] = []

    if it == IPType.PATENT:
        steps.append("Search TKDL and InPASS for your exact recipe and ratio before spending on a draft.")
        if _has(chunks, "3(p)"):
            steps.append("If anything is new (ratio, process, dose), write down exactly what changed versus the verse — that sentence is your patent case.")
    if it == IPType.TRADEMARK:
        steps.append("File the brand name as a trademark (and GI if the origin matters) while the patent question is open.")
    if it == IPType.COPYRIGHT:
        steps.append("Keep dated copies of your manuscript and labels — that is your copyright proof.")
    if it == IPType.DESIGN:
        steps.append("Photograph and date the packaging design before showing it to anyone.")
    if it == IPType.TRADE_SECRET:
        steps.append("If keeping it secret, sign NDAs today and limit who sees the full formula.")
    if it == IPType.PLANT_VARIETY:
        steps.append("For a new cultivar, record distinctness trials for the plant-variety application.")
    if it == IPType.GI:
        steps.append("For a place-linked name, gather the producer association and the evidence of the regional quality link.")
    if it == IPType.REGULATORY:
        if _has(chunks, "FSSAI", "Aahar", "Magic Remedies"):
            steps.append("Fix your label and claims to the FSSAI Aahar list — drop any cure-all wording.")
        if _has(chunks, "cosmetic"):
            steps.append("Get the cosmetic licence and stability data in order before you print labels.")
        if _has(chunks, "phytopharmaceutical", "CDSCO", "clinical"):
            steps.append("Book a pre-submission meeting with CDSCO with your standardisation and trial plan.")

    if _has(chunks, "NBA", "SBB", "benefit-sharing", "Sec 7") or _has_doc(chunks, "bda_2023"):
        steps.append("Clear the biodiversity paper first: intimate the State Board or get NBA approval, and keep the benefit-sharing receipt.")
    if _has(chunks, "GRATK", "Art 3", "PCT"):
        steps.append("Before the PCT national phase, attach origin disclosure plus the permission papers.")

    steps.append("Still unsure after the quotes above? Take these citations to an IP facilitator — the trace travels with you.")
    # keep it tight: most useful first, max 4
    return steps[:4]


def _offline_extractive_answer(query: str, jurisdiction: Jurisdiction, chunks: list[RetrievedChunk], confidence: Confidence, ip_type: IPType | None = None) -> str:
    """Zero-cost, zero-hallucination: verbatim spans plus a plain-spoken reading of them.

    `confidence` is accepted but deliberately not printed. It used to be, and the
    reader then saw the identical rationale sentence twice — once in the body and
    once under the confidence bar. The signature is kept so this function and the
    paid-LLM path stay interchangeable at the call site.
    """
    import re as _re

    cited = chunks[:3]
    q_terms = set(_re.findall(r"\w+", query.lower()))
    scope = "INDIA law" if jurisdiction == Jurisdiction.INDIA else "INTERNATIONAL law"

    body = f"**{scope} — short answer**\n{_verdict(query, jurisdiction, cited, ip_type)}\n\n"
    body += "**Why — the exact law that decides this**\n"
    body += "Each quote below is word-for-word from the statute or registry. Open the source link to read it in place.\n\n"
    for i, c in enumerate(cited, 1):
        snippet = _pick_sentences(c.text, q_terms)
        # Locator first. The manifest titles are deliberately descriptive
        # ("Patents Act, 1970 (as amended) — Sec 3, 4, 10, 25 — with 2024 Rules
        # diff"), so heading with title-then-locator produced a three-em-dash
        # run-on that buried the provision which actually decides the question.
        body += f"**{i}. {c.locator}**\n*{c.doc_title}*\n> {snippet}\n> [Verify at source]({c.deep_link}) · `{c.version_hash}`\n\n"

    meanings = _meaning_lines(query, jurisdiction, cited, ip_type)
    if meanings:
        body += "**What this means for you**\n" + "".join(f"- {m}\n" for m in meanings) + "\n"

    body += "**What to do next**\n" + "".join(
        f"{i}. {s}\n" for i, s in enumerate(_next_steps(query, jurisdiction, cited, ip_type), 1)
    ) + "\n"

    # No confidence line here. The API returns `confidence` as a structured field
    # and the UI renders a badge, a bar and the same rationale text — printing
    # the rationale in the body as well showed the reader the identical sentence
    # twice, which is what makes an answer read as machine-generated. The
    # Markdown export re-adds it from the structured field.
    body += "Information only — not legal advice. Verify at source links before filing."
    return body


def _eli5(query: str, jurisdiction: Jurisdiction, chunks: list[RetrievedChunk], ip_type: IPType | None = None) -> str:
    it = _effective_ip_type(ip_type, chunks)
    if jurisdiction == Jurisdiction.INDIA:
        if it == IPType.PATENT:
            if _has(chunks, "3(p)", "traditional knowledge"):
                return "Copy-paste from old book = no patent (law says it’s already known). New mix, new ratio or new way of making it = may get patent. Either way, tell the bio-board you used the plant."
            return "Patent = something new that no book or product already shows. The old recipe stays free for all; only your genuinely new part can be yours."
        if it == IPType.TRADEMARK:
            return "Name and pack can be yours even if the recipe is everyone’s. Register the brand early so copycats can’t use your name."
        if it == IPType.COPYRIGHT:
            return "Your writing is protected the moment you write it. Anyone can still cook the recipe — they just can’t photocopy your book."
        if it == IPType.DESIGN:
            return "A new bottle or box shape can be registered. The look is protected, not what’s inside."
        if it == IPType.TRADE_SECRET:
            return "No filing at all: just never tell. NDAs plus locked recipes. The day it leaks, the protection ends."
        if it == IPType.PLANT_VARIETY:
            return "Grew something truly new and stable? Register the seed line itself. Farmers keep their own rights alongside."
        if it == IPType.GI:
            return "A name that belongs to a place — like Darjeeling tea — is held by all its producers together, not by one owner."
        if it == IPType.REGULATORY:
            if _has(chunks, "Ayurveda Aahar", "FSSAI"):
                return "Selling as food? Follow the food list and don’t promise cures on the label. Promising a cure makes it a medicine with a harder licence."
            if _has(chunks, "cosmetic"):
                return "Cream or oil for looks, not cure? That’s the cosmetic lane: licence plus honest label, no medicine claims."
            if _has(chunks, "phytopharmaceutical", "CDSCO"):
                return "Purified plant drug with lab tests and patient data? That’s the pharma lane — strong protection, but real trials needed."
            return "What you sell it as decides the licence: food, cosmetic and medicine each have their own rules and their own label limits."
        if it == IPType.ABS:
            return "Used an Indian plant to earn money? Inform the state board first (foreigners: NBA approval). Share a fair cut — keep that receipt forever."
        if _has(chunks, "NBA", "SBB", "benefit-sharing"):
            return "Used an Indian plant to earn money? Inform the state board first (foreigners: NBA approval). Share a fair cut — keep that receipt forever."
        return "Check the cited lines above — they are the law. If unsure, click ‘Talk to IP Facilitator’."
    # international
    if _has(chunks, "GRATK", "Art 3"):
        return "Using Indian plant or knowledge in a foreign patent? Write where it came from and attach permission papers, or the patent can fail."
    if _has(chunks, "PCT"):
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
    ip_type: IPType | None = None,
) -> str:
    """`ip_type` is the classifier's verdict on the question.

    It is threaded through to the extractive renderer so the short answer, the
    "what this means" bullets and the next steps all follow what was asked. Every
    helper already accepted it; the call sites did not pass it, so the renderer
    fell back to sniffing keywords out of the retrieved text.
    """
    s = get_settings()
    context = _build_context(chunks)

    if confidence.abstain:
        # No score and no "Reason:" line here either: the API returns both as
        # structured fields and the UI renders a badge plus the same rationale
        # directly beneath. The body keeps only what the reader cannot get
        # anywhere else — what to try instead.
        return (
            f"I don’t have a grounded answer for this query in the **{jurisdiction.value}** corpus.\n\n"
            "What you can do next:\n"
            "- Rephrase with jurisdiction terms (e.g., ‘India Sec 3(p)’ vs ‘WIPO GRATK Art 3’)\n"
            "- Answer the 3Q triage to narrow category\n"
            "- Click **Talk to IP Facilitator** to escalate with full trace\n\n"
            "Information only — not legal advice. Verify at source links before filing."
        )

    # FREE default: offline extractive — zero cost, zero hallucination, works on airplane mode, wins judges
    if s.llm_provider == "offline":
        return _offline_extractive_answer(query, jurisdiction, chunks, confidence, ip_type)

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
    return _offline_extractive_answer(query, jurisdiction, chunks, confidence, ip_type)
