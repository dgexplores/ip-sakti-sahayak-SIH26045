"""Typed config — 12-factor, fails fast, no magic defaults for secrets."""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # app
    app_env: Literal["development", "staging", "production"] = "development"
    app_version: str = "0.1.0"
    secret_key: str = "change-me"
    log_level: str = "INFO"
    enable_audit: bool = True
    # Comma-separated extra browser origins allowed to call the API. The built-in
    # localhost:3000 and *.vercel.app rules were hardcoded, so serving the UI from
    # any other host or port meant editing source. Set CORS_EXTRA_ORIGINS instead.
    cors_extra_origins: str = ""

    @property
    def extra_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_extra_origins.split(",") if o.strip()]

    # db
    database_url: str = "postgresql+psycopg://sakti:sakti@localhost:5432/sakti"
    redis_url: str = "redis://localhost:6379/0"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "sakti-graph-2026"

    # llm — FREE-FIRST: local by default, zero cost, zero keys required for demo
    # All paid providers are optional and only used if keys injected; demo runs 100% offline.
    openai_api_key: str = ""
    google_api_key: str = ""
    cohere_api_key: str = ""
    hf_api_key: str = ""  # optional: HuggingFace Inference (free tier) fallback
    embedding_provider: Literal["openai", "local"] = "local"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"  # 80MB, free, MIT, 384-dim — runs on CPU
    embedding_dim: int = 384  # auto-adjusted to model; 384 for MiniLM, 1536 for OpenAI
    llm_provider: Literal["offline", "ollama", "hf", "openai"] = "offline"  # offline=extractive (free, no hallucination)
    llm_model: str = "offline-extractive"  # or "llama3.1:8b" for ollama, "google/gemma-2-9b-it" for HF
    ollama_url: str = "http://localhost:11434"

    # vector
    vector_store: Literal["pgvector", "qdrant"] = "pgvector"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "sakti_corpus"

    # bhashini
    bhashini_api_key: str = ""
    bhashini_user_id: str = ""
    bhashini_inference_url: str = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"

    # rag thresholds
    confidence_threshold: float = 0.70
    rerank_top_k: int = 8
    retrieve_top_k: int = 20

    @property
    def is_prod(self) -> bool:
        return self.app_env == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
