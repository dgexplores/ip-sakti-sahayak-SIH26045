"""Embedder — FREE-FIRST: local MiniLM default, zero keys, zero cost, CPU-friendly."""
from __future__ import annotations

import hashlib
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
        self.dim = 1536 if "small" in model else 3072

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not self.api_key:
            return [_fake_embed(t, self.dim) for t in texts]
        async with httpx.AsyncClient(timeout=30) as client:
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
                items = sorted(data["data"], key=lambda x: x["index"])
                out.extend([it["embedding"] for it in items])
            return out


class LocalEmbedder:
    """Free, offline, MIT. 80MB, runs on CPU, no API key, no billing."""

    dim = 384

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        if SentenceTransformer is None:
            # graceful degradation: hash embed so demo never crashes when transformers missing
            self.model = None  # type: ignore[assignment]
            self.model_name = model_name
            self.dim = 384
            return
        try:
            self.model = SentenceTransformer(model_name)
            self.dim = self.model.get_sentence_embedding_dimension() or 384
            self.model_name = model_name
        except Exception:
            # offline no-cache: fallback to hash
            self.model = None  # type: ignore[assignment]
            self.model_name = model_name
            self.dim = 384

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if self.model is None:
            return [_fake_embed(t, self.dim) for t in texts]
        import anyio  # type: ignore[import]

        def _run() -> list[list[float]]:
            arr = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)  # type: ignore[union-attr]
            return [row.tolist() for row in arr]

        return await anyio.to_thread.run_sync(_run)


def _fake_embed(text: str, dim: int) -> list[float]:
    """Deterministic hash vector — free, offline, test-stable. Never billed."""
    h = hashlib.sha256(text.encode()).digest()
    vals: list[float] = []
    while len(vals) < dim:
        for b in h:
            vals.append((b / 255.0) * 2 - 1)
            if len(vals) >= dim:
                break
        h = hashlib.sha256(h).digest()
    norm = sum(x * x for x in vals) ** 0.5 or 1
    return [x / norm for x in vals[:dim]]


def get_embedder() -> Embedder:
    from app.core.config import get_settings

    s = get_settings()
    # FREE default: local. OpenAI only if explicitly requested + key present.
    if s.embedding_provider == "openai" and s.openai_api_key:
        return OpenAIEmbedder(api_key=s.openai_api_key, model=s.embedding_model)
    # Hash fallback keeps tests & offline demo alive even before model download
    return LocalEmbedder(model_name=s.embedding_model if s.embedding_provider == "local" else "sentence-transformers/all-MiniLM-L6-v2")
