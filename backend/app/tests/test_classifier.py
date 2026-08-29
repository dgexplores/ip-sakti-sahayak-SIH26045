from app.rag.classifier import classify_query
from app.models.schemas import Jurisdiction, IPType

def test_jurisdiction_india():
    r = classify_query("Is classical ashwagandha churna patentable under Sec 3(p)?", Jurisdiction.INDIA)
    assert r.jurisdiction == Jurisdiction.INDIA
    assert r.ip_type == IPType.PATENT

def test_jurisdiction_intl():
    r = classify_query("WIPO GRATK disclosure for genetic resource PCT filing", Jurisdiction.INTERNATIONAL)
    assert r.jurisdiction == Jurisdiction.INTERNATIONAL

def test_formulation_trigger():
    r = classify_query("my proprietary ashwagandha extract with novel ratio for phytopharma")
    assert r.needs_formulation_flow is True

def test_abs():
    r = classify_query("Do I need NBA approval for accessing aloe from Kerala for export?")
    assert r.ip_type == IPType.ABS
