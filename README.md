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
- **The interface itself is multilingual.** Hindi renders in Devanagari, Tamil in Tamil script, English in English, and the whole interface switches, not just the answer. Legal terms stay in Latin script (`Sec 3(p)`, `TKDL`) so you can match them against the official record.
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
It searches the law library from 5 angles at once: statutes, TKDL
  (traditional-knowledge registry), other registries, case law, and
  rules/treaties
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

## Project status and handoff notes

Last updated 2026-09-01. This section is the running record of where the project stands, so anyone picking it up knows what is finished, what was deliberately left, and what to do next.

### Verified working (checked end to end, not assumed)

| Area | Status | How it was checked |
|---|---|---|
| Corpus coverage | 23 documents, every regime the PS names | `make ingest-dry` reports 23 docs, 38 chunks |
| Retrieval correctness | Right document cited first on 10 of 11 regime questions | Direct API calls, see "Known retrieval limitation" below |
| Four homepage demo buttons | All four return the correct Act, confidence 71 to 95, firewall clean | Clicked through the running UI |
| Jurisdiction firewall | India and International never mix, no self-inflicted leaks | Both toggles return `firewall: clean` |
| Safe abstention | Out-of-scope questions ("write me a poem") refuse, confidence 45 | Direct API calls |
| Backend tests | 76 passing, 0 failing | `cd backend && pytest -q` |
| Frontend build | Clean production build, no TypeScript errors | `cd frontend && npm run build` |
| Icon system | 0 emoji left in the UI, all icons drawn from one shared module | Scripted scan of `app/` and `components/` |
| Answer formatting | Markdown renders properly, no raw `**` or `>` on screen | Read the rendered DOM in the browser |
| Real multilingual UI | Hindi renders in Devanagari, Tamil in Tamil script, the whole interface switches | Clicked each language and read the rendered page |
| First-run clarity | Numbered 3-step explainer, one primary action, triage no longer opens uninvited | Loaded the page cold at desktop and mobile |

### What changed in the most recent pass (2026-09-01)

A usability pass. The interface was cluttered and, more seriously, the language switch did not work.

1. **The multilingual claim did not survive a click.** Only three strings in the whole app responded to the language switch, and they swapped between romanised Hinglish ("Aapka sawaal") and English. Nothing was ever rendered in Devanagari, and picking தமிழ் changed *nothing at all*: a Tamil speaker saw romanised Hindi. The only Devanagari and Tamil characters in the codebase were the three pill labels themselves. Every UI string now lives in `frontend/lib/i18n.ts` in all three languages and scripts, and the whole interface switches, including the voice button, the 3-question triage, the proof panel, buttons and error messages. Legal terms (`Sec 3(p)`, `TKDL`, `Patents Act`) deliberately stay in Latin script so a user can match them against the official record, which is what the problem statement asks for.
2. **The page asked for too much at once.** Arrival showed a hero, four example cards, the voice and text input, the full 3-question triage already expanded, a "how we differ" list, a 3-step explainer and a 6-row comparison table, all competing. The triage now stays closed until someone asks for it, examples are compact chips inside the ask card rather than four cards competing with it, and the marketing comparison was removed from the main flow entirely.
3. **Nothing told a first-time visitor what to do.** There is now a numbered three-step line (ask, we search the law, read the answer and its proof) above a single obvious primary action.
4. **Citation spans leaked their own markup.** Quoted spans come from the corpus markdown, so they showed `##` headings and `>` markers inside an already-styled quote block. Stripped for display.
5. **Mobile truncated the product name** to "IP-SAK…" because the language switcher crowded the header. The switcher now wraps to its own row on narrow screens.

`HowItWorks.tsx` and `FreeBadge.tsx` were deleted rather than left unreferenced after the declutter. Their content is in git history if the comparison table is wanted for a slide.

### What changed in the pass before that (2026-08-31)

The work was a design and correctness pass to make the app presentable to judges. Five things were fixed, all of them real defects rather than cosmetics:

