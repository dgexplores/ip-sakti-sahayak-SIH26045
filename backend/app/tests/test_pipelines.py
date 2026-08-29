import pathlib, json, hashlib
from app.pipelines.ingest.loader import load_manifest, load_file
from app.pipelines.ingest.chunker import chunk_text

def test_manifest_valid():
    manifest = pathlib.Path(__file__).parents[3] / "corpus" / "manifest.json"
    assert manifest.exists()
    docs = load_manifest(manifest)
    assert len(docs) >= 15
    # all have required fields
    for d in docs:
        assert "doc_id" in d and "file" in d and "jurisdiction" in d and "deep_link" in d
        assert d["jurisdiction"] in ("india", "international")
    # unique doc_ids
    ids = [d["doc_id"] for d in docs]
    assert len(ids) == len(set(ids))

def test_manifest_files_exist():
    manifest = pathlib.Path(__file__).parents[3] / "corpus" / "manifest.json"
    corpus_root = manifest.parent
    docs = load_manifest(manifest)
    missing = []
    for d in docs:
        p = corpus_root / d["file"]
        if not p.exists():
            missing.append(d["file"])
    assert missing == [], f"missing files: {missing}"

def test_loader_and_chunker_all_docs():
    manifest = pathlib.Path(__file__).parents[3] / "corpus" / "manifest.json"
    corpus_root = manifest.parent
    docs = load_manifest(manifest)
    for meta in docs[:5]:  # sample 5 for speed
        p = corpus_root / meta["file"]
        raw = load_file(p, meta, git_hash="test123")
        assert raw.text.strip()
        assert len(raw.sha256) == 64
        chunks = chunk_text(raw.text, raw.doc_id)
        assert len(chunks) >= 1
        for c in chunks:
            assert c.text.strip()
            assert c.token_count > 0
            assert c.locator

def test_chunker_no_empty():
    chunks = chunk_text("", "empty")
    assert chunks == []

def test_chunker_section_aware():
    text = "# Sec 3(p)\n" + "Traditional knowledge bar. " * 50 + "\n## Sec 10\n" + "Complete spec. " * 50
    chunks = chunk_text(text, "doc", chunk_size=100, overlap=10)
    locs = [c.locator for c in chunks]
    assert any("Sec 3(p)" in l for l in locs)
    assert any("Sec 10" in l for l in locs)
