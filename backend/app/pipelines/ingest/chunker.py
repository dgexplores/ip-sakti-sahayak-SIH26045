"""Chunker — recursive, section-aware, token-budgeted. Idempotent."""
from __future__ import annotations

import re
from dataclasses import dataclass

# keep chunker dependency-free; token count approximated (1 token ≈ 0.75 words)
# swap to tiktoken if available for exact counts

try:
    import tiktoken  # type: ignore[import]

    _enc = tiktoken.get_encoding("cl100k_base")

    def count_tokens(text: str) -> int:
        return len(_enc.encode(text))

except Exception:

    def count_tokens(text: str) -> int:
        return max(1, int(len(text.split()) / 0.75))


_SECTION_RE = re.compile(r"^(#{1,3}\s+.+|Section\s+\d+.*|Sec\.?\s*\d+.*|Article\s+\d+.*)$", re.MULTILINE)


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    text: str
    locator: str
    token_count: int


def split_on_sections(text: str) -> list[tuple[str, str]]:
    """Return list of (section_title, section_text). Fallback to whole doc if no headings."""
    matches = list(_SECTION_RE.finditer(text))
    if not matches:
        return [("Document", text)]
    sections: list[tuple[str, str]] = []
    for i, m in enumerate(matches):
        title = m.group(1).strip()[:120]
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections.append((title, text[start:end].strip()))
    return sections


def chunk_text(
    text: str,
    doc_id: str,
    chunk_size: int = 800,
    overlap: int = 120,
) -> list[Chunk]:
    chunks: list[Chunk] = []
    sections = split_on_sections(text)
    global_idx = 0
    for section_title, section_text in sections:
        # sliding window over section
        # split roughly by tokens, but respect sentence boundaries where possible
        sentences = re.split(r"(?<=[.!?])\s+", section_text)
        cur = ""
        cur_tokens = 0
        for sent in sentences:
            st = count_tokens(sent)
            if cur_tokens + st > chunk_size and cur:
                chunks.append(
                    Chunk(
                        chunk_id=f"{doc_id}#{global_idx:04d}",
                        text=cur.strip(),
                        locator=section_title,
                        token_count=cur_tokens,
                    )
                )
                global_idx += 1
                # overlap: keep tail
                if overlap > 0 and cur_tokens > overlap:
                    # approximate overlap by words
                    words = cur.split()
                    keep = int(overlap * 0.75)
                    cur = " ".join(words[-keep:]) + " " + sent
                    cur_tokens = count_tokens(cur)
                else:
                    cur = sent
                    cur_tokens = st
            else:
                cur = f"{cur} {sent}".strip() if cur else sent
                cur_tokens += st
        if cur.strip():
            chunks.append(
                Chunk(
                    chunk_id=f"{doc_id}#{global_idx:04d}",
                    text=cur.strip(),
                    locator=section_title,
                    token_count=count_tokens(cur),
                )
            )
            global_idx += 1
    return chunks
