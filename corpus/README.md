# Corpus — version-tracked, jurisdiction-tagged

Every file in `sources/` is Git-tracked markdown with:
- `jurisdiction: india | international` (never conflated at query time)
- `effective_date` (ISO)
- `deep_link` to official source
- `version_hash` per ingest (git short hash + sha256)

Ingest: `make ingest` → chunk (800 tok, 120 overlap, section-aware) → embed → pgvector/qdrant upsert (idempotent by doc_id#chunk_id).

Freshness proof: `GET /api/v1/corpus/version` returns `corpus_version` hash; every chat response carries `corpus_version` in footer.

To add a document:
1. Drop markdown/pdf under `sources/`
2. Add entry to `manifest.json` with jurisdiction + effective_date + deep_link
3. `make ingest` (or `make ingest-dry` to preview)

Licenses respected per manifest. PDFs of statutes are public domain; summaries are public-domain-summary.
