"""Classifier — jurisdiction + IP type + formulation trigger. Deterministic first, LLM fallback."""
from __future__ import annotations

import re

from app.models.schemas import ClassifyResponse, FormulationCategory, IPType, Jurisdiction

# ── Rule layer (cheap, judge-visible) ─────────────────
INDIA_HINTS = re.compile(r"\b(india|indian|ayush|ayurveda|tkdl|biodiversity act|patents act|sec\s*3\(p\)|gi tag|ppv&fr|fssai|ayush ministry)\b", re.I)
INTL_HINTS = re.compile(r"\b(wipo|pct|madrid|hague|trips|cbd|nagoya|gratk|epo|uspto|budapest|upov)\b", re.I)
FORMULATION_HINTS = re.compile(r"\b(classical|proprietary|phytopharma|new drug|aahar|cosmetic|formulation|churna|bhasma|arishta|asava|ghrita)\b", re.I)

IP_KEYWORDS: dict[IPType, re.Pattern] = {
    IPType.PATENT: re.compile(r"\b(patent|prior art|novelty|inventive|sec\s*3\(|section 3|claim)\b", re.I),
    IPType.GI: re.compile(r"\b(gi|geographical indication|darjeeling|basmati|origin)\b", re.I),
    IPType.TRADEMARK: re.compile(r"\b(trademark|trade mark|brand|logo|™)\b", re.I),
    IPType.PLANT_VARIETY: re.compile(r"\b(ppv|plant variety|cultivar|breeder)\b", re.I),
    IPType.ABS: re.compile(r"\b(abs|biodiversity|benefit sharing|nba|sbb|bmc|access.*biological)\b", re.I),
    IPType.REGULATORY: re.compile(r"\b(drug|cosmetic|fssai|ayurveda[-\s]?aahar|license|schedule e|magic remedies)\b", re.I),
}


def classify_query(query: str, jurisdiction_hint: Jurisdiction | None = None) -> ClassifyResponse:
    q = query.strip()
    # jurisdiction: explicit toggle wins; else infer, but never silently conflate
    if jurisdiction_hint is not None:
        jurisdiction = jurisdiction_hint
        j_conf = 1.0
    else:
        has_india = bool(INDIA_HINTS.search(q))
        has_intl = bool(INTL_HINTS.search(q))
        if has_india and not has_intl:
            jurisdiction, j_conf = Jurisdiction.INDIA, 0.85
        elif has_intl and not has_india:
            jurisdiction, j_conf = Jurisdiction.INTERNATIONAL, 0.85
        elif has_india and has_intl:
            # mixed — abstention signal: caller should keep toggles separate and re-ask
            jurisdiction, j_conf = Jurisdiction.INDIA, 0.55
        else:
            jurisdiction, j_conf = Jurisdiction.INDIA, 0.60  # default india for SIH context

    # IP type: highest keyword overlap
    best: IPType = IPType.UNKNOWN
    best_score = 0
    for ip_type, pat in IP_KEYWORDS.items():
        score = len(pat.findall(q))
        if score > best_score:
            best_score, best = score, ip_type
    # threshold
    ip_type = best if best_score > 0 else IPType.UNKNOWN
    conf = min(0.95, 0.55 + best_score * 0.12) if ip_type != IPType.UNKNOWN else 0.50
    # combine with jurisdiction confidence
    overall = round((j_conf * 0.5 + conf * 0.5), 2)

    needs_formulation = bool(FORMULATION_HINTS.search(q)) or ip_type in (IPType.PATENT, IPType.REGULATORY, IPType.ABS)

    return ClassifyResponse(
        jurisdiction=jurisdiction,
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
