import pytest
from app.pipelines.ingest.embedder import LocalEmbedder, _fake_embed, get_embedder

def test_fake_embed_deterministic():
    a = _fake_embed("hello world", 16)
    b = _fake_embed("hello world", 16)
    c = _fake_embed("different", 16)
    assert a == b
    assert a != c
    assert len(a) == 16
    # normalized
    assert abs(sum(x*x for x in a) - 1) < 1e-6

@pytest.mark.asyncio
async def test_local_embedder_fake_fallback():
    # without sentence_transformers model, should fallback to hash
    emb = LocalEmbedder(model_name="nonexistent-model-xyz")
    out = await emb.embed(["hello", "world"])
    assert len(out) == 2
    assert len(out[0]) == emb.dim

@pytest.mark.asyncio
async def test_get_embedder_free_default():
    emb = get_embedder()
    # default is local, dim 384
    assert emb.dim in (384, 1536, 768, 1024)
    vecs = await emb.embed(["Sec 3(p) traditional knowledge"])
    assert len(vecs) == 1
    assert len(vecs[0]) == emb.dim
