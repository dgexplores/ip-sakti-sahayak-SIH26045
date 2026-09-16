import pytest

from app.models.schemas import Confidence, IPType, Jurisdiction
from app.rag.generator import (
    _effective_ip_type,
    _eli5,
    _offline_extractive_answer,
    _pick_sentences,
    _verdict,
    _wants_novelty,
    generate_answer,
)
from app.rag.retriever import RetrievedChunk


def _c(
    title="Patents Act, 1970 — Sec 3(p)",
    text="An invention which, in effect, is traditional knowledge is not patentable. Sec 3(p) bars it.",
    locator="Sec 3(p)",
    jurisdiction="india",
    doc_id="patents_act_1970",
):
    return RetrievedChunk(id=doc_id, doc_id=doc_id, doc_title=title, source_type="statute", jurisdiction=jurisdiction, text=text, locator=locator, deep_link="https://example.com", version_hash="abc123", score=0.91)


def _conf(score=85, abstain=False):
    return Confidence(score=score, rationale="grounded", abstain=abstain)


def test_offline_india_contains_banner():
    ans = _offline_extractive_answer("Is classical churna patentable?", Jurisdiction.INDIA, [_c()], _conf())
    assert "INDIA" in ans
    assert "Information only" in ans
    assert "Sec 3(p)" in ans


def test_offline_international_gratk():
    c = _c(title="WIPO GRATK 2024", text="Disclosure requirement Art 3: disclose country of origin.", locator="Art 3", jurisdiction="international", doc_id="wipo_gratk_2024")
    ans = _offline_extractive_answer("WIPO GRATK disclosure?", Jurisdiction.INTERNATIONAL, [c], _conf())
    assert "INTERNATIONAL" in ans
    assert "Art 3" in ans


def test_offline_abstain_not_called_here_but_conf():
    # generator's abstain path is in generate_answer, not offline helper
    c = _c()
    low = _conf(score=12, abstain=True)
    # offline should still produce answer; abstain handled upstream
    ans = _offline_extractive_answer("q", Jurisdiction.INDIA, [c], low)
    assert "Information only" in ans


def test_eli5_simple():
    c = _c()
    s = _eli5("Is classical churna patentable?", Jurisdiction.INDIA, [c])
    assert "Copy-paste" in s or "no patent" in s.lower()


def test_eli5_gratk():
    c = _c(title="GRATK", text="x", jurisdiction="international", doc_id="wipo_gratk_2024")
    s = _eli5("GRATK PCT?", Jurisdiction.INTERNATIONAL, [c])
    assert "permission" in s.lower() or "where it came from" in s.lower()


@pytest.mark.asyncio
async def test_generate_answer_offline_path():
    chunks = [_c(), _c(title="BDA", text="NBA approval required", locator="Sec 7", jurisdiction="india", doc_id="bda_2023")]
    conf = _conf(score=82)
    ans = await generate_answer("Is novel extract patentable?", Jurisdiction.INDIA, chunks, conf)
    assert "INDIA" in ans
    assert "Information only" in ans


@pytest.mark.asyncio
async def test_generate_abstain_path():
    chunks = []
    conf = Confidence(score=12, rationale="no chunks", abstain=True)
    ans = await generate_answer("write a poem", Jurisdiction.INDIA, chunks, conf)
    assert "have a grounded answer" in ans  # handles ’ vs '


@pytest.mark.asyncio
async def test_generate_answer_forwards_ip_type():
    """`generate_answer` accepted an ip_type and never passed it on.

    The parameter existed on every helper but no call site populated it, so the
    renderer fell back to sniffing keywords out of the retrieved text.
    """
    tm = _c(
        title="Trade Marks Act, 1999",
        text="A mark that is purely descriptive cannot be registered. A classical formulation's own traditional name risks refusal.",
        locator="Sec 9",
        doc_id="trade_marks_act_1999",
    )
    conf = _conf(score=82)
    as_trademark = await generate_answer("Can I register my brand?", Jurisdiction.INDIA, [tm], conf, ip_type=IPType.TRADEMARK)
    assert "trademark" in as_trademark.lower()
    # Same span, different classification, different short answer.
    as_patent = await generate_answer("Can I register my brand?", Jurisdiction.INDIA, [tm], conf, ip_type=IPType.PATENT)
    assert as_trademark != as_patent


# ── Verdict routing ───────────────────────────────────
def _tm():
    return _c(title="Trade Marks Act, 1999", text="Trademark protects a brand name. Sec 9 bars descriptive marks.", locator="Sec 9", doc_id="trade_marks_act_1999")


def _cr():
    return _c(title="Copyright Act, 1957", text="Copyright protects literary works. A textbook compilation is protected automatically.", locator="Sec 13", doc_id="copyright_act_1957")


def test_verdict_follows_the_question_not_the_retrieved_keywords():
    """The verdict used to be a chain of `_has(chunks, "term")` tests in fixed order.

    "Can I copyright my Ayurveda textbook?" returned the *trademark* verdict,
    because "trademark" was tested before "copyright" and the Trade Marks Act was
    among the retrieved spans. Routing on the classified IP type fixes it.
    """
    chunks = [_tm(), _cr()]
    v = _verdict("Can I copyright my Ayurveda textbook?", Jurisdiction.INDIA, chunks, IPType.COPYRIGHT)
    assert "copyright" in v.lower() or "book" in v.lower()
    assert "brand" not in v.lower()


def test_verdict_is_not_decided_by_a_passing_keyword_mention():
    """"What is the capital of France?" returned the Sec 3(p) patent verdict."""
    v = _verdict("What is the capital of France?", Jurisdiction.INDIA, [_c()], IPType.UNKNOWN)
    assert "3(p)" not in v


