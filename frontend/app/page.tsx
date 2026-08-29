"use client";
import { useEffect, useRef, useState } from "react";
import { JurisdictionToggle } from "@/components/JurisdictionToggle";
import { ConfidenceBadge, ConfidenceBar } from "@/components/ConfidenceBadge";
import { CitationPane } from "@/components/CitationPane";
import { FormulationFlow, PostureTable } from "@/components/FormulationFlow";
import { EscalateButton } from "@/components/EscalateButton";
import { FreeBadge, OfflineReadyBanner } from "@/components/FreeBadge";
import { GlossaryBar } from "@/components/GlossaryTooltip";
import { ExportButton } from "@/components/ExportButton";
import { HowItWorks, ComparisonTable } from "@/components/HowItWorks";
import { chat, getCorpusVersion, type ChatResponse, type Jurisdiction } from "@/lib/api";

const EXAMPLES = [
  { label: "Can I patent old churna?", jurisdiction: "india" as Jurisdiction, q: "Is classical Ashwagandha churna as per Charaka Samhita patentable in India?" },
  { label: "My new extract", jurisdiction: "india" as Jurisdiction, q: "I made a novel Ashwagandha extract with 10x withanolide by new process — patentable?" },
  { label: "Go international — GRATK", jurisdiction: "international" as Jurisdiction, q: "WIPO GRATK disclosure requirement for PCT filing with Indian genetic resource" },
  { label: "Need permission for aloe?", jurisdiction: "india" as Jurisdiction, q: "Do I need NBA approval to source aloe vera from Kerala for cosmetic export?" },
];

