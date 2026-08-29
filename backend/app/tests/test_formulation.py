from app.rag.formulation import evaluate_formulation, FORMULATION_QUESTIONS
from app.models.schemas import FormulationAnswer, FormulationCategory

def test_classical_flow():
    ans = FormulationAnswer(q_source_text=True, q_novelty=False, q_category=FormulationCategory.CLASSICAL)
    r = evaluate_formulation(ans)
    assert r.category == FormulationCategory.CLASSICAL
    assert "Sec 3(p) bar" in r.posture_table["IP"]

def test_proprietary_flow():
    ans = FormulationAnswer(q_source_text=True, q_novelty=True, q_category=FormulationCategory.PROPRIETARY)
    r = evaluate_formulation(ans)
    assert r.category == FormulationCategory.PROPRIETARY
    assert "Patentable if novel" in r.posture_table["IP"]

def test_phytopharma():
    ans = FormulationAnswer(q_source_text=False, q_novelty=True, q_category=FormulationCategory.PHYTOPHARMACEUTICAL)
    r = evaluate_formulation(ans)
    assert r.category == FormulationCategory.PHYTOPHARMACEUTICAL

def test_cosmetic_direct():
    ans = FormulationAnswer(q_source_text=False, q_novelty=False, q_category=FormulationCategory.COSMETIC)
    r = evaluate_formulation(ans)
    assert r.category == FormulationCategory.COSMETIC

def test_incomplete_defaults_unknown_or_category():
    ans = FormulationAnswer(q_source_text=True, q_novelty=None, q_category=None)
    r = evaluate_formulation(ans)
    assert r.category == FormulationCategory.UNKNOWN

def test_questions_shape():
    assert len(FORMULATION_QUESTIONS) == 3
    assert FORMULATION_QUESTIONS[0]["key"] == "q_source_text"
    assert "options" in FORMULATION_QUESTIONS[2]
    assert len(FORMULATION_QUESTIONS[2]["options"]) == 6
