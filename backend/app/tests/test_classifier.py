import pytest

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


@pytest.mark.parametrize(
    "query,expected",
    [
        # A trailing \b after the stem rejected every inflected form, so the most
        # natural phrasing of the flagship question classified as UNKNOWN, which
        # the chat route reads as an out-of-scope signal.
        ("Is my Ayurvedic formulation patentable?", IPType.PATENT),
        ("Is this patented already?", IPType.PATENT),
        ("How do patents work in India?", IPType.PATENT),
        ("How do I file a PCT application?", IPType.PATENT),
        ("Can I register several trademarks?", IPType.TRADEMARK),
        ("Do I need a licence to sell this?", IPType.REGULATORY),
    ],
)
def test_classifier_matches_inflected_forms(query, expected):
    assert classify_query(query).ip_type == expected, query


@pytest.mark.parametrize(
    "query",
    [
        "What is the capital of France?",
        "Who won the 1998 world cup?",
        "asdfgh qwerty zxcvb",
    ],
)
def test_classifier_says_unknown_rather_than_guessing(query):
    """An unmatched question must be UNKNOWN, not the first keyword in the list."""
    assert classify_query(query).ip_type == IPType.UNKNOWN


def test_classifier_reports_the_regimes_the_question_text_points_at():
    """`inferred_jurisdiction` ignores the toggle on purpose.

    The chat route compares it against the toggle to detect a mismatch. Passing
    the toggle in as a hint used to make the classifier echo it back, so the
    comparison was false by construction and could never fire.
    """
    r = classify_query("What is the WIPO GRATK disclosure requirement?", Jurisdiction.INDIA)
    assert r.jurisdiction == Jurisdiction.INDIA  # we answer for the toggle
    assert r.inferred_jurisdiction == Jurisdiction.INTERNATIONAL  # the words say otherwise
    assert r.inferred_jurisdiction_confidence >= 0.85

    r2 = classify_query("Is classical churna patentable?", Jurisdiction.INTERNATIONAL)
    assert r2.jurisdiction == Jurisdiction.INTERNATIONAL
    assert r2.inferred_jurisdiction == Jurisdiction.INDIA

