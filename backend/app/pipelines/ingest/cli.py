"""CLI: python -m app.pipelines.ingest.cli --manifest corpus/manifest.json [--dry-run]"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import pathlib
import subprocess
import sys

from app.pipelines.ingest.chunker import chunk_text
from app.pipelines.ingest.embedder import get_embedder
from app.pipelines.ingest.indexer import build_records, upsert
from app.pipelines.ingest.loader import load_file, load_manifest


def git_short_hash(path: pathlib.Path) -> str | None:
    try:
        out = subprocess.check_output(["git", "rev-parse", "--short=12", "HEAD"], cwd=str(path), text=True)
        return out.strip()
    except Exception:
        return None


async def run(manifest_path: pathlib.Path, dry_run: bool = False, reindex: bool = False) -> None:
    manifest_path = manifest_path.resolve()
    corpus_root = manifest_path.parent
    docs_meta = load_manifest(manifest_path)
    git_hash = git_short_hash(corpus_root.parent) or git_short_hash(corpus_root) or "nogit"

    embedder = get_embedder()
    total_chunks = 0
    total_docs = 0
    corpus_version = hashlib.sha256("".join(sorted(d["doc_id"] for d in docs_meta)).encode()).hexdigest()[:12]

    print(f"[ingest] manifest={manifest_path} docs={len(docs_meta)} git={git_hash} corpus_version={corpus_version}")
    print(f"[ingest] embedder dim={embedder.dim} dry_run={dry_run}")

    for meta in docs_meta:
        # resolve file
        rel = meta.get("file") or meta.get("path") or ""
        fpath = (corpus_root / rel).resolve() if rel else None
        if fpath is None or not fpath.exists():
            print(f"  [skip] {meta.get('doc_id')}: file not found {fpath}", file=sys.stderr)
            continue
        raw = load_file(fpath, meta, git_hash=git_hash)
        chunks = chunk_text(raw.text, raw.doc_id)
        if not chunks:
            print(f"  [skip] {raw.doc_id}: no chunks", file=sys.stderr)
            continue
        texts = [c.text for c in chunks]
        embeddings = await embedder.embed(texts)
        records = build_records(raw, chunks, embeddings)

        if dry_run:
            print(f"  [dry] {raw.doc_id}: {len(chunks)} chunks | {raw.title} | {raw.locator if False else ''}")
            for c in chunks[:2]:
                print(f"        chunk {c.chunk_id} tokens={c.token_count} locator={c.locator[:60]}")
        else:
            n = upsert(records)
            print(f"  [upsert] {raw.doc_id}: {n} chunks → {records[0].jurisdiction}/{records[0].source_type}")

        total_chunks += len(chunks)
        total_docs += 1

    print(f"[ingest] done docs={total_docs} chunks={total_chunks} corpus_version={corpus_version}")
    if dry_run:
        print("[ingest] dry-run — no DB writes for pgvector; Qdrant writes skipped")


def main() -> None:
    ap = argparse.ArgumentParser(description="IP-SAKTI corpus ingest")
    ap.add_argument("--manifest", required=True, help="path to corpus/manifest.json")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--reindex", action="store_true", help="force re-embed even if hash unchanged")
    args = ap.parse_args()
    asyncio.run(run(pathlib.Path(args.manifest), dry_run=args.dry_run, reindex=args.reindex))


if __name__ == "__main__":
    main()
