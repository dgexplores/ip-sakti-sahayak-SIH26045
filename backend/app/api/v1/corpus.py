from __future__ import annotations

from fastapi import APIRouter

from app.core.corpus import corpus_document_count, corpus_documents, corpus_version

router = APIRouter()


@router.get("/version")
async def get_corpus_version() -> dict:
    return {
        "corpus_version": corpus_version(),
        "document_count": corpus_document_count(),
        "documents": corpus_documents(limit=20),
    }


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "corpus"}
