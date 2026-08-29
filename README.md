# IP-SAKTI Sahayak — SIH26045

Multilingual, RAG-based, source-cited AI assistant for IP & regulatory guidance in Ayurveda.  
**Jurisdiction-firewalled. Citation-grounded. 100% FREE to demo. Easy for anyone to understand.**

> PS: SIH26045 · Ministry of Ayush (AIIA) · MedTech/HealthTech · Theme 18 · Python + AI/ML track.

**Win strategy: Theme 18 (moderate) + Org Ayush 5 (rarest — only 5 PS in 229) = compete vs 3–5 teams, not 50. Free-stack + ELI5 + firewall is the moat generic teams can’t fake.**

---

## Why this wins (judge’s checklist)

| PS Must-Have | How we do it — uniquely & free | Proof |
|---|---|---|
| **Jurisdiction toggle — never conflated** | Hard `Jurisdiction` enum + **firewall** (`jurisdiction_firewall.py`) filters leaks, shows verdict banner, two colors (saffron `#FF9933` vs ink `#0B2239`) never mixed | `backend/app/rag/jurisdiction_firewall.py:1`, `frontend/components/JurisdictionToggle.tsx:1` |
| **Formulation classification** | **3Q flow** → `classical/proprietary/phytopharma/new_drug/aahar/cosmetic` → posture table (IP/ABS/Regulatory) + next steps, one tap | `backend/app/rag/formulation.py:1`, `frontend/components/FormulationFlow.tsx:1` |
| **ABS + TKDL pointer** | Dedicated retrievers, ABS helper, TKDL guideline chunk | `backend/app/rag/retriever.py:1` |
| **Triple citation + confidence + “not legal advice”** | Every answer = verbatim span + `locator` + `deep_link` + `version_hash` + confidence 0–100 + abstain gate 0.70 + footer disclaimer. Offline-extractive = **zero hallucination** | `backend/app/models/schemas.py:20`, `backend/app/rag/generator.py:1` |
| **Version-tracked corpus (2024 Rules, GRATK 2024)** | Git-tracked `corpus/sources/*.md` + `manifest.json` + hash in every answer | `corpus/manifest.json:1`, `GET /api/v1/corpus/version` |
| **Bhashini + ELI5** | Bhashini ASR/TTS (free govt infra) + **ELI5 toggle** (simple words for any villager) + glossary hover where legal terms stay English | `backend/app/services/bhashini.py:1`, `frontend/components/GlossaryTooltip.tsx:1` |
| **Agentic 4-retriever** | `retrieve_all` fan-out (statute, TKDL, registry, case_law) → **free CrossEncoder** rerank → firewall → offline-extractive | `backend/app/rag/reranker.py:1` |
| **Paid DB consent + DPDP audit** | `PaidConnector` blocks paid DB without `consent_id`; `AuditLogger` pseudonymized, 365-day retention, ticket with full trace | `backend/app/services/audit.py:1` |
| **100% FREE to demo** | Default = **local MiniLM (80MB, MIT, CPU)** + **offline-extractive (₹0)** + **pgvector (FOSS)** + lexical rerank. No OpenAI/Cohere key needed. Add `OPENAI_API_KEY` or run Ollama to upgrade — zero code change. | `backend/app/core/config.py:1` (`llm_provider=offline`, `embedding_provider=local`) |

**Unique only we have:** firewall banner, ELI5 panel, one-click Export .md, glossary hover, free-tier badge (`FREE — ₹0`), offline-ready banner, comparison table.

---

## Free-stack architecture (₹0 default)

```
User (Hindi voice, free Bhashini) → ASR → Classifier → 3Q Triage (if needed)
→ 4× Retriever (parallel, jurisdiction-filtered) → CrossEncoder rerank (free, local)
→ Jurisdiction Firewall → Offline-extractive stitching (free, zero hallucination)
→ Citation assembler + confidence → Bhashini TTS (free) → UI (toggle + pane + ELI5 + export) + Audit
```

**Ingest:** `loader` (pdf/md/json, sha256) → `chunker` (800/120, section-aware) → `LocalEmbedder` (MiniLM, batched) → `pgvector` upsert by `doc_id#chunk_id` (idempotent).

All **offline**, **free**, **observable** (`make ingest-dry`, `make eval`).

---

## Quick start — zero keys, zero billing

```bash
cp .env.example .env   # already FREE defaults, no edits needed for demo
make up                # docker: db+redis+qdrant+neo4j+backend+frontend

# or without docker:
pip install -e backend/
uvicorn app.main:app --reload --port 8000 &
cd frontend && npm install && npm run dev
```

Open http://localhost:3000 (check `FREE — ₹0` badge), http://localhost:8000/docs, http://localhost:7474 (Neo4j).

### Ingest corpus
```bash
make ingest-dry   # preview 17 docs → 27 chunks
make ingest       # embed (local MiniLM) → pgvector
make corpus-hash  # hash shown in every answer footer
```

### Evaluate (RAGAS heuristic, free)
```bash
make eval  # writes eval/report.json — faithfulness, citation precision, abstention
```

### Upgrade to free LLM (optional, still free)
```bash
# Option A: Ollama local (free, offline)
ollama pull llama3.1:8b
# .env: LLM_PROVIDER=ollama  LLM_MODEL=llama3.1:8b

# Option B: HuggingFace free tier
# .env: LLM_PROVIDER=hf  HF_API_KEY=hf_...  LLM_MODEL=google/gemma-2-9b-it

# Option C: OpenAI (only if you want to pay)
# .env: LLM_PROVIDER=openai  OPENAI_API_KEY=sk-... 
```

---

## Easy to use — for anyone

1. **Toggle** 🇮🇳 INDIA vs 🌐 INTERNATIONAL — colors never mix, firewall warns if leaked.
2. **Tap an example** or type plain words (“Can I sell chawanprash as food?”) — no legal jargon needed.
3. **3Q Triage** — 3 taps classify classical/proprietary/phytopharma → table tells IP/ABS/Regulatory.
4. **Read answer** — highlights + ELI5 (toggle on) + glossary hover (e.g., `Sec 3(p)` → plain English).
5. **Check proof** — right pane: statute span + “↗ Verify” link + hash. Export .md for PPT.

**Judge demo (2 min):** Classical? (🇮🇳 Sec 3(p) + TKDL) → toggle 🌐 (GRATK Art 3) → ELI5 on → 3Q posture → Export → escalate ticket → point to `corpus hash` + `FREE` badge.

---

## API

`POST /api/v1/chat` — `{query, jurisdiction, language, explain_simple, formulation, session_id}` → `{answer, answer_simple, jurisdiction, citations[], confidence, corpus_version, firewall, free_tier}`

See `backend/app/models/schemas.py:44` for contracts.

---

## Roadmap (PS staged)

- **W1–2 MVP (today):** 17 docs, offline RAG, firewall, ELI5, export — runs free, wins 70% judge score.
- **W3 Graph+Agentic:** Neo4j `Formulation→Category→Act→Registry` + LangGraph.
- **W4 Voice+Scale:** full Bhashini 10 langs + voice mode + facilitator tickets.

License: MIT. Corpus public-domain per `corpus/manifest.json`.
