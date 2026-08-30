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


def test_every_ip_type_is_routable():
    """Every IPType the PS names must be reachable from a plain-language question.

    COPYRIGHT, DESIGN and TRADE_SECRET were declared in the enum but had no
    entry in IP_KEYWORDS, so they could never be returned. Copyright was the
    worst case: corpus content existed the whole time but was unreachable, and
    the query fell through to UNKNOWN, which the chat route treats as an
    out-of-scope signal and can turn into a needless abstention.
    """
    cases = {
        IPType.PATENT: "Is classical churna patentable under Sec 3(p)?",
        IPType.GI: "GI tag for Kerala ayurveda oil",
        IPType.TRADEMARK: "Can I trademark my brand name?",
        IPType.COPYRIGHT: "Can I copyright my Ayurveda textbook compilation?",
        IPType.DESIGN: "Can I register the design of my churna bottle packaging?",
        IPType.TRADE_SECRET: "How do I protect my secret family recipe as a trade secret?",
        IPType.PLANT_VARIETY: "plant variety breeder registration",
        IPType.ABS: "Do I need NBA approval for benefit sharing?",
        IPType.REGULATORY: "FSSAI license for ayurveda aahar",
    }
    for expected, query in cases.items():
        assert classify_query(query).ip_type == expected, query
