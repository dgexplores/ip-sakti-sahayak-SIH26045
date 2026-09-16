import pytest
from app.services.paid_connector import check_paid_access, request_consent
from app.services.bhashini import translate, _protect_terms, _restore_terms

def test_paid_not_requested():
    r = check_paid_access(False, None)
    assert r.allowed is False

def test_paid_no_consent():
    r = check_paid_access(True, None)
    assert r.allowed is False

def test_paid_invalid_consent():
    r = check_paid_access(True, "bad_id")
    assert r.allowed is False

def test_paid_allowed():
    cr = request_consent("registry search", "anon")
    assert cr.consent_id.startswith("consent_")
    r = check_paid_access(True, cr.consent_id)
    assert r.allowed is True

def test_protect_terms():
    text = "Sec 3(p) and WIPO GRATK Art 3"
    protected, placeholders = _protect_terms(text)
    assert "__TERM_" in protected
    restored = _restore_terms(protected, placeholders)
    assert restored == text


def test_protect_terms_shields_source_links_and_version_hash():
    """The answer body is markdown the reader is meant to act on.

    A translated "Verify at source" link is a broken link, and a mangled
    `version_hash` no longer identifies the span the answer was drawn from, so
    both have to be lifted out of the text before it goes to the translator.
    """
    text = "Verify at [source](https://ipindia.gov.in/ps3.html) · `4105ccdf55d7`"
    protected, placeholders = _protect_terms(text)
    assert "https://ipindia.gov.in/ps3.html" not in protected
    assert "4105ccdf55d7" not in protected
    assert _restore_terms(protected, placeholders) == text


@pytest.mark.asyncio
async def test_translate_without_key_returns_text_unchanged():
    """No key means nothing was translated, so the text must come back verbatim.

    This used to return "[Bhashini mock en->hi] Sec 3(p) bars patent for TK" —
    a debug string in the middle of the legal answer a user actually reads. The
    old test only asserted the term survived, so the prefix went unnoticed.
    """
    text = "Sec 3(p) bars patent for TK"
    out = await translate(text, source_lang="en", target_lang="hi")
    assert out == text
    assert "mock" not in out.lower()


@pytest.mark.asyncio
async def test_translate_same_lang():
    out = await translate("hello", source_lang="en", target_lang="en")
    assert out == "hello"


@pytest.mark.asyncio
async def test_asr_without_key_raises_rather_than_inventing_a_query():
    """A fabricated transcript silently answered a different question.

    With no Bhashini key this used to return the hardcoded string
    "[ASR mock] अश्वगंधा चूर्ण पेटेंट योग्य है?", which the chat route accepted as
    the user's query. Uploading audio therefore produced a confident answer about
    ashwagandha that the reader never asked for.
    """
    from app.services.bhashini import asr

    with pytest.raises(Exception) as ei:
        await asr("ZmFrZQ==", language="hi")
    assert "mock" not in str(ei.value).lower()

