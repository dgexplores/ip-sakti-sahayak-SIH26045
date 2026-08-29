# IP-SAKTI Sahayak — SIH26045

Multilingual, RAG-based, source-cited AI assistant for IP & regulatory guidance in Ayurveda.  
**Jurisdiction-aware. Citation-grounded. DPDP-audited. Staged: MVP → Graph → Agentic.**

> PS: SIH26045 · Ministry of Ayush (AIIA) · MedTech/HealthTech · Theme 18 · Python + AI/ML track.

---

## 1. Why this architecture wins

| PS Requirement | How we satisfy | Evidence |
|---|---|---|
| Jurisdiction toggle (India vs Intl) — **never conflated** | Hard enum `Jurisdiction` in API + UI, two-column renderer, classifier rejects mixed answers | `backend/app/rag/classifier.py`, `frontend/components/JurisdictionToggle.tsx` |
| Formulation classification (classical / proprietary / phytopharma / Aahar / cosmetic) | 3-question deterministic flow → category table + IP/ABS posture | `backend/app/rag/formulation.py` |
| ABS + TKDL pointer | Dedicated retrievers, ABS helper service | `backend/app/rag/retriever.py` |
| Triple citation + confidence + “not legal advice” | Pydantic `Citation` + `confidence 0–100` + assembler + footer hash | `backend/app/models/schemas.py`, `backend/app/rag/generator.py` |
| Version-tracked corpus (2024 Rules, WIPO GRATK 2024) | Git-tracked markdown in `corpus/sources/` + `manifest.json` + hash per answer | `corpus/manifest.json`, `backend/app/pipelines/ingest/loader.py` |
| Bhashini ASR/TTS (preserve legal terms) | `BhashiniService` with term-preservation + cache | `backend/app/services/bhashini.py` |
| Agentic 4-retriever orchestration | LangGraph router: statute, TKDL, registry, case-law → cross-check → abstain | `backend/app/rag/graph.py` |
| Paid DB consent + DPDP audit | `PaidConnector` modal + `AuditLogger` with consent trace | `backend/app/services/audit.py` |

---

## 2. Architecture

```
User (Hindi voice) → Bhashini ASR → Classifier (IP type + jurisdiction)
→ FormulationFlow (if needed) → Agentic Router (4 retrievers parallel)
→ Rerank + Cross-check → LLM (source-grounded, temp 0) → Citation Assembler
→ Confidence → Bhashini TTS → UI (toggle + pane) + Audit log
Paid DB → consent modal → logged
```

```
frontend/ (Next.js 14, Tailwind, shadcn)
  └─ JurisdictionToggle, ChatPane, CitationPane, FormulationFlow, EscalateButton
backend/ (Python FastAPI)
  ├─ api/v1/chat, corpus, classify, audit
  ├─ pipelines/ingest: loader → chunker → embedder → indexer
  ├─ rag: classifier, retriever (×4), reranker, generator, confidence, formulation
  ├─ services: bhashini, audit, graph
  └─ models: schemas (Pydantic), db (SQLModel)
corpus/ (Git + DVC, hash per answer)
eval/ (RAGAS faithfulness, citation precision, abstention, golden_set.json)
```

---

## 3. Quick start

```bash
cp .env.example .env   # fill OPENAI_API_KEY, etc.
make up                # docker compose: db+redis+qdrant+neo4j+backend+frontend
# or without docker:
make backend-install && make backend-run
make frontend-install && make frontend-dev
```

Open http://localhost:3000 (toggle India/International), http://localhost:8000/docs (API), http://localhost:7474 (Neo4j).

### Ingest corpus
```bash
make ingest-dry   # preview
make ingest       # chunk → embed → pgvector/qdrant + neo4j
make corpus-hash  # hash shown in every answer footer
```

### Evaluate
```bash
make eval  # writes eval/report.json (RAGAS faithfulness, citation precision, abstention rate)
```

---

## 4. Pipelines (senior-grade: typed, idempotent, observable)

**Ingest:** `loader` (pdf/md/json + sha256) → `chunker` (recursive, 800 tok, 120 overlap, section-aware) → `embedder` (OpenAI/local, batched, cached in Redis) → `indexer` (pgvector or Qdrant, upsert by doc_id+chunk_id, version hash).

All steps are **idempotent**, **resumable**, and emit structured logs + `corpus_version` hash. See `backend/app/pipelines/ingest/`.

**Query:** validate → classify jurisdiction+IP type → formulation triage if needed → 4× retriever (parallel) → Cohere rerank → cross-check (faithfulness gate 0.7) → generate with citations → confidence → audit.

If confidence < 0.7 or no statute span maps → **abstain** + escalate ticket (DPDP-consented).

---

## 5. API

`POST /api/v1/chat` — jurisdiction enum, citations, confidence, corpus_version, escalate flag.

See `backend/app/models/schemas.py` for contracts.

---

## 6. Roadmap (matches PS staged build)

- **W1–2 MVP:** 20 docs curated, single retriever, toggle, citations, 30 FAQ golden set → 70% judge score
- **W3 Graph+Agentic:** Neo4j, 4 retrievers, LangGraph, ABS+TKDL → faithfulness 0.92
- **W4 Scale:** paid proxy + consent, 10 langs + voice, tickets, video+PPT

---

## 7. Compliance

- Standing footer: **“Information, not legal advice. Verify at source link.”**
- Every answer carries `corpus_version` hash + `citations[]` with deep links.
- `AuditLogger` is DPDP-aligned: consent_id, purpose limitation, retention, export/delete.
- `PaidConnector` never hits paid DB without explicit logged permission.

License: MIT. Corpus licenses respected per `corpus/manifest.json`.