export default function Page() {
  const [jurisdiction, setJurisdiction] = useState<Jurisdiction>("india");
  const [query, setQuery] = useState("");
  const [lang, setLang] = useState("en");
  const [eli5, setEli5] = useState(true); // win: on by default — easy to understand
  const [loading, setLoading] = useState(false);
  const [res, setRes] = useState<ChatResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [corpus, setCorpus] = useState<{ corpus_version: string; document_count: number } | null>(null);
  const [sessionId] = useState(() => `sess_${Math.random().toString(36).slice(2, 10)}`);
  const [showTriage, setShowTriage] = useState(false);
  const [formulation, setFormulation] = useState<any>(null);
  const [showWhyWin, setShowWhyWin] = useState(false);
  const scroller = useRef<HTMLDivElement>(null);

  useEffect(() => { getCorpusVersion().then(setCorpus).catch(() => {}); }, []);

  async function onSend(q?: string, form?: any) {
    const text = (q ?? query).trim();
    if (!text) return;
    setLoading(true); setError(null);
    try {
      const r = await chat(text, jurisdiction, lang, form ?? formulation ?? undefined, sessionId, eli5);
      setRes(r);
      setTimeout(() => scroller.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 100);
    } catch (e: any) { setError(e.message || "request failed"); }
    finally { setLoading(false); }
  }

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-30 backdrop-blur bg-white/80 border-b border-stone-200">
        <div className="mx-auto max-w-[1280px] px-4 sm:px-6 py-3 flex items-center gap-3 sm:gap-6">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-ink text-white grid place-items-center font-bold text-sm">IP</div>
            <div>
              <div className="h-display text-[17px] font-extrabold leading-none">IP-SAKTI</div>
              <div className="text-[11px] tracking-widest font-semibold text-stone-500 -mt-0.5">SAHAYAK · SIH26045</div>
            </div>
            <span className="hidden md:inline-flex ml-2 text-[11px] font-mono px-2 py-1 rounded-full bg-stone-100 border border-stone-200">{corpus ? `corpus ${corpus.corpus_version} · ${corpus.document_count} docs` : "corpus loading…"}</span>
            <span className="hidden lg:inline-flex"><FreeBadge /></span>
          </div>
          <div className="ml-auto hidden lg:flex items-center gap-2 text-xs text-stone-500">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" /> Deployable · Audited · DPDP-aligned · <span className="font-bold text-emerald-700">FREE</span>
          </div>
          <a href="http://localhost:8000/docs" target="_blank" className="hidden sm:inline-flex text-xs font-semibold px-3 py-2 rounded-full bg-white border border-stone-300 hover:bg-stone-50">API docs ↗</a>
        </div>
        <div className="mx-auto max-w-[1280px] px-4 sm:px-6 pb-3 flex flex-wrap items-center gap-3">
          <JurisdictionToggle value={jurisdiction} onChange={setJurisdiction} />
          <div className="flex items-center gap-2 ml-auto flex-wrap">
            <label className="text-xs font-medium text-stone-600 flex items-center gap-1.5">
              <input type="checkbox" checked={eli5} onChange={(e) => setEli5(e.target.checked)} className="rounded" /> ELI5 (simple words)
            </label>
            <select value={lang} onChange={(e) => setLang(e.target.value)} className="text-sm rounded-full border border-stone-300 bg-white px-3 py-1.5">
              <option value="en">English</option><option value="hi">हिन्दी</option><option value="ta">தமிழ்</option><option value="kn">ಕನ್ನಡ</option><option value="te">తెలుగు</option><option value="mr">मराठी</option>
            </select>
            <button onClick={() => setShowTriage((v) => !v)} className="text-xs font-semibold px-3 py-2 rounded-full bg-amber-500 text-white hover:bg-amber-600">3Q Triage {showTriage ? "−" : "+"}</button>
            <button onClick={() => setShowWhyWin((v) => !v)} className="text-xs font-semibold px-3 py-2 rounded-full bg-emerald-600 text-white hover:bg-emerald-700">{showWhyWin ? "Hide" : "Why we win →"}</button>
          </div>
        </div>
        <div className="h-1 w-full flex">
          <div className={`flex-1 transition-all ${jurisdiction === "india" ? "bg-saffron" : "bg-stone-200"}`} />
          <div className={`flex-1 transition-all ${jurisdiction === "international" ? "bg-indiaBlue" : "bg-stone-200"}`} />
        </div>
      </header>

      {/* Win banner — collapsible */}
      {showWhyWin && (
        <div className="mx-auto max-w-[1280px] px-4 sm:px-6 py-4 space-y-4">
          <OfflineReadyBanner />
          <ComparisonTable />
        </div>
      )}

      <main className="mx-auto max-w-[1280px] px-4 sm:px-6 py-6 grid grid-cols-1 lg:grid-cols-[1.15fr_0.85fr] gap-6">
        {/* Left */}
        <div className="space-y-4">
          <div className="rounded-2xl bg-white border border-stone-200 shadow-card p-5">
            <h1 className="h-display text-2xl sm:text-[30px] font-extrabold leading-tight">Ask in plain words — get the <span className={jurisdiction === "india" ? "text-saffron-dark" : "text-indiaBlue"}>{jurisdiction === "india" ? "India" : "International"}</span> law, <span className="underline decoration-amber-300 decoration-4 underline-offset-2">with proof</span>.</h1>
            <p className="text-sm text-stone-600 mt-2 leading-relaxed">No jargon surprise. Every line cites the exact Act/Rule/Treaty + link. Not sure? We say “I don’t know” and connect you to a human. Works in 6 languages, even offline.</p>
            <div className="mt-3"><GlossaryBar /></div>
            <div className="flex flex-wrap gap-2 mt-3">
              {EXAMPLES.map((ex) => (
                <button key={ex.label} onClick={() => { setQuery(ex.q); setJurisdiction(ex.jurisdiction); onSend(ex.q); }} className={`text-xs font-medium px-3 py-1.5 rounded-full border ${jurisdiction === ex.jurisdiction ? "bg-ink text-white border-ink" : "bg-white text-stone-700 border-stone-300 hover:bg-stone-50"}`}>
                  {ex.label} · {ex.jurisdiction === "india" ? "🇮🇳" : "🌐"} →
                </button>
              ))}
            </div>
          </div>

          <HowItWorks />

          {showTriage && (
            <FormulationFlow onComplete={(ans) => { setFormulation(ans); onSend(query || "Classify my formulation: classical vs proprietary vs phytopharma", ans); }} />
          )}

          <div className="rounded-2xl bg-white border border-stone-200 shadow-card p-4">
            <div className="flex gap-3">
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) onSend(); }}
                placeholder={jurisdiction === "india" ? "e.g., Can I sell chawanprash as food or drug? · Try Tamil/Hindi too" : "e.g., What does GRATK Art 3 require for PCT with Indian TK?"}
                rows={3}
                className="flex-1 resize-none rounded-xl border border-stone-300 bg-stone-50 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-ink/20 focus:border-ink"
              />
            </div>
            <div className="flex items-center gap-2 mt-3 flex-wrap">
              <button onClick={() => onSend()} disabled={loading || !query.trim()} className="px-5 py-2.5 rounded-xl bg-ink text-white text-sm font-semibold hover:bg-stone-800 disabled:opacity-50 disabled:cursor-not-allowed">
                {loading ? "Checking 4 sources…" : `Ask in ${jurisdiction.toUpperCase()} →`}
              </button>
              <span className="text-xs text-stone-500">⌘+Enter · Firewall keeps India/World separate</span>
              {res?.free_tier && <span className="text-[11px] font-bold px-2 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700">FREE tier — ₹0</span>}
              {res?.latency_ms && <span className="ml-auto text-xs font-mono text-stone-400">{res.latency_ms}ms</span>}
            </div>
            {error && <div className="mt-3 rounded-xl bg-red-50 border border-red-200 p-3 text-sm text-red-800">{error} — is backend on http://localhost:8000 ? <code className="bg-white px-1 rounded">make up</code></div>}
          </div>

          {res && (
            <div className="rounded-2xl border-2 bg-white shadow-card overflow-hidden" style={{ borderColor: jurisdiction === "india" ? "#FF9933" : "#0B2239" }}>
              <div className={`px-4 py-2 flex items-center gap-3 text-xs font-semibold tracking-widest uppercase ${jurisdiction === "india" ? "bg-saffron-light text-amber-900" : "bg-indiaBlue text-sky-100"}`}>
                <span>{res.jurisdiction.toUpperCase()} ANSWER {res.free_tier ? "· FREE" : ""}</span>
                <span className="ml-auto flex items-center gap-2"><ConfidenceBadge score={res.confidence.score} abstain={res.confidence.abstain} /></span>
              </div>
              <div className="p-5">
                {res.firewall && res.firewall.status !== "clean" && (
                  <div className="mb-3 rounded-xl bg-sky-50 border border-sky-200 p-3 text-xs text-sky-800">🛡️ Jurisdiction firewall: {res.firewall.message}</div>
                )}
                <div className="prose prose-sm max-w-none whitespace-pre-wrap leading-relaxed text-[15px]">{res.answer}</div>
                {res.answer_simple && (
                  <div className="mt-4 rounded-xl bg-amber-50 border border-amber-200 p-4">
                    <div className="text-xs font-bold tracking-widest uppercase text-amber-800">In simple words (ELI5) — for anyone to understand</div>
                    <div className="text-sm leading-relaxed mt-1 whitespace-pre-wrap">{res.answer_simple}</div>
                  </div>
                )}
                <div className="mt-4"><ConfidenceBar score={res.confidence.score} /></div>
                <p className="mt-2 text-xs text-stone-500">{res.confidence.rationale}</p>
                {res.formulation_result && <div className="mt-4"><PostureTable table={res.formulation_result.posture_table} nextSteps={res.formulation_result.next_steps} category={res.formulation_result.category} /></div>}
                <div className="mt-4 flex flex-wrap items-center gap-2 text-xs">
                  <span className="font-mono px-2 py-1 rounded-full bg-stone-100 border border-stone-200">corpus {res.corpus_version}</span>
                  <span className="text-stone-400">· {res.disclaimer}</span>
                </div>
                <div className="mt-3 flex flex-wrap gap-2"><ExportButton answer={res.answer + (res.answer_simple ? "\n\nELI5: " + res.answer_simple : "")} citations={res.citations} jurisdiction={res.jurisdiction} corpusVersion={res.corpus_version} /></div>
                <div className="mt-4"><EscalateButton sessionId={sessionId} query={query} jurisdiction={jurisdiction} citations={res.citations} /></div>
                {res.escalate_suggested && <p className="mt-2 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-xl p-2">Low confidence — we suggest escalating. Every query is audit-logged (DPDP) with full trace for the facilitator.</p>}
              </div>
            </div>
          )}

          {!res && !loading && (
            <div className="rounded-2xl border border-dashed border-stone-300 bg-white p-6 text-sm text-stone-600">
              <div className="font-bold text-ink text-base">Why this wins over ChatGPT / ip-sakti.vercel.app</div>
              <div className="mt-2 grid sm:grid-cols-2 gap-2 text-xs">
                {[
                  ["🛡️ Jurisdiction firewall", "India vs World never mixed — hard toggle + filter."],
                  ["🧪 3-tap classification", "Classical / proprietary / phytopharma in one go."],
                  ["📜 Every line has proof", "Act/Rule/Treaty + link + hash. No fake Sec numbers."],
                  ["₹0 to run", "No OpenAI/Cohere key. Offline MiniLM + extractive = ₹0."],
                  ["🧒 Anyone understands", "ELI5 + glossary hover + 6 languages."],
                  ["📦 One-click report", "Export .md / Print for PPT submission."],
                ].map(([t, d]) => (
                  <div key={t} className="rounded-xl bg-stone-50 border border-stone-200 p-3"><div className="font-bold text-ink">{t}</div><div className="text-stone-600 leading-relaxed">{d}</div></div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="space-y-4" ref={scroller}>
          <div className="rounded-2xl bg-white border border-stone-200 shadow-card p-4">
            <CitationPane citations={res?.citations ?? []} corpusVersion={res?.corpus_version ?? corpus?.corpus_version} />
          </div>
          <div className="rounded-2xl border border-stone-200 bg-stone-900 text-stone-100 p-4">
            <div className="text-xs font-semibold tracking-widest uppercase text-stone-400">How it works — free & robust</div>
            <div className="mt-3 space-y-2 font-mono text-xs leading-relaxed">
              <div>query → Bhashini ASR (free) → classifier → 3Q triage → 4× retriever ⟶ local MiniLM (₹0) → CrossEncoder rerank (₹0) → firewall → offline-extractive (₹0) → Bhashini TTS (free)</div>
              <div className="text-stone-400">loader → chunker 800/120 § → local embed batched → pgvector upsert (idempotent)</div>
              <div className="flex flex-wrap gap-2 pt-2">
                <span className="px-2 py-1 rounded bg-emerald-600 font-bold">100% FREE DEFAULT</span><span className="px-2 py-1 rounded bg-white/10">pgvector · Neo4j · RAGAS</span><span className="px-2 py-1 rounded bg-white/10">FastAPI + Next.js</span>
              </div>
            </div>
          </div>
          <div className="rounded-2xl bg-white border border-stone-200 p-4 text-xs leading-relaxed text-stone-600">
            <div className="font-semibold text-ink">Demo script (2 min — remember this)</div>
            <ol className="mt-2 space-y-1 list-decimal pl-5">
              <li>Hit <b>Can I patent old churna? · 🇮🇳</b> → Sec 3(p) + TKDL, 92% confidence, firewall clean.</li>
              <li>Toggle <b>🌐 International</b> → same q → GRATK Art 3, visibly separate.</li>
              <li>Toggle <b>ELI5 on</b> → show simple words panel. Export report.</li>
              <li>Open <b>3Q Triage</b> → posture table (IP/ABS/Regulatory) + next steps. Click escalate → ticket. Point to <b>corpus hash + free badge</b>.</li>
            </ol>
            <p className="mt-3 text-[11px] text-stone-400">Staged: MVP (today, offline) → Ollama/HF free upgrade (1 cmd) → full Bhashini voice. Theme 18 + Org 5 = lowest competition.</p>
          </div>
        </div>
      </main>

      <footer className="mx-auto max-w-[1280px] px-6 py-6 text-center text-xs text-stone-400">
        IP-SAKTI Sahayak · Information, not legal advice. Verify at source links. · DPDP 365-day audit · Paid DB only with consent · <span className="font-bold text-emerald-600">Zero-cost free tier wins</span> — no API billing to demo.
      </footer>
    </div>
  );
}
