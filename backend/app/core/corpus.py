"""Single source of truth for the corpus version hash shown across the API and UI."""
from __future__ import annotations

import hashlib
import json
import pathlib

_MANIFEST = pathlib.Path(__file__).parents[3] / "corpus" / "manifest.json"


def _load_manifest() -> list[dict]:
    if not _MANIFEST.exists():
        return []
    try:
        data = json.loads(_MANIFEST.read_text())
        docs = data.get("documents") if isinstance(data, dict) else data
        return docs if isinstance(docs, list) else []
    except Exception:
        return []


def corpus_version() -> str:
    """Stable hash of manifest doc_ids. Works with or without .git, same value everywhere."""
    docs = _load_manifest()
    if not docs:
        return hashlib.sha256(b"sakti-corpus-v1").hexdigest()[:12]
    ids = "".join(sorted(d.get("doc_id", "") for d in docs))
    return hashlib.sha256(ids.encode()).hexdigest()[:12]


def corpus_document_count() -> int:
    return len(_load_manifest())


def corpus_documents(limit: int = 20) -> list[dict]:
    return _load_manifest()[:limit]
