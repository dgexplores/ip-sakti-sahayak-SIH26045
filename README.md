# IP-SAKTI Sahayak (SIH26045)

A free assistant that answers Ayurveda IP and legal questions, with a real law quoted for every answer.

> PS: SIH26045, Ministry of Ayush (AIIA), MedTech/HealthTech, Theme 18, Python + AI/ML track.

Ask something like "Can I patent my grandmother's churna recipe?" and it tells you the actual law (India or International, never mixed up), quotes the exact line, links to the government source, and says how sure it is. If it is not sure, it tells you to talk to a human instead of guessing.

## Repo map (new here? start here)

```
backend/app/        FastAPI service — api/ routes, rag/ retrieval+generation,
                    pipelines/ ingest, services/ LLM/Bhashini, models/ schemas
backend/app/tests/  pytest suite (148 passing) — run with `make test`
backend/app/eval/   ragas_eval.py — the pipeline eval behind `make eval`
frontend/app/       Next.js pages — page.tsx (ask flow), privacy/, terms/,
                    not-found.tsx, icon.svg, loading.tsx, error.tsx
frontend/components/ UI blocks — answer render, citations, triage, voice, badges
frontend/lib/       api.ts (backend client), i18n.ts (en/hi/ta strings)
corpus/             23 law summaries + manifest.json (public-domain govt text)
eval/golden_set.json  20 graded questions for `make eval`
eval/check_i18n.ts    three-language string parity gate
eval/check_frontend_syntax.ts  frontend parse gate
scripts/            check.sh / robust_check.sh / demo.sh — scripted health checks
Makefile            every command below — `make check` runs all the gates
```

Follow the request path: `frontend/lib/api.ts` → `POST /api/v1/chat` →
`backend/app/api/` → `backend/app/rag/` (retrieve → firewall → generate → score).

---

## What we have (working today)

- **India vs International, kept separate.** A hard toggle plus a "firewall" check that stops the two from ever getting mixed into one answer. On the flagship question it removes 11 of 27 candidates before answering and says so.
- **Every answer is quoted, not invented.** The default mode stitches together real quoted lines from the law library. It does not use an LLM to freely generate text, so it cannot hallucinate a fake section number. Every `>` block in an answer is a verbatim substring of a cited source span, and that is checked on all 20 eval cases.
- **Confidence score with a stop button.** Every answer gets a 0 to 100 score. Below the threshold, it refuses to guess and tells you to escalate to a human IP facilitator instead.
- **3-question triage.** Three taps (is it in an old text? did you change anything? what will you sell it as?) sort your formulation into a category and show what that means for patents, biodiversity permission, and food/drug rules.
- **Simple-language mode (ELI5).** A plain-words version of the answer for someone who is not a lawyer, plus hover definitions on legal terms like `Sec 3(p)` or `TKDL` — the definitions are translated too, not just the surrounding chrome.
- **The interface itself is multilingual.** Hindi renders in Devanagari, Tamil in Tamil script, English in English, and the whole interface switches: the ask flow, the voice button, the triage, the proof panel, the glossary, the error and 404 pages, and the footer. 69 UI strings, 22 triage strings and 11 glossary definitions in each of the three languages, checked for parity by `make check-i18n`. Legal terms stay in Latin script (`Sec 3(p)`, `TKDL`) so you can match them against the official record. Your language choice survives a reload.
- **Voice input.** Tap the mic and speak in Hindi, Tamil, or English using the browser's own speech recognition. If the browser has none, it says so in your language instead of throwing an alert about the server.
- **Export and print.** Turn any answer into a Markdown report or print it, citations and confidence included.
- **Runs for free.** No API key needed. It uses a small local AI model (MiniLM, runs on your own CPU) to search the law library when a database is present, and a free local database (pgvector). You can optionally plug in a paid model later without changing any code.
- **23 real law documents** are loaded, covering every regime the problem statement names: Patents Act and 2024 Rules, Trade Marks, Designs, GI, Copyright, Plant Varieties, trade secrets, the Biological Diversity Act, FSSAI food rules, the drug and advertising Acts, and on the international side GRATK, PCT, TRIPS, CBD/Nagoya, Madrid/Hague/Budapest, plus export-market access (EU THMPD, US DSHEA) and the landmark case law (Divya Pharmacy, turmeric, neem). All in `corpus/sources/`.
- **Works with no database at all.** If Postgres is not running, the assistant reads and searches `corpus/` directly in memory, so a fresh clone answers correctly with zero setup. The same corpus backs both paths, so nothing is reachable in one and invisible in the other. The offline path never constructs an embedding model — verified at 0 model loads per request.
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

