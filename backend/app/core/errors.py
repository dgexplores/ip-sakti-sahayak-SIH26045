"""Central error taxonomy — no generic 500 leaks."""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


class SaktiError(Exception):
    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(SaktiError):
    status_code = 422
    code = "validation_error"


class NotFoundError(SaktiError):
    status_code = 404
    code = "not_found"


class UpstreamError(SaktiError):
    status_code = 502
    code = "upstream_error"


class CorpusNotReadyError(SaktiError):
    status_code = 503
    code = "corpus_not_ready"


async def sakti_exception_handler(_: Request, exc: SaktiError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
    )
