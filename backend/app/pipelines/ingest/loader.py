"""Loader — pdf/md/json → normalized docs with sha256 + version hash."""
from __future__ import annotations

import hashlib
import json
import pathlib
from dataclasses import dataclass

try:
    from pypdf import PdfReader  # type: ignore[import]
except Exception:
    PdfReader = None  # type: ignore[assignment,misc]


@dataclass(frozen=True)
class RawDoc:
    doc_id: str
    title: str
    source_type: str
    jurisdiction: str
    effective_date: str
    deep_link: str
    text: str
    sha256: str
    version_hash: str  # git short hash or content hash fallback


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _version_hash(content: str, git_hash: str | None = None) -> str:
    if git_hash:
        return git_hash[:12]
    return _sha256(content)[:12]


def load_pdf(path: pathlib.Path) -> str:
    if PdfReader is None:
        raise RuntimeError("pypdf not installed")
    reader = PdfReader(str(path))
    return "\n\n".join((page.extract_text() or "") for page in reader.pages)


def load_markdown(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: pathlib.Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    # if structured, flatten to text
    if isinstance(data, dict) and "text" in data:
        return str(data["text"])
    return json.dumps(data, ensure_ascii=False)


LOADERS = {".pdf": load_pdf, ".md": load_markdown, ".markdown": load_markdown, ".json": load_json}


def load_file(path: pathlib.Path, meta: dict, git_hash: str | None = None) -> RawDoc:
    ext = path.suffix.lower()
    loader = LOADERS.get(ext)
    if loader is None:
        raise ValueError(f"unsupported file type: {ext} — {path}")
    text = loader(path).strip()
    if not text:
        raise ValueError(f"empty document after load: {path}")
    sha = _sha256(text)
    vh = _version_hash(text, git_hash)
    return RawDoc(
        doc_id=meta.get("doc_id") or path.stem,
        title=meta.get("title") or path.stem,
        source_type=meta.get("source_type") or "statute",
        jurisdiction=meta.get("jurisdiction") or "india",
        effective_date=meta.get("effective_date") or "2024-01-01",
        deep_link=meta.get("deep_link") or "",
        text=text,
        sha256=sha,
        version_hash=vh,
    )


def load_manifest(manifest_path: pathlib.Path) -> list[dict]:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    # support both {documents: [...]} and [...]
    if isinstance(data, dict) and "documents" in data:
        return list(data["documents"])
    if isinstance(data, list):
        return data
    raise ValueError(f"invalid manifest shape: {manifest_path}")
