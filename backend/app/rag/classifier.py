"""Classifier — jurisdiction + IP type + formulation trigger. Deterministic first, LLM fallback."""
from __future__ import annotations

import re

from app.models.schemas import ClassifyResponse, FormulationCategory, IPType, Jurisdiction

# ── Rule layer (cheap, judge-visible) ─────────────────
INDIA_HINTS = re.compile(
    r"\b(india|indian|ayush|ayurveda|ayurvedic|tkdl|biodiversity act|patents act|"
    r"sec\s*3\(p\)|gi tag|ppv&fr|fssai|ayush ministry)\b",
    re.I,
)
INTL_HINTS = re.compile(r"\b(wipo|pct|madrid|hague|trips|cbd|nagoya|gratk|epo|uspto|budapest|upov)\b", re.I)
FORMULATION_HINTS = re.compile(
    r"\b(classical|proprietary|phytopharma\w*|new drug|aahar|cosmetic\w*|formulation\w*|"
    r"churna|bhasma|arishta|asava|ghrita)\b",
    re.I,
)

# Ordered by specificity, and the order is load-bearing: when two types match the
# same number of times the earlier entry wins, so the narrow, unambiguous types
# come first and the broad catch-alls (design, regulatory) come last. This used to
# be dict iteration order, which meant the tie-break was accidental.
#
# Every pattern is suffix-tolerant (`patent\w*`, `trade[-\s]?marks?`) because a
# trailing `\b` after the stem silently rejected the inflected forms people
# actually type: "patentable", "patents", "trademarks". "Is my formulation
# patentable?" — the most natural phrasing of the flagship question — matched
# nothing, came back UNKNOWN, and then fell into the chat route's out-of-scope
# branch.
IP_KEYWORDS: list[tuple[IPType, re.Pattern]] = [
    # PCT is a patent filing route, so it belongs to PATENT rather than to a
    # treaty category of its own. Without it, "How do I file a PCT application?"
    # matched no IP keyword at all and classified as UNKNOWN. GRATK is the
    # disclosure-of-origin requirement attached to a patent application, and
    # "genetic resource" is the vocabulary that question is phrased in.
    (IPType.PATENT, re.compile(r"\bpatent\w*|\bprior art\b|\bnovelty\b|\binventiv\w*|\b(?:sec|section)\.?\s*3\b|\bpct\b|\bgratk\b|\bgenetic\s+resource\w*|\bcountry\s+of\s+origin\b", re.I)),
    (IPType.TRADE_SECRET, re.compile(r"\btrade[-\s]?secrets?\b|\bsecret\s+(?:recipe|formula)\b|\bconfidential\w*|\bknow[-\s]?how\b|\bnda\b|\bnon[-\s]?disclosure\b|\bundisclosed\b", re.I)),
    # `gi` before plant variety: "Can I get a GI tag for my rice variety?" mentions
    # both, and the explicit "GI tag" is the stronger signal.
    (IPType.GI, re.compile(r"\bgi\b|\bgeographical\s+indication\w*|\bdarjeeling\b|\bbasmati\b", re.I)),
    (IPType.PLANT_VARIETY, re.compile(r"\bppv\w*\b|\bplant\s+variet\w*|\bcultivars?\b|\bbreeders?\b|\b(?:new|improved|seed|crop|plant|rice|wheat|maize)\s+variet\w*", re.I)),
    (IPType.TRADEMARK, re.compile(r"\btrade[-\s]?marks?\b|\bbrands?\b|\blogos?\b|\u2122", re.I)),
    (IPType.COPYRIGHT, re.compile(r"\bcopyright\w*|\u00a9|\bliterary\b|\btextbooks?\b|\bmanuscripts?\b|\bcompilation\w*|\bauthorship\b|\btranslation\w*", re.I)),
    (IPType.ABS, re.compile(r"\babs\b|\bbiodiversity\b|\bbenefit[-\s]sharing\b|\bnba\b|\bsbb\b|\bbmc\b", re.I)),
    (IPType.DESIGN, re.compile(r"\bdesigns?\b|\bpackaging\b|\bornamental\b|\bcontainers?\b|\bbottles?\b|\bcartons?\b|\bappearance\b", re.I)),
    (IPType.REGULATORY, re.compile(r"\bdrugs?\b|\bcosmetics?\b|\bfssai\b|\bayurveda[-\s]?aahar\b|\blicen[cs]\w*|\bschedule\s+e\b|\bmagic\s+remedies\b", re.I)),
]