1. **Emoji were doing the job of an icon system.** 52 emoji across 9 files. Emoji render differently on every platform (the scroll glyph is a beige blob on one machine and a line drawing on another) and flag emoji degrade to plain letter pairs on some Windows builds, so a row of them had no shared stroke, weight or optical size. They are now drawn icons from one shared module, `frontend/components/Icon.tsx`, named by meaning (`classical`, `firewall`, `plant`) so a concept is restyled in one place. This used `lucide-react`, which was already a dependency but completely unused, so it added nothing to the bundle's dependency list.
2. **The answer was showing its own markup.** The generator emits markdown but the UI printed it with `whitespace-pre-wrap`, so readers saw literal `**Q:**` and a leading `>` instead of a bold label and a quoted statute span. On the single most-read element of the product that reads as broken. `frontend/components/AnswerText.tsx` now renders the small, fixed subset the generator actually produces. A full markdown library was deliberately not added: this is the only producer of that text, so a targeted renderer avoids both a dependency and an HTML-sanitising problem.
3. **Offline search weighted every word equally.** "india" appears in nearly every Indian legal document and carried the same weight as "patentable", so four documents tied on "is classical churna patentable in India" and an arbitrary one won. Retrieval is now IDF-weighted, so rare, discriminating words decide the ranking.
4. **The reranker returned chunks out of order relative to their scores.** It reordered the list but left each chunk's original score untouched, so the list was no longer sorted by score and `compute_confidence`, which reads `chunks[0]`, was scoring whichever chunk the reranker happened to promote. It now blends the retriever and CrossEncoder scores and writes the result back, so order and score agree.
5. **CORS origins were hardcoded.** Only `localhost:3000` and `*.vercel.app` were allowed, so serving the UI from any other host or port required editing source. Set `CORS_EXTRA_ORIGINS` in `.env` instead (comma-separated).

### Known retrieval limitation, left deliberately

The "Naya extract banaaya" demo button cites the **Plant Varieties Act** first rather than the Patents Act. This is defensible rather than broken: the query says "high-withanolide ashwagandha", which is literally the PPV&FR document's own worked example, and a novel high-yield cultivar genuinely is a plant-variety question. The Patents Act still appears at citations 2, 3 and 5, so the user sees it.

This was left alone on purpose. Tuning the ranking further would have meant overfitting to one phrasing, and three other phrasings of the same question already return the Patents Act correctly. If you want to improve it properly, the honest fix is to lengthen `corpus/sources/ppvfr_act_2001.md` (it is six lines, so its one Ayurveda sentence dominates the whole document) rather than to adjust ranking weights.

### Suggested next steps, roughly in order of value

1. **Get a free Bhashini API key** and set `BHASHINI_API_KEY` in `.env`. This is the largest visible gap: voice and translation are fully coded but currently show `[Bhashini mock en->hi]` placeholders. For an "AI for Bharat" pitch this is the single highest-impact hour of work available.
2. **Run `make up` before demoing** if you have Docker. It starts Postgres with pgvector and switches retrieval from keyword matching to true semantic search over the same corpus, which meaningfully improves answers on loosely-phrased questions.
3. **Expand the thin corpus documents.** `ppvfr_act_2001.md`, `gi_act_1999.md` and similar are only a few lines each. Longer documents both retrieve more accurately and quote more usefully.
4. **Wire up or delete the Neo4j graph.** `backend/app/rag/graph.py` returns mock data and nothing calls it. Either build the `Formulation to Category to Act to Registry` view the PS describes as a later stage, or remove it and the Neo4j container so `make up` stops starting a database nothing reads.
5. **Add more case law.** Only two landmark matters are covered (Divya Pharmacy, and the turmeric and neem revocations). The `case_law` retriever is wired and working, so new documents drop straight in.

### Local development gotchas worth knowing

- **Do not run `npm run build` while `next dev` is running.** Both write to `.next` and the dev server will start serving unstyled pages. If that happens, stop the server, `rm -rf frontend/.next`, and restart.
- **The backend does not auto-reload** unless you pass `--reload`. After editing anything under `backend/app`, restart uvicorn or your change will not be live.
- **Port 8000 may be occupied** by another project on your machine. If the header badge reads "backend offline" or shows a corpus version you do not recognise, the frontend is talking to the wrong server. Set `NEXT_PUBLIC_API_URL` in `frontend/.env.local` and add the matching origin to `CORS_EXTRA_ORIGINS`.
- **First question is slow.** The MiniLM embedding model loads on the first request, which takes several seconds. Send one warm-up query before demoing.

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
