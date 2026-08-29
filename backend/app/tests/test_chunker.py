from app.pipelines.ingest.chunker import chunk_text

def test_chunker_basic():
    text = "# Sec 3(p)\n" + ("An invention which is traditional knowledge is not patentable. " * 40)
    chunks = chunk_text(text, "doc1", chunk_size=100, overlap=10)
    assert len(chunks) >= 2
    assert all(c.token_count > 0 for c in chunks)
    assert chunks[0].locator == "# Sec 3(p)"

def test_chunker_no_heading():
    chunks = chunk_text("hello world " * 200, "doc2")
    assert len(chunks) >= 1
