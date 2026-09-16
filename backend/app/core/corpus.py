"""Single source of truth for the corpus version hash shown across the API and UI."""
from __future__ import annotations

import hashlib
import json
import os
import pathlib


def _resolve_corpus_dir() -> pathlib.Path:
    """Locate `corpus/` without depending on this file's depth in the tree.

    The original was `Path(__file__).parents[3] / "corpus"`, which is correct for
    the local layout — `repo/backend/app/core/corpus.py` — and wrong in the
    container, where the same file sits at `/app/app/core/corpus.py` and
    `parents[3]` is `/`. Docker Compose mounts the corpus at `/app/corpus`, so the
    resolved path `/corpus` did not exist: the manifest loaded as empty, the
    offline index came back empty, and `corpus_version()` fell through to its
    placeholder hash.

    That placeholder is `"sakti-corpus-v1"` — the same string the response header
    was separately hardcoded to. The two wrong values agreed with each other, so
    the defect produced no visible contradiction and `make up`, the documented
    primary path, silently ran without a corpus.

    Resolution order: `CORPUS_DIR` if set, then the nearest ancestor (or the CWD)
    that actually contains `corpus/manifest.json`.
    """
    override = os.getenv("CORPUS_DIR")
    if override:
        candidate = pathlib.Path(override)
        if (candidate / "manifest.json").exists():
            return candidate

    here = pathlib.Path(__file__).resolve()
    cwd = pathlib.Path.cwd().resolve()
    seen: set[pathlib.Path] = set()
    for base in (*here.parents, *cwd.parents, cwd):
        if base in seen:
            continue
        seen.add(base)
        candidate = base / "corpus"
        if (candidate / "manifest.json").exists():
            return candidate

    # Nothing found. Fall back to the original guess so the error message a caller
    # sees still points somewhere sensible.
    return here.parents[3] / "corpus" if len(here.parents) > 3 else cwd / "corpus"


CORPUS_DIR = _resolve_corpus_dir()
_MANIFEST = CORPUS_DIR / "manifest.json"


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


def corpus_documents(limit: int | None = 20) -> list[dict]:
    """Manifest entries. Pass limit=None for all of them, the API view caps at 20."""
    docs = _load_manifest()
    return docs if limit is None else docs[:limit]
