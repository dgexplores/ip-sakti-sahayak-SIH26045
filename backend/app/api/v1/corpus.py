from __future__ import annotations

import subprocess
from fastapi import APIRouter

router = APIRouter()


@router.get("/version")
async def corpus_version() -> dict:
    try:
        h = subprocess.check_output(["git", "rev-parse", "--short=12", "HEAD"], text=True).strip()
    except Exception:
        h = "nogit"
    # count docs from manifest if present
    import pathlib, json

    manifest = pathlib.Path(__file__).parents[4] / "corpus" / "manifest.json"
    count = 0
    docs = []
    if manifest.exists():
        try:
            data = json.loads(manifest.read_text())
            docs = data.get("documents") if isinstance(data, dict) else data
            count = len(docs) if isinstance(docs, list) else 0
        except Exception:
            pass
    return {"corpus_version": h, "document_count": count, "documents": docs[:20] if isinstance(docs, list) else []}


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "corpus"}
