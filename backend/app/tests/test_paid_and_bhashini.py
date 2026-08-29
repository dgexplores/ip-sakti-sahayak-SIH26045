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

@pytest.mark.asyncio
async def test_translate_free_mock():
    out = await translate("Sec 3(p) bars patent for TK", source_lang="en", target_lang="hi")
    # without Bhashini key, mock prefixes but preserves term
    assert "Sec 3(p)" in out

@pytest.mark.asyncio
async def test_translate_same_lang():
    out = await translate("hello", source_lang="en", target_lang="en")
    assert out == "hello"
