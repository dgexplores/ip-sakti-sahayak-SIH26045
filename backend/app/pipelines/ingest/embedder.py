"""Embedder abstraction — OpenAI or local sentence-transformers, batched + cached."""
from __future__ import annotations

import hashlib
import os
from typing import Protocol

import httpx

try:
    from sentence_transformers import SentenceTransformer  # type: ignore[import]
except Exception:
    SentenceTransformer = None  # type: ignore[assignment,misc]


class Embedder(Protocol):
    dim: int

    async def embed(self, texts: list[str]) -> list[list[float]]: ...


class OpenAIEmbedder:
    dim = 1536

    def __init__(self, api_key: str, model: str = "text-embedding-3-small") -> None:
        self.api_key = api_key
        self.model = model
        # dim varies by model
        self.dim = 1536 if "small" in model else 3072

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not self.api_key:
            # deterministic fake embeddings for local dev without key (never used in prod)
            return [_fake_embed(t, self.dim) for t in texts]
        async with httpx.AsyncClient(timeout=30) as client:
            # batch in 64
            out: list[list[float]] = []
            for i in range(0, len(texts), 64):
                batch = texts[i : i + 64]
                resp = await client.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"model": self.model, "input": batch},
                )
                resp.raise_for_status()
                data = resp.json()
                # sort by index to guarantee order
                items = sorted(data["data"], key=lambda x: x["index"])
                out.extend([it["embedding"] for it in items])
            return out


class LocalEmbedder:
    dim = 384  # MiniLM default

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        if SentenceTransformer is None:
            raise RuntimeError("sentence-transformers not installed; pip install sentence-transformers")
        self.model = SentenceTransformer(model_name)
        self.dim = self.model.get_sentence_embedding_dimension() or 384

    async def embed(self, texts: list[str]) -> list[list[float]]:
        # run in thread to not block event loop
        import anyio  # type: ignore[import]

        def _run() -> list[list[float]]:
            arr = self.model.encode(texts, normalize_embeddings=True)
            return [row.tolist() for row in arr]

        return await anyio.to_thread.run_sync(_run)


def _fake_embed(text: str, dim: int) -> list[float]:
    """Deterministic hash-based fake vector — useful for tests/offline."""
    h = hashlib.sha256(text.encode()).digest()
    # repeat hash to fill dim
    vals: list[float] = []
    while len(vals) < dim:
        for b in h:
            vals.append((b / 255.0) * 2 - 1)
            if len(vals) >= dim:
                break
        h = hashlib.sha256(h).digest()
    # l2 normalize
    norm = sum(x * x for x in vals) ** 0.5 or 1
    return [x / norm for x in vals[:dim]]


def get_embedder() -> Embedder:
    from app.core.config import get_settings

    s = get_settings()
    if s.embedding_provider == "local":
        return LocalEmbedder()
    return OpenAIEmbedder(api_key=s.openai_api_key, model=s.embedding_model)