- **Answer translation and text-to-speech need a Bhashini key.** The interface itself is fully translated (Hindi in Devanagari, Tamil in Tamil), but the *answer body* is only translated when a free Bhashini API key is set. Without one it stays in English rather than being faked. Set `BHASHINI_API_KEY` in `.env` to turn it on. The same applies to the triage result table (`posture_table`) and its next-steps list, which the backend generates in English.
- **The 23 documents are summaries, not full statutes.** Each file condenses the provisions that matter for Ayurveda, so the assistant cites the right section and links to the official source, but cannot quote deep sub-clauses. Only two landmark cases are included, not a full case-law database. Adding documents is a manual step (see "Adding more law documents" below).
- **Without a database, retrieval is keyword-based, not semantic.** The offline path matches on words, so a question phrased with terms that appear in no statute may score low and the assistant will abstain rather than guess. Running `make up` (Postgres + pgvector) enables true semantic search over the same corpus. Abstaining is the intended failure mode here, but it does mean the offline path refuses some questions it could answer with a database. **The vector path itself has not been run against a live pgvector** — no Docker or Postgres was available during the audit, so every measurement in the section above comes from the offline lexical path. It is covered by unit tests around the reranker and degrades to the offline index on connection failure, but "semantic search works" is, at the time of writing, a design claim rather than a measured one.
- **Within one statute, the leading span can still be the wrong provision.** Document-level top-citation accuracy is 20/20, but on the flagship question the first quote is Patents Act **Sec 3(d)** (mere discovery) while **Sec 3(p)** — the traditional-knowledge bar that actually decides the question — is quoted in full at position 2. The ranking is lexical, and the 3(p) text says "not an invention" rather than using the query's word "patentable", so it loses on term overlap. See "Known retrieval limitation" below.
- **The "paid database" consent flow is a placeholder.** It correctly blocks access and asks for consent, but there is no actual paid legal database wired up behind it yet, there's nothing to unlock.
- **No real user accounts or login.** Every visit is a fresh, anonymous session. Fine for a demo, would need real auth for production use.
- **One notice is shown twice.** The jurisdiction-firewall message appears both in the dedicated blue panel above the answer and as the first line of the answer body. The body copy is deliberate (the answer has to be self-contained for export and print), so the duplication is accepted rather than fixed.
- **The corpus index is built on the first request.** Roughly 1.4 s to read and chunk 23 documents, cached afterwards; subsequent requests run in about 150–250 ms. Warm the server with one query before demoing.

None of these block the demo. The core promise, real quoted law with links and a working India/International split, works end to end today.

---

## Project status and handoff notes

Last updated 2026-09-20. This section is the running record of where the project stands, so anyone picking it up knows what is finished, what was deliberately left, and what to do next.

### Production (2026-09-20, measured live)

Live: frontend `https://ip-sakti-sahayak-ashen.vercel.app`, backend `https://sakti-api.onrender.com` (free tiers, `render.yaml` + `frontend/vercel.json` in repo).

- **Backend runs databaseless.** No Postgres/Redis: retrieval is lexical over `corpus/`, audit falls back to log lines. `SKIP_ML_MODELS=1` is set because 512MB free containers OOM-restart when torch + MiniLM + CrossEncoder load (measured: 502 + restart mid-request). Embeddings are discarded by the offline path and rerank falls back to the write-back TF-IDF path, so answers are unaffected — only the unused vectors change. If this moves to paid hosting with RAM, unset the flag to restore CrossEncoder rerank and re-run the eval below.
- **20/20 golden cases pass against the live API** (`scripts/grade_live.sh`): abstention, jurisdiction, top-doc and quote-verbatim all green. In-scope scores 63.8–96.0, genuine out-of-scope 5.0, signal-path refusals 45.0. Gate stays 0.45 — no recalibration was needed on the merged code.
- **Citations carry full chunk text.** `to_citations` cut spans at 400 chars while the generator quoted from full chunk text (a real Sec 2(1)(j) line past the cut). Fixed: verifiable-by-construction now.
- **History note (read before rewriting history).** On 2026-09-20 a force-push orphaned the Sep-17 audit commit `1d83da6`; it was recovered to branch `audit-recovery` and merged back as `414e5f9` with the deployment stack layered on top. Never force-push `main` without `git branch <backup> <tip>` first.

