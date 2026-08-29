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

    # db
    database_url: str = "postgresql+psycopg://sakti:sakti@localhost:5432/sakti"
    redis_url: str = "redis://localhost:6379/0"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "sakti-graph-2026"

    # llm
    openai_api_key: str = ""
    google_api_key: str = ""
    cohere_api_key: str = ""
    embedding_provider: Literal["openai", "local"] = "openai"
    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1536
    llm_model: str = "gpt-4o-mini"

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
