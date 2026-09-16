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

# Markdown presentation markers. The corpus files are markdown, so a chunk used
# to carry its "##" heading markers, ">" blockquote markers and "-" bullets into
# the index — and from there into the answer, where the quote is already inside a
# styled blockquote. A span beginning "> " then rendered as a nested quote, and
# "##" appeared as literal hashes in the middle of a sentence.
_MD_HEADING = re.compile(r"^\s{0,3}#{1,6}\s*", re.MULTILINE)
_MD_QUOTE = re.compile(r"^\s{0,3}>\s?", re.MULTILINE)
_MD_BULLET = re.compile(r"^\s{0,3}[-*+]\s+", re.MULTILINE)
_MD_STRONG = re.compile(r"\*\*(.+?)\*\*")
_MD_CODE = re.compile(r"`([^`]+)`")
_WS_RUN = re.compile(r"\s+")


def plain_text(text: str) -> str:
    """Strip markdown presentation from chunk text without changing any word.

    The section heading is preserved separately as the chunk's `locator`, so
    nothing is lost by removing the markers here.
    """
    out = _MD_HEADING.sub("", text)
    out = _MD_QUOTE.sub("", out)
    out = _MD_BULLET.sub("", out)
    out = _MD_STRONG.sub(r"\1", out)
    out = _MD_CODE.sub(r"\1", out)
    return _WS_RUN.sub(" ", out).strip()


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    text: str
    locator: str
    token_count: int


def split_on_sections(text: str) -> list[tuple[str, str]]:
    """Return list of (section_title, section_body). Fallback to whole doc if no headings.

    The heading line is excluded from the body and its markdown markers are stripped
    from the title. Previously the heading was part of both, which had two effects.
    The title kept its "##" prefix and reached the UI verbatim as the citation's
    locator, so citations read "## Sec 3(p) — Not patentable (TK bar)". And a
    heading with no body under it — the document's own H1 section, in every file —
    produced a chunk whose entire content was a bare document title: a retrievable,
    citable span that supports no claim at all.
    """
    matches = list(_SECTION_RE.finditer(text))
    if not matches:
        return [("Document", text)]
    sections: list[tuple[str, str]] = []
    for i, m in enumerate(matches):
        title = _MD_HEADING.sub("", m.group(1)).strip()[:120]
        start = m.end()
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

    def _emit(cur: str, section_title: str, token_count: int) -> None:
        """Store one chunk, unless it holds no law at all.

        A heading with no body under it — which is what the document's own H1
        section is — produced a chunk whose entire content was a title. Those
        chunks were retrievable and citable, so a citation slot could be spent on
        a bare document title that supports no claim. They are dropped here.
        """
        nonlocal global_idx
        body = plain_text(cur)
        if not body:
            return
        chunks.append(
            Chunk(
                chunk_id=f"{doc_id}#{global_idx:04d}",
                text=body,
                locator=section_title,
                token_count=token_count,
            )
        )
        global_idx += 1

    for section_title, section_text in sections:
        # Strip markdown BEFORE the sentence split, not after.
        #
        # The window loop below splits the section on sentence boundaries and
        # rejoins the pieces with a single space. That flattens every newline, and
        # `plain_text`'s marker regexes are all line-anchored (`^\s{0,3}>`), so once
        # the newlines were gone the ">" and "-" markers could no longer match and
        # were carried straight into the index — which is why quotes in the answer
        # began "> - Sec 9 (absolute grounds...)". Normalising first makes the
        # regexes see the line starts they need.
        section_text = plain_text(section_text)
        if not section_text:
            continue
        # sliding window over section
        # split roughly by tokens, but respect sentence boundaries where possible
        sentences = re.split(r"(?<=[.!?])\s+", section_text)
        cur = ""
        cur_tokens = 0
        for sent in sentences:
            st = count_tokens(sent)
            if cur_tokens + st > chunk_size and cur:
                _emit(cur, section_title, cur_tokens)
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
            _emit(cur, section_title, count_tokens(cur))
    return chunks