### What changed in this pass (2026-09-15)

An audit pass. The theme was that the project's claims were stronger than its behaviour, in several places where nothing was measuring the difference. Everything below was measured, not assumed, and every fix has a test or an eval metric holding it in place.

**Correctness**

1. **The confidence gate made every homepage button refuse to answer.** `retriever.py` mapped raw relevance into a hardcoded `0.62 + (raw / ceiling) * 0.33` band, so an unrelated chunk still scored 62 points; the gate was 70. The result: **all four** demo questions abstained, at 22.7 / 17.0 / 67.0 / 15.0, and the one the README leads with — "Can I patent my grandmother's churna recipe?" — was among them. The floor is gone, the curve is a single sub-1 exponent (`_RELEVANCE_EXPONENT = 0.65`) shared by both retrieval backends, and the gate now sits inside a measured 27-point gap: in-scope questions land at 60.1–96.0, relevance-scored out-of-scope questions at 5.0–32.9.

   Measured before and after, same four queries:

   | Homepage button | Before | After |
   |---|---|---|
   | classical Ashwagandha churna | 22.7, **abstained** | 58.0, answers, Patents Act |
   | novel extract | 17.0, **abstained** | 65.7, answers, Patents Act |
   | selling abroad | 67.0, **abstained** | 96.0, answers, WIPO GRATK |
   | plant permission | 15.0, **abstained**, cited *Trade secrets* | 59.5, answers, BDA 2023 |

   The "before" column was measured by checking out the previous commit into a scratch worktree and posting the same four queries, not read off the source.
2. **"Word-for-word" quotes were not word-for-word.** Sentences were scored independently and concatenated, so a "quote" could open with a source URL and a fabricated version hash. Quoting is now a single contiguous substring, metadata lines are excluded as anchors and trimmed from the edges only, and every `>` line in every eval answer is verified to be a verbatim substring of a cited span.
3. **The jurisdiction firewall had no work to do and could not report on it.** `foreign_ratio` was structurally always 0.0, both leak branches were unreachable, and `has_mismatch` was always False. Retrieval no longer pre-filters by jurisdiction, so the firewall sees both regimes and removes the foreign ones: 11 of 27 candidates on the flagship question. `leak_warning` now fires only when the *best* candidate is the other regime, and a toggle mismatch is reported.
4. **The classifier rejected its own vocabulary.** A trailing `\b` meant "patentable", "patents" and "trademarks" did not match, and dict iteration order made tie-breaking accidental. Patterns are suffix-tolerant, the keyword table is an ordered list, and PCT/GRATK/genetic-resource queries now classify as patent instead of unknown.
5. **The verdict was a keyword switch, not a reading of the question.** "Can I copyright my Ayurveda textbook?" returned the trademark verdict. The verdict now routes on the classified IP type, which the call sites were computing and then not passing down.
6. **Reranking did not rescore.** The list was reordered while each chunk kept its old score, so order and score disagreed and `compute_confidence`, which reads `chunks[0]`, was scoring whichever chunk happened to get promoted. The reranker now writes blended scores back.
7. **All four homepage buttons reported `firewall: clean`** — because retrieval pre-filtered by jurisdiction, the firewall never saw a foreign candidate and could not have reported contamination even if there had been any. It also meant the "before" column above was uniformly green while every answer was a refusal. The firewall now has real work (see item 3) and its verdict distinguishes `filtered` from `clean` from `mixed_query`.

**Claims that were not true**

8. **`make eval` never invoked the pipeline.** It returned `ragas_used: false` and graded nothing. It now posts all 20 golden cases to the real `/api/v1/chat` and grades abstention, jurisdiction, IP type, top citation, quote integrity and firewall integrity, plus a calibration block — and exits non-zero on failure, so it is a gate rather than a report.
9. **Three test assertions could not fail** (`assert x or True`-shaped). They were replaced with assertions on the artefact the reader actually sees.
10. **The privacy notice described a file that did not do what it said.** `audit.py` stores the query verbatim (capped at 500 characters) — it is not pseudonymised. The docstring and the privacy page now say so, and the audit read route no longer returns the query text.
11. **The response header advertised a hardcoded corpus version** (`sakti-corpus-v1`) that matched a fallback in `corpus.py` only because both were wrong. In the container the manifest resolved to `/corpus`, loaded empty, and the placeholder hash agreed with the header, so `make up` silently ran without a corpus. Resolution now walks ancestors and honours `CORPUS_DIR`.
12. **The README's own numbers were stale**: a test count two passes old, a confidence band that no longer existed, and "firewall clean" on every demo button when the firewall's real verdict is `filtered`. All replaced with measured values, and CI now fails if the eval regresses.

