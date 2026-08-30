"""FastAPI entry — senior-grade: typed, CORS-tight, health, version, audit."""
from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import audit as audit_router
from app.api.v1 import chat as chat_router
from app.api.v1 import classify as classify_router
from app.api.v1 import corpus as corpus_router
from app.core.config import get_settings
from app.core.errors import SaktiError, sakti_exception_handler
from app.core.logging import get_logger, setup_logging

setup_logging()
logger = get_logger("api")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    logger.info("startup", version=settings.app_version, env=settings.app_env)
    yield
    logger.info("shutdown")


app = FastAPI(
    title="IP-SAKTI Sahayak API",
    version=settings.app_version,
    description="RAG for Ayurveda IP & regulatory guidance — jurisdiction-aware, citation-grounded.",
    lifespan=lifespan,
)

# CORS — allow frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(SaktiError, sakti_exception_handler)  # type: ignore[arg-type]


@app.middleware("http")
async def add_request_id(request: Request, call_next):  # type: ignore[no-untyped-def]
    import uuid

    rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
    start = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    response.headers["X-Corpus-Version"] = "sakti-corpus-v1"
    response.headers["X-Response-Time"] = f"{(time.perf_counter()-start)*1000:.1f}ms"
    return response


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "version": settings.app_version, "env": settings.app_env}


@app.get("/")
async def root() -> dict:
    return {"service": "IP-SAKTI Sahayak", "version": settings.app_version, "docs": "/docs", "health": "/health"}


# v1 routers
app.include_router(chat_router.router, prefix="/api/v1", tags=["chat"])
app.include_router(classify_router.router, prefix="/api/v1", tags=["classify"])
app.include_router(corpus_router.router, prefix="/api/v1/corpus", tags=["corpus"])
app.include_router(audit_router.router, prefix="/api/v1", tags=["audit"])


@app.exception_handler(Exception)
async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("unhandled", path=str(request.url), error=str(exc))
    return JSONResponse(status_code=500, content={"error": {"code": "internal_error", "message": "Internal error. Try again or escalate."}})