def test_verdict_international_pct_is_not_answered_with_gratk():
    """The PCT question returned the GRATK verdict because the international
    branch tested GRATK first, regardless of what was asked."""
    gratk = _c(title="WIPO GRATK 2024", text="Art 3 disclosure of origin.", locator="Art 3", jurisdiction="international", doc_id="wipo_gratk_2024")
    pct = _c(title="PCT System", text="One international application, national phase in each country.", locator="Art 3", jurisdiction="international", doc_id="pct_system")
    v = _verdict("How do I file a PCT application?", Jurisdiction.INTERNATIONAL, [gratk, pct], IPType.PATENT)
    assert "pct" in v.lower() or "many countries" in v.lower()


def test_verdict_patent_question_never_returns_a_trademark_verdict():
    v = _verdict("Can I patent my formulation?", Jurisdiction.INDIA, [_tm(), _c()], IPType.PATENT)
    assert "brand" not in v.lower()


# ── IP type inference ─────────────────────────────────
def test_effective_ip_type_prefers_the_classifier():
    assert _effective_ip_type(IPType.COPYRIGHT, [_c()]) == IPType.COPYRIGHT


def test_effective_ip_type_scans_past_a_supporting_document():
    """The top hit is often TKDL or the pharmacopoeia, which maps to no IP type.

    Reading only `chunks[0]` threw away a clear signal sitting one position below.
    """
    tkdl = _c(title="TKDL Guidelines", text="prior art database", doc_id="tkdl_guidelines")
    assert _effective_ip_type(None, [tkdl, _c()]) == IPType.PATENT


def test_effective_ip_type_falls_back_to_the_title():
    c = _c(title="Designs Act, 2000", doc_id="unknown_fixture_id")
    assert _effective_ip_type(None, [c]) == IPType.DESIGN


def test_effective_ip_type_unknown_when_nothing_matches():
    assert _effective_ip_type(None, [_c(title="Misc", doc_id="misc")]) == IPType.UNKNOWN


# ── Novelty detection ─────────────────────────────────
@pytest.mark.parametrize(
    "query,expected",
    [
        ("Can I patent a new formulation?", True),
        ("Is my novel ratio patentable?", True),
        ("I changed the process", True),
        ("What's new in patent law?", False),
        ("Is classical churna patentable?", False),
        ("Can I patent my grandmother's recipe?", False),
    ],
)
def test_novelty_detection_is_narrow(query, expected):
    """A bare "new" appears in "what's new in patent law", which is not a novelty
    claim, so "new" only counts when it introduces the thing that changed."""
    assert _wants_novelty(query) is expected


# ── Quote integrity ───────────────────────────────────
def test_pick_sentences_returns_a_contiguous_span():
    """The quote must be an exact substring of the source.

    Sentences used to be scored independently and concatenated, so the two chosen
    sentences could come from opposite ends of the document and the result was not
    a quotation at all. On the flagship question the resulting "quote" opened with
    a source URL and a fabricated version hash.
    """
    text = (
        "Source: https://example.gov.in/act.html. "
        "Version hash: a1b2c3d4e5f6. "
        "Sec 3(p) is the traditional knowledge bar. "
        "An invention which, in effect, is traditional knowledge is not an invention. "
        "This provision is the reason classical formulations cannot be patented. "
        "Sec 25 allows opposition on the same ground."
    )
    out = _pick_sentences(text, {"traditional", "knowledge", "patentable"}, n=2)
    assert out in text, out
    assert "Source:" not in out
    assert "Version hash" not in out


def test_pick_sentences_is_verbatim():
    """Every word of the quote must appear in the source, in order."""
    text = "First sentence here. Second sentence with churna. Third one. Fourth one."
    out = _pick_sentences(text, {"churna"}, n=2)
    assert out in text
    assert "churna" in out


def test_pick_sentences_trims_metadata_from_the_edges_only():
    """Interior spans stay, so the result is still one contiguous substring."""
    text = "Note: editorial aside. The statute says a patent is barred. Sec 3(p) governs. See also: appendix."
    out = _pick_sentences(text, {"statute", "patent"}, n=3)
    assert out in text, out
    assert "Note:" not in out
    assert "See also:" not in out
    assert "patent is barred" in out


def test_offline_answer_never_quotes_a_url_or_hash_as_law():
    """A "quote" once opened with the source URL and a fabricated version hash."""
    c = _c(
        title="Patents Act, 1970",
        text="Source: https://ipindia.gov.in/ps3.html. Version hash: a1b2c3d4e5f6. Sec 3(p) bars a patent on traditional knowledge.",
        doc_id="patents_act_1970",
    )
    ans = _offline_extractive_answer("Is churna patentable?", Jurisdiction.INDIA, [c], _conf())
    quoted = [ln for ln in ans.splitlines() if ln.startswith("> ") and not ln.startswith("> [")]
    assert quoted, "expected at least one quoted span"
    for ln in quoted:
        assert "Version hash" not in ln, ln
        assert "https://ipindia" not in ln, ln
    assert any("Sec 3(p)" in ln for ln in quoted), quoted


def test_offline_answer_does_not_duplicate_the_eli5_block():
    """The plain-language paragraph used to be appended to the body *and* returned
    as answer_simple, so the reader saw it twice."""
    c = _c()
    ans = _offline_extractive_answer("Is classical churna patentable?", Jurisdiction.INDIA, [c], _conf())
    assert ans.count("Copy-paste") <= 1
