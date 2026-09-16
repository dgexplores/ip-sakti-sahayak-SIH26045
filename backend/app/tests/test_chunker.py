from app.pipelines.ingest.chunker import chunk_text, plain_text, split_on_sections


def test_chunker_basic():
    text = "# Sec 3(p)\n" + ("An invention which is traditional knowledge is not patentable. " * 40)
    chunks = chunk_text(text, "doc1", chunk_size=100, overlap=10)
    assert len(chunks) >= 2
    assert all(c.token_count > 0 for c in chunks)
    # The locator used to be the raw heading line, so the citation UI printed
    # "## Sec 3(p) — Not patentable (TK bar)" with the hashes intact.
    assert chunks[0].locator == "Sec 3(p)"


def test_chunker_no_heading():
    chunks = chunk_text("hello world " * 200, "doc2")
    assert len(chunks) >= 1


def test_heading_only_section_produces_no_chunk():
    """A heading with nothing under it is a bare title, not a citable span.

    Every corpus file opens with an H1 and a blank line, so each document used to
    contribute a retrievable chunk whose entire content was its own title. One of
    them was cited in place of the provision that decides the question.
    """
    chunks = chunk_text("# Patents Act, 1970\n\n## Sec 3(p)\nTK is not an invention.\n", "doc3")
    texts = [c.text for c in chunks]
    assert all(t.strip() != "Patents Act, 1970" for t in texts), texts
    assert any("TK is not an invention." in t for t in texts)


def test_markdown_markers_never_reach_a_chunk():
    """The window loop flattens newlines before normalising, so the marker
    regexes have to run first. Otherwise quotes reach the answer as
    "> - Sec 9 (absolute grounds...)" — a nested blockquote inside a bullet."""
    raw = (
        "# Act\n"
        "## Sec 9\n"
        "A mark that is purely descriptive cannot be registered.\n"
        "\n"
        '> Sec 9: "a mark that is purely descriptive." — the Act.\n'
        "- Sec 11: earlier marks block registration.\n"
    )
    for c in chunk_text(raw, "doc4"):
        assert "##" not in c.text
        assert not c.text.startswith(">")
        assert " > " not in c.text
        assert " - " not in c.text
        assert "**" not in c.text


def test_plain_text_keeps_every_word():
    """Stripping presentation must not change wording — the quote is evidence."""
    raw = '## Sec 3(p)\n\n> Sec 3(p): "an invention which, in effect, is traditional knowledge."\n'
    out = plain_text(raw)
    for word in ("Sec", "3(p)", "invention", "effect", "traditional", "knowledge"):
        assert word in out
    assert "#" not in out and ">" not in out


def test_section_split_excludes_the_heading_line():
    title, body = split_on_sections("# Act\nBody under the heading.\n")[0]
    assert title == "Act"
    assert "Body under the heading." in body