**Presentation**

13. **System notices were dressed as quoted law.** "Jurisdiction firewall:", "Check the toggle:" and "Paid database:" were emitted as blockquotes, rendering in the same grey box as the statutory spans — in a product whose entire claim is that you can tell the two apart. They are bold paragraphs now, and the eval's quote check was tightened to match: no banner exemption, every remaining blockquote must be verbatim law.
14. **Citation headings were three-em-dash run-ons.** Manifest titles are deliberately descriptive, so title-then-locator produced `Patents Act, 1970 (as amended) — Sec 3, 4, 10, 25 — with 2024 Rules diff — Sec 3(d) — mere discovery`. The provision now heads the line, with the document title beneath it. Related, and visible in the "before" column above: the locator itself carried its markdown markers, so citations read `## Sec 3(p) — Not patentable (TK bar)`. The chunker now strips presentation markers from the heading before it becomes a locator, and drops headings that have no body under them (which is every document's own H1).
15. **The confidence rationale was printed twice** — once in the answer body, once under the confidence bar. It is a structured field now, and the Markdown export re-adds it for the report.
16. **Romanised Hinglish survived in the corners the language switch could not reach.** `SplitView.tsx` ("Dono kanoon alag dekho"), `error.tsx` ("Kuch gadbad ho gayi") and `not-found.tsx` were hardcoded, and the glossary definitions were English-only, so every tooltip stayed English in all three languages. All of it is in `lib/i18n.ts` now, the error and 404 pages read the stored language, and the choice persists across reloads.

**Cleanup**

17. **`app/rag/graph.py` was deleted**, along with the Neo4j service, its volume and its dependency. Nothing imported it, and its "real Neo4j" branch connected, verified, closed and then returned mock data regardless — so even with a live database it could not have told the truth. Redis is behind the `cache` compose profile for the same reason: the default `make up` now starts only what the app queries.
18. **`make up` failed on a fresh clone.** `.env` is gitignored and only `.env.example` is committed, so `docker compose up` stopped at "env file .env not found" on the documented primary path. The Makefile creates it on first use.
19. **The frontend image ignored its own lockfile** (`COPY package.json` + `npm install`), so a container could ship a different dependency tree than the repo pinned. It is `npm ci` with the lockfile now, with `.dockerignore` files so a host `node_modules` cannot overwrite the image's.
20. **`scripts/check.sh` could not fail.** It piped the eval and the frontend build into `tail`, which replaced their exit status with tail's, and it called three test files "the suite". It delegates to `make check` now, and `robust_check.sh` lost its hardcoded "(68)" test count.
21. **`npm run lint` had never been runnable.** `eslint` and `eslint-config-next` were declared as devDependencies, but no `.eslintrc.json` was ever committed — `git log` confirms it never existed. `next lint` therefore stopped at an interactive "How would you like to configure ESLint?" prompt, so the command hung rather than failing. A hang is worse than a failure: it reads as a slow machine, not a missing file. `frontend/.eslintrc.json` extends `next/core-web-vitals`, the tree is clean under it, and both `make lint` and CI now run `--max-warnings=0` so the next warning fails the build.
22. **The default retrieval path was called `_mock_chunks`.** Nothing in it is mocked — it reads the real corpus through `_offline_index()` and scores it lexically — but the name meant a reader had to open the body to find out whether the offline answers were real, which is the opposite of what a name is for. It is `_offline_search` now. This is the same class of defect as the deleted `graph.py` (a real-looking path that did not do what it said) and the stale corpus hash, just caught earlier.

### Verified working (checked end to end, not assumed)

| Area | Status | How it was checked |
|---|---|---|
| Backend tests | 148 passing, 0 failing | `cd backend && pytest -q` |
| Pipeline eval | 20/20 cases, verdict PASS | `make eval` — abstention, jurisdiction, IP type, top citation, quote integrity, firewall integrity all 1.000 |
| Confidence calibration | In-scope 60.1–96.0, out-of-scope 5.0–45.0, gate 45 | `make eval` calibration block. The printed out-of-scope band reaches 45.0 because it includes the one case caught by the `_OUT_OF_SCOPE` regex short-circuit rather than by score; on score alone the band is 5.0–32.9, so the gate still sits in a clear gap. |
| Corpus coverage | 23 documents, 34 chunks, version `c48970b2c9b5` | `make ingest-dry` |
| Four homepage demo buttons | All four answer with the right Act: 58.0 / 65.7 / 96.0 / 59.5 | Direct API calls, query strings taken from `lib/i18n.ts` |
| …the same four buttons before this pass | **All four abstained**: 22.7 / 17.0 / 67.0 / 15.0, and every one reported `firewall: clean` | Same four queries posted to `44faf11` checked out in a scratch `git worktree`. The fixed `0.62 + (raw/ceiling)*0.33` floor in `retriever.py` met a `0.70` gate, so even a 0.67-relevance answer abstained. |
| Jurisdiction firewall | Removes 11 of 27 foreign candidates on the flagship question; verdicts `filtered` / `mixed_query` | Direct API calls, `foreign_ratio` non-zero |
| Safe abstention | "write me a poem", "capital of France", keyboard mash, weather, sports, nonsense — all abstain | `make eval` out-of-scope band |
| Quote integrity | Every `>` line is a verbatim substring of a cited span, across all 20 cases | `make eval` quote_integrity, plus a unit test |
| System notices | Never rendered as blockquotes | Unit test over firewall, mismatch and paid-database notices |
| Real multilingual UI | 69 UI + 22 triage strings and 11 glossary definitions in en/hi/ta, all three sets identical | `make check-i18n` |
| Frontend syntax | 23 files parse clean | `make check-frontend` — and it exits 2 with an actionable message, rather than crashing, when TypeScript is not installed |
| **Frontend typecheck** | **Clean — exit 0, all 23 project files** | `tsc --noEmit` against the pinned TypeScript 5.5.2 |
| **Frontend lint** | **Clean — "No ESLint warnings or errors"** | `next lint --max-warnings=0` |
| **Frontend production build** | **Succeeds — 7/7 static pages, `/` at 19.7 kB / 116 kB first load** | `next build`, which also runs its own type check and lint pass |
| `make check` as one command | test → eval → i18n all pass, then stops at the frontend gate with that same message | `make check PYTHON=… PYTEST=…` — the interpreter is overridable so the gate runs without an activated venv |
| Offline path | No embedding model constructed; index built once in ~1.4 s | Instrumented `get_embedder`, 0 calls |
| Container corpus path | Simulated container layout and the real layout resolve to the same directory and the same `c48970b2c9b5` / 23 docs | Direct call under a `/app`-shaped tree |

### What changed in the pass before that (2026-09-01)

A usability pass. The interface was cluttered and, more seriously, the language switch did not work.

1. **The multilingual claim did not survive a click.** Only three strings in the whole app responded to the language switch, and they swapped between romanised Hinglish ("Aapka sawaal") and English. Nothing was ever rendered in Devanagari, and picking தமிழ் changed *nothing at all*: a Tamil speaker saw romanised Hindi. The only Devanagari and Tamil characters in the codebase were the three pill labels themselves. Every UI string now lives in `frontend/lib/i18n.ts` in all three languages and scripts. (The 2026-09-15 pass above found and fixed the four places that pass had missed.)
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
4. **The reranker returned chunks out of order relative to their scores.** It reordered the list but left each chunk's original score untouched. (The 2026-09-15 pass found that this fix had not gone far enough — see item 6 above.)
5. **CORS origins were hardcoded.** Only `localhost:3000` and `*.vercel.app` were allowed, so serving the UI from any other host or port required editing source. Set `CORS_EXTRA_ORIGINS` in `.env` instead (comma-separated).

### Known retrieval limitation, left deliberately

The flagship question leads with Patents Act **Sec 3(d)** (mere discovery) and puts **Sec 3(p)**, the traditional-knowledge bar, at position 2.

This is a real limitation, not a mis-citation: the answer's verdict is correct, Sec 3(p) is quoted in full immediately below, and the reader is not misled about the outcome. The cause is that ranking is lexical and the 3(p) span says "is not an invention" rather than using the question's own word "patentable", so it loses on term overlap to a span that does.

It was left alone on purpose. The honest fix is to rank spans, not just documents — `order_by_ip_type` currently partitions on document identity, so it can put the Patents Act first but cannot prefer one section of it over another. That is a real piece of work, and nudging the weights instead would overfit to one phrasing.

Note that the limitation this section used to describe — the "naya extract" demo button citing the Plant Varieties Act first — **no longer reproduces**. That button now leads with the Patents Act, which occupies its first four citations (Sec 3(d), Sec 3(p), Sec 10, Sec 25) with TKDL fifth, and the Plant Varieties Act does not appear at all. It is recorded here only so the next reader does not go looking for it.

### Suggested next steps, roughly in order of value

1. **Rank spans, not documents.** The one measurable retrieval defect left (see above). Extend `order_by_ip_type` in `backend/app/rag/reranker.py` to prefer the provision the classified IP type actually rests on, and add a golden case that asserts the *locator* of the top citation, not just its document.
2. **Get a free Bhashini API key** and set `BHASHINI_API_KEY` in `.env`. The interface is already multilingual, but answer bodies stay English until a key is present. For an "AI for Bharat" pitch this is the single highest-impact hour of work available.
3. **Expand the thin corpus documents.** `ppvfr_act_2001.md`, `gi_act_1999.md` and similar are only a few lines each. Longer documents both retrieve more accurately and quote more usefully.
4. **Add more case law.** Only two landmark matters are covered (Divya Pharmacy, and the turmeric and neem revocations). The `case_law` retriever is wired and working, so new documents drop straight in.
5. **Localise the generated `posture_table` and `next_steps`** from the triage flow, which are still English regardless of the chosen language.

### Local development gotchas worth knowing

- **Do not run `npm run build` while `next dev` is running.** Both write to `.next` and the dev server will start serving unstyled pages. If that happens, stop the server, `rm -rf frontend/.next`, and restart.
- **The backend does not auto-reload** unless you pass `--reload`. After editing anything under `backend/app`, restart uvicorn or your change will not be live. (`make backend-run` and the compose stack both pass it for you.)
- **Port 8000 may be occupied** by another project on your machine. If the header badge reads "backend offline" or shows a corpus version you do not recognise, the frontend is talking to the wrong server. Set `NEXT_PUBLIC_API_URL` in `frontend/.env.local` and add the matching origin to `CORS_EXTRA_ORIGINS`.
- **The first request builds the corpus index**, which takes about 1.4 s; after that it is cached and requests run in 150–250 ms. Send one warm-up query before demoing.
- **Without Postgres, every request logs `audit.db_write_failed`.** That is expected and harmless — the structured log line above it is the audit record, and the DB write is best-effort. Start the stack with `make up` to silence it.
- **Every backend `make` target runs `python`, not your venv's python, unless the venv is active.** If `make eval` or `make test` fails with `ModuleNotFoundError: No module named 'fastapi'` while `python -m pytest` works in your shell, the Makefile is picking up a different interpreter. Point it at the right one instead of activating: `make check PYTHON=backend/.venv/bin/python PYTEST="backend/.venv/bin/python -m pytest"`. (`check-frontend` has the same escape hatch for its TypeScript resolution: `TYPESCRIPT_PATH=frontend/node_modules/typescript`.)

---

## Quick start (no accounts, no cost)

```bash
make up                # creates .env from .env.example if needed, then starts everything
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

### New here? 60-second health check

```bash
make test         # backend suite — expect 148 passed, 0 failed
make ingest-dry   # corpus preview — expect 23 docs, 34 chunks, no changes made
make check        # tests + eval + i18n parity + frontend parse, all gates
```

Then ask one question in the UI ("Can I patent my grandmother's churna recipe?")
and confirm: an answer with quotes, source links, a confidence score, and a corpus hash.
If the header badge reads "backend offline", the frontend is talking to the wrong
server — see "Port 8000 may be occupied" below.

### Adding more law documents
```bash
make ingest-dry   # preview what would be loaded, no changes made
make ingest       # actually load and index the documents
make corpus-hash  # print the version hash shown on every answer
```

### Checking answer quality
```bash
make eval   # grades the real pipeline on 20 questions; exits non-zero on any failure
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

1. Pick India or International at the top. The two never get mixed.
2. Tap an example question, or type your own in plain words, no legal terms needed.
3. Try the 3-question triage: three taps tell you your formulation's category and what it means.
4. Turn on "Simple" mode to get a plain-language version alongside the legal one.
5. Check the right-hand panel: every claim links back to the real government source, with a version hash.

## API

`POST /api/v1/chat` with `{query, jurisdiction, language, explain_simple, formulation, session_id}` returns `{answer, answer_simple, jurisdiction, citations[], confidence, corpus_version, firewall, free_tier}`.

Full request and response shapes are in `backend/app/models/schemas.py`.

---

License: MIT (see `LICENSE`). The law documents in `corpus/` are public-domain government text, see `corpus/manifest.json` for sources.
