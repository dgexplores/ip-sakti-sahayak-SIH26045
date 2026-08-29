"""Formulation flow — 3-question triage → category + posture table + citations stub."""
from __future__ import annotations

from app.models.schemas import Citation, FormulationAnswer, FormulationCategory, FormulationResult
from app.rag.classifier import classify_formulation_answers

POSTURE: dict[FormulationCategory, dict[str, str]] = {
    FormulationCategory.CLASSICAL: {
        "IP": "Sec 3(p) bar — not patentable (mere discovery of traditional knowledge). Defensive via TKDL.",
        "ABS": "Access still needs NBA/SBB intimation; benefit-sharing may apply on commercialization.",
        "Regulatory": "First Schedule classical — AYUSH license via State SLA, no new-drug approval.",
    },
    FormulationCategory.PROPRIETARY: {
        "IP": "Patentable if novel process/dosage/form (Sec 3(p) not attracted). Consider GI/trademark for brand.",
        "ABS": "NBA approval + benefit-sharing agreement if accessing Indian biological resource.",
        "Regulatory": "Proprietary Ayurveda — safety/efficacy dossier + AYUSH + possible FSSAI if Aahar overlap.",
    },
    FormulationCategory.PHYTOPHARMACEUTICAL: {
        "IP": "Patentable as new phytopharmaceutical (D&C Rules). Strong claim set + Budapest deposit if microbe.",
        "ABS": "NBA + BDA 2023 compliance; prior informed consent if TK associated.",
        "Regulatory": "CDSCO phytopharma pathway — clinical data, GMP, Schedule Y.",
    },
    FormulationCategory.NEW_DRUG: {
        "IP": "Patentable + PCT route; publish after filing to preserve novelty.",
        "ABS": "Mandatory ABS + PIC/MAT; WIPO GRATK disclosure of origin if TK/genetic resource.",
        "Regulatory": "New drug approval — CDSCO + AYUSH joint, full clinical trial.",
    },
    FormulationCategory.AYURVEDA_AAHAR: {
        "IP": "Trademark + trade dress; recipe may be trade secret; patent unlikely.",
        "ABS": "Intimation to SBB; benefit-sharing on commercial scale.",
        "Regulatory": "FSSAI Ayurveda Aahar Regulations 2022 — packaging, claims, Magic Remedies guardrail.",
    },
    FormulationCategory.COSMETIC: {
        "IP": "Design + trademark; process patent possible.",
        "ABS": "SBB intimation; source declaration.",
        "Regulatory": "D&C Cosmetic Rules — AYUSH/state license, label, cruelty-free norms.",
    },
    FormulationCategory.UNKNOWN: {
        "IP": "Needs triage — answer follow-ups to classify.",
        "ABS": "Assume ABS screening required.",
        "Regulatory": "Do not market until license category confirmed.",
    },
}

NEXT_STEPS: dict[FormulationCategory, list[str]] = {
    FormulationCategory.CLASSICAL: ["Search TKDL for prior art", "File GI/trademark for brand", "Intimate SBB on commercialization"],
    FormulationCategory.PROPRIETARY: ["Prior-art search (InPASS + TKDL)", "Draft patent + ABS filing", "AYUSH proprietary dossier"],
    FormulationCategory.PHYTOPHARMACEUTICAL: ["CDSCO pre-submission meeting", "Budapest deposit if applicable", "NBA ABS + GRATK disclosure"],
    FormulationCategory.NEW_DRUG: ["Novelty search + PCT filing strategy", "CBD/Nagoya due diligence", "Full clinical plan"],
    FormulationCategory.AYURVEDA_AAHAR: ["FSSAI Aahar checklist", "Label/claim compliance (Magic Remedies Act)", "SBB intimation"],
    FormulationCategory.COSMETIC: ["Cosmetic license, stability data", "Trademark search", "SBB intimation"],
    FormulationCategory.UNKNOWN: ["Answer the 3 triage questions above"],
}


def evaluate_formulation(ans: FormulationAnswer, citations: list[Citation] | None = None) -> FormulationResult:
    cat = FormulationCategory.UNKNOWN
    if ans.is_complete():
        cat = classify_formulation_answers(bool(ans.q_source_text), bool(ans.q_novelty), ans.q_category or FormulationCategory.UNKNOWN)
    # fallback: if category explicitly chosen even when incomplete, respect it
    if not ans.is_complete() and ans.q_category and ans.q_category != FormulationCategory.UNKNOWN:
        cat = ans.q_category

    return FormulationResult(
        category=cat,
        posture_table=POSTURE[cat],
        next_steps=NEXT_STEPS[cat],
        citations=citations or [],
    )


# Questions for UI — keep in sync with frontend
FORMULATION_QUESTIONS = [
    {
        "key": "q_source_text",
        "label": "Is the formulation/recipe found in a classical Ayurveda text (Charaka/Sushruta/First Schedule)?",
        "type": "boolean",
        "help": "Yes → classical path (Sec 3(p) bar, TKDL). No → proprietary/phytopharma/new-drug.",
    },
    {
        "key": "q_novelty",
        "label": "Does it have a novel ingredient, ratio, process, or dosage not in the classical verse?",
        "type": "boolean",
        "help": "Novelty is required for patentability.",
    },
    {
        "key": "q_category",
        "label": "Intended market category?",
        "type": "enum",
        "options": [c.value for c in FormulationCategory if c != FormulationCategory.UNKNOWN],
        "help": "Determines AYUSH vs FSSAI vs CDSCO vs cosmetic route.",
    },
]
