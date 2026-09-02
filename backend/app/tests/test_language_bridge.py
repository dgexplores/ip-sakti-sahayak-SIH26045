"""The interface offers Devanagari and Tamil, so people type in them.

The corpus is English. Before the bridge, an Indic-script question scored
near zero against every document, the classifier returned UNKNOWN, and the
chat route then ruled the question out of scope and abstained, even on
questions the corpus answers well. These pin that path.
"""
import pytest

from app.models.schemas import IPType, Jurisdiction
from app.rag.classifier import classify_query
from app.rag.retriever import _mock_chunks, bridge_query


@pytest.mark.parametrize(
    "query,expect_en",
    [
        ("क्या मैं पुराने नुस्खे का पेटेंट करा सकता हूँ?", "patent"),
        ("क्या मैं अपनी किताब कॉपीराइट करा सकता हूँ?", "copyright"),
        ("பழைய மருந்துக்கு பேட்டன்ட் கிடைக்குமா?", "patent"),
    ],
)
def test_bridge_adds_english_without_losing_the_original(query, expect_en):
    out = bridge_query(query)
    assert query in out, "the original question must survive, the bridge only appends"
    assert expect_en in out


def test_bridge_leaves_english_untouched():
    q = "Can I patent a classical formulation?"
    assert bridge_query(q) == q


@pytest.mark.parametrize(
    "query,expected",
    [
        ("क्या मैं अपना ब्रांड ट्रेडमार्क करा सकता हूँ?", IPType.TRADEMARK),
        ("क्या मैं अपनी किताब कॉपीराइट करा सकता हूँ?", IPType.COPYRIGHT),
        ("என் வர்த்தக முத்திரை பதிவு செய்யலாமா?", IPType.TRADEMARK),
    ],
)
def test_classifier_reads_indic_scripts(query, expected):
    """Every IP_KEYWORDS pattern is English, so without bridging the classifier
    returned UNKNOWN for any Indic question, which is what opened the
    out-of-scope branch and produced a needless abstention."""
    assert classify_query(query).ip_type == expected


def test_indic_question_retrieves_the_right_statute():
    hits = _mock_chunks(Jurisdiction.INDIA, None, 3, "क्या मैं अपनी किताब कॉपीराइट करा सकता हूँ?")
    assert hits and hits[0].doc_id == "copyright_act_1957"


def test_title_match_outranks_a_passing_body_mention():
    """The Designs Act says a formulation's recipe falls *outside* it, which is
    a body mention of "patent". A document titled "Patents Act" is about the
    word in a way that mention is not."""
    hits = _mock_chunks(Jurisdiction.INDIA, None, 1, "patent")
    assert hits[0].doc_id == "patents_act_1970"