def classify_query(query: str, jurisdiction_hint: Jurisdiction | None = None) -> ClassifyResponse:
    # Match on the bridged query. Every pattern below is English, so a question
    # typed in Devanagari or Tamil always came back UNKNOWN, which then opened
    # the out-of-scope branch in the chat route and abstained on questions the
    # corpus answers. The interface invites those scripts, so the classifier
    # has to read them.
    from app.rag.retriever import bridge_query

    q = bridge_query(query.strip())

    # Jurisdiction, in two parts.
    #
    # `inferred` is what the *question text* points at, decided with no regard
    # for the toggle. It is reported separately so the caller can tell when the
    # reader's words and the toggle disagree — the "never conflate" guarantee is
    # only observable if that disagreement is surfaced rather than overwritten.
    #
    # `jurisdiction` is what we answer for: the explicit toggle when given, else
    # the inference. The chat route previously compared `jurisdiction` against
    # the requested value to detect a mismatch, but passing the hint in made the
    # two equal by construction, so the check could never fire.
    has_india = bool(INDIA_HINTS.search(q))
    has_intl = bool(INTL_HINTS.search(q))
    if has_india and not has_intl:
        inferred, inferred_conf = Jurisdiction.INDIA, 0.85
    elif has_intl and not has_india:
        inferred, inferred_conf = Jurisdiction.INTERNATIONAL, 0.85
    elif has_india and has_intl:
        # mixed — abstention signal: caller should keep toggles separate and re-ask
        inferred, inferred_conf = Jurisdiction.INDIA, 0.55
    else:
        inferred, inferred_conf = Jurisdiction.INDIA, 0.60  # default india for SIH context

    if jurisdiction_hint is not None:
        jurisdiction, j_conf = jurisdiction_hint, 1.0
    else:
        jurisdiction, j_conf = inferred, inferred_conf

    # IP type: highest keyword overlap, ties broken by the order above.
    best: IPType = IPType.UNKNOWN
    best_score = 0
    for ip_type, pat in IP_KEYWORDS:
        score = len(pat.findall(q))
        if score > best_score:
            best_score, best = score, ip_type
    ip_type = best if best_score > 0 else IPType.UNKNOWN
    conf = min(0.95, 0.55 + best_score * 0.12) if ip_type != IPType.UNKNOWN else 0.50
    overall = round((j_conf * 0.5 + conf * 0.5), 2)

    needs_formulation = bool(FORMULATION_HINTS.search(q)) or ip_type in (IPType.PATENT, IPType.REGULATORY, IPType.ABS)

    return ClassifyResponse(
        jurisdiction=jurisdiction,
        inferred_jurisdiction=inferred,
        inferred_jurisdiction_confidence=inferred_conf,
        ip_type=ip_type,
        confidence=overall,
        needs_formulation_flow=needs_formulation,
    )


def classify_formulation_answers(source_text: bool, novelty: bool, category: FormulationCategory) -> FormulationCategory:
    """Deterministic mapping per doc — truth table."""
    if category == FormulationCategory.COSMETIC:
        return FormulationCategory.COSMETIC
    if category == FormulationCategory.AYURVEDA_AAHAR:
        return FormulationCategory.AYURVEDA_AAHAR
    if source_text and not novelty:
        return FormulationCategory.CLASSICAL
    if source_text and novelty:
        return FormulationCategory.PROPRIETARY
    if not source_text and novelty:
        # could be phytopharma or new drug — default phytopharma, caller refines
        if category == FormulationCategory.PHYTOPHARMACEUTICAL:
            return FormulationCategory.PHYTOPHARMACEUTICAL
        return FormulationCategory.NEW_DRUG
    return FormulationCategory.UNKNOWN
