# IP-SAKTI Sahayak (SIH26045)

A free assistant that answers Ayurveda IP and legal questions, with a real law quoted for every answer.

> PS: SIH26045, Ministry of Ayush (AIIA), MedTech/HealthTech, Theme 18, Python + AI/ML track.

Ask something like "Can I patent my grandmother's churna recipe?" and it tells you the actual law (India or International, never mixed up), quotes the exact line, links to the government source, and says how sure it is. If it is not sure, it tells you to talk to a human instead of guessing.

---

## What we have (working today)

- **India vs International, kept separate.** A hard toggle plus a "firewall" check that stops the two from ever getting mixed into one answer.
- **Every answer is quoted, not invented.** The default mode stitches together real quoted lines from the law library. It does not use an LLM to freely generate text, so it cannot hallucinate a fake section number.
- **Confidence score with a stop button.** Every answer gets a 0 to 100 score. Below the threshold, it refuses to guess and tells you to escalate to a human IP facilitator instead.
- **3-question triage.** Three taps (is it in an old text? did you change anything? what will you sell it as?) sort your formulation into a category and show what that means for patents, biodiversity permission, and food/drug rules.
- **Simple-language mode (ELI5).** A plain-words version of the answer for someone who is not a lawyer, plus hover definitions on legal terms like `Sec 3(p)` or `TKDL`.
- **Voice input.** Tap the mic and speak in Hindi, Tamil, or English using the browser's own speech recognition.
- **Export and print.** Turn any answer into a Markdown report or print it, citations included.
- **Runs for free.** No API key needed. It uses a small local AI model (MiniLM, runs on your own CPU) to search the law library, and a free local database (pgvector). You can optionally plug in a paid model later without changing any code.
- **23 real law documents** are loaded, covering every regime the problem statement names: Patents Act and 2024 Rules, Trade Marks, Designs, GI, Copyright, Plant Varieties, trade secrets, the Biological Diversity Act, FSSAI food rules, the drug and advertising Acts, and on the international side GRATK, PCT, TRIPS, CBD/Nagoya, Madrid/Hague/Budapest, plus export-market access (EU THMPD, US DSHEA) and the landmark case law (Divya Pharmacy, turmeric, neem). All in `corpus/sources/`.
- **Works with no database at all.** If Postgres is not running, the assistant reads and searches `corpus/` directly in memory, so a fresh clone answers correctly with zero setup. The same corpus backs both paths, so nothing is reachable in one and invisible in the other.
- **A version stamp on every answer.** Each answer shows a short hash of exactly which version of the law library produced it, so you can always tell if the source data has changed.

## How it works (plain-language walkthrough)

```
You type or speak a question
        ↓
The system reads your question and guesses what kind of IP question it is
        ↓
It searches the law library from 4 angles at once:
  statutes, TKDL (traditional-knowledge registry), other registries, case law
        ↓
It re-ranks those results to find the best matching lines
        ↓
The firewall checks: does this mix India and International law? If yes, it warns you
        ↓
It builds an answer using ONLY the quoted lines it found (never makes anything up)
        ↓
It scores how confident it is. Too low? It tells you to talk to a human instead
        ↓
You see: the answer, a simple-language version, the exact quotes with links, and the confidence score
```

Everything above runs on your own machine for free. If you later add a paid AI key (OpenAI) or run a free local model (Ollama), the system will use that instead to write more natural-sounding answers, but it will still only use the same quoted law as its source material.

## What's left (known gaps, being honest)

- **Voice translation and text-to-speech are mocked.** The code to call the real government Bhashini service is written and works, but without a free Bhashini API key it shows placeholder text like `[Bhashini mock en->hi]` instead of a real translation. Get a key and set `BHASHINI_API_KEY` in `.env` to turn this on for real.
- **The knowledge-graph view is a stub.** There's a page planned that shows how a formulation connects to a law to a registry as a visual graph (Neo4j). Right now it only returns made-up example data and isn't linked to any button in the app yet.
- **The 23 documents are summaries, not full statutes.** Each file condenses the provisions that matter for Ayurveda, so the assistant cites the right section and links to the official source, but cannot quote deep sub-clauses. Only two landmark cases are included, not a full case-law database. Adding documents is a manual step (see "Adding more law documents" below).
- **Without a database, retrieval is keyword-based, not semantic.** The offline path matches on words, so a question phrased with terms that appear in no statute may score low and the assistant will abstain rather than guess. Running `make up` (Postgres + pgvector) enables true semantic search over the same corpus. Abstaining is the intended failure mode here, but it does mean the offline path refuses some questions it could answer with a database.
- **The "paid database" consent flow is a placeholder.** It correctly blocks access and asks for consent, but there is no actual paid legal database wired up behind it yet, there's nothing to unlock.
- **No real user accounts or login.** Every visit is a fresh, anonymous session. Fine for a demo, would need real auth for production use.
- **Docker services that aren't used yet.** `make up` also starts a Redis cache and a Neo4j graph database. Neither is actually read from by the running app yet, they're there for the features above once those get built.

None of these block the demo. The core promise, real quoted law with links and a working India/International split, works end to end today.

---

## Quick start (no accounts, no cost)

```bash
cp .env.example .env   # already set to the free defaults, nothing to edit for a demo
make up                # starts everything with Docker
```

Or without Docker:
```bash
pip install -e backend/
uvicorn app.main:app --reload --port 8000 &
cd frontend && npm install && npm run dev
```

Then open:
- http://localhost:3000 for the app
- http://localhost:8000/docs for the API
- http://localhost:7474 for the (currently unused) Neo4j graph browser

### Adding more law documents
```bash
make ingest-dry   # preview what would be loaded, no changes made
make ingest       # actually load and index the documents
make corpus-hash  # print the version hash shown on every answer
```

### Checking answer quality
```bash
make eval   # writes eval/report.json with faithfulness and citation-accuracy scores
```

### Turning on a real AI model (optional, still free options available)
```bash
# Option A: Ollama, runs a free model on your own machine
ollama pull llama3.1:8b
# in .env: LLM_PROVIDER=ollama  LLM_MODEL=llama3.1:8b

# Option B: Hugging Face free tier
# in .env: LLM_PROVIDER=hf  HF_API_KEY=hf_...  LLM_MODEL=google/gemma-2-9b-it

# Option C: OpenAI (paid, only if you want it)
# in .env: LLM_PROVIDER=openai  OPENAI_API_KEY=sk-...
```

---

## Trying it yourself

1. Pick 🇮🇳 India or 🌐 International at the top. The two never get mixed.
2. Tap an example question, or type your own in plain words, no legal terms needed.
3. Try the 3-question triage: three taps tell you your formulation's category and what it means.
4. Turn on "Simple" mode to get a plain-language version alongside the legal one.
5. Check the right-hand panel: every claim links back to the real government source, with a version hash.

## API

`POST /api/v1/chat` with `{query, jurisdiction, language, explain_simple, formulation, session_id}` returns `{answer, answer_simple, jurisdiction, citations[], confidence, corpus_version, firewall, free_tier}`.

Full request and response shapes are in `backend/app/models/schemas.py`.

---

License: MIT. The law documents in `corpus/` are public-domain government text, see `corpus/manifest.json` for sources.
