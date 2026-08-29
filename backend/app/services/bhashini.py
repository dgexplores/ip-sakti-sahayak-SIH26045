"""Bhashini service — ASR/TTS pipeline with legal-term preservation + cache."""
from __future__ import annotations

import hashlib
import re

import httpx

from app.core.config import get_settings

# legal terms that must never be translated
PRESERVE_TERMS = [
    r"Sec\s*3\(p\)",
    r"Section\s+\d+[A-Za-z\(\)]*",
    r"Article\s+\d+",
    r"GRATK",
    r"TKDL",
    r"InPASS",
    r"NBA",
    r"SBB",
    r"BMC",
    r"PCT",
    r"TRIPS",
    r"CBD",
    r"Nagoya",
    r"WIPO",
    r"FSSAI",
]
PRESERVE_RE = re.compile("(" + "|".join(PRESERVE_TERMS) + ")", re.I)

# naive in-memory cache (MVP); stage 3 → Redis
_CACHE: dict[str, str] = {}


def _cache_key(text: str, src: str, tgt: str) -> str:
    return hashlib.sha256(f"{src}->{tgt}:{text}".encode()).hexdigest()[:16]


def _protect_terms(text: str) -> tuple[str, dict[str, str]]:
    """Replace preserved terms with placeholders before translation."""
    placeholders: dict[str, str] = {}
    def _repl(m: re.Match) -> str:
        ph = f"__TERM_{len(placeholders)}__"
        placeholders[ph] = m.group(0)
        return ph
    protected = PRESERVE_RE.sub(_repl, text)
    return protected, placeholders


def _restore_terms(text: str, placeholders: dict[str, str]) -> str:
    for ph, orig in placeholders.items():
        text = text.replace(ph, orig)
    return text


async def translate(text: str, source_lang: str = "en", target_lang: str = "hi") -> str:
    """Translate via Bhashini Dhruva pipeline; fallback to identity if no key (dev)."""
    if source_lang == target_lang or not text.strip():
        return text
    ck = _cache_key(text, source_lang, target_lang)
    if ck in _CACHE:
        return _CACHE[ck]

    s = get_settings()
    if not s.bhashini_api_key:
        # offline mock — keeps demo runnable, signals missing key
        out = f"[Bhashini mock {source_lang}->{target_lang}] {text}"
        _CACHE[ck] = out
        return out

    protected, placeholders = _protect_terms(text)
    payload = {
        "pipelineTasks": [
            {
                "taskType": "translation",
                "config": {"language": {"sourceLanguage": source_lang, "targetLanguage": target_lang}},
            }
        ],
        "inputData": {"input": [{"source": protected}]},
    }
    headers = {"Authorization": s.bhashini_api_key, "Content-Type": "application/json"}
    if s.bhashini_user_id:
        headers["userID"] = s.bhashini_user_id

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(s.bhashini_inference_url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        translated = (
            data.get("pipelineResponse", [{}])[0]
            .get("output", [{}])[0]
            .get("target", protected)
        )
        restored = _restore_terms(translated, placeholders)
        _CACHE[ck] = restored
        return restored


async def asr(audio_base64: str, language: str = "hi") -> str:
    """ASR via Bhashini — mock fallback."""
    s = get_settings()
    if not s.bhashini_api_key or not audio_base64:
        return "[ASR mock] अश्वगंधा चूर्ण पेटेंट योग्य है?"
    # real pipelineTasks: asr
    payload = {
        "pipelineTasks": [{"taskType": "asr", "config": {"language": {"sourceLanguage": language}}}],
        "inputData": {"audio": [{"audioContent": audio_base64}]},
    }
    headers = {"Authorization": s.bhashini_api_key}
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(s.bhashini_inference_url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return data.get("pipelineResponse", [{}])[0].get("output", [{}])[0].get("source", "")


async def tts(text: str, language: str = "hi") -> str:
    """TTS via Bhashini — returns base64 audio mock."""
    s = get_settings()
    if not s.bhashini_api_key:
        return ""  # frontend hides player if empty
    protected, placeholders = _protect_terms(text)
    payload = {
        "pipelineTasks": [{"taskType": "tts", "config": {"language": {"sourceLanguage": language}}}],
        "inputData": {"input": [{"source": protected}]},
    }
    headers = {"Authorization": s.bhashini_api_key}
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(s.bhashini_inference_url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        audio = data.get("pipelineResponse", [{}])[0].get("audio", [{}])[0].get("audioContent", "")
        return audio
