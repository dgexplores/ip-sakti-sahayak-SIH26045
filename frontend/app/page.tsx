"use client";
import { useEffect, useRef, useState } from "react";
import { JurisdictionToggle } from "@/components/JurisdictionToggle";
import { ConfidenceBadge, ConfidenceBar } from "@/components/ConfidenceBadge";
import { CitationPane } from "@/components/CitationPane";
import { FormulationFlow, PostureTable } from "@/components/FormulationFlow";
import { EscalateButton } from "@/components/EscalateButton";
import { chat, getCorpusVersion, type ChatResponse, type Jurisdiction } from "@/lib/api";

const EXAMPLES = [
  { label: "Classical?", jurisdiction: "india" as Jurisdiction, q: "Is classical Ashwagandha churna as per Charaka Samhita patentable in India?" },
  { label: "Novel extract", jurisdiction: "india" as Jurisdiction, q: "I made a novel Ashwagandha extract with 10x withanolide by new process — patentable?" },
  { label: "GRATK PCT", jurisdiction: "international" as Jurisdiction, q: "WIPO GRATK disclosure requirement for PCT filing with Indian genetic resource" },
  { label: "ABS Kerala", jurisdiction: "india" as Jurisdiction, q: "Do I need NBA approval to source aloe vera from Kerala for cosmetic export?" },
];

export default function Page() {
  const [jurisdiction, setJurisdiction] = useState<Jurisdiction>("india");
  const [query, setQuery] = useState("");
  const [lang, setLang] = useState("en");
  const [loading, setLoading] = useState(false);
  const [res, setRes] = useState<ChatResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [corpus, setCorpus] = useState<{ corpus_version: string; document_count: number } | null>(null);
  const [sessionId] = useState(() => `sess_${Math.random().toString(36).slice(2, 10)}`);
  const [showTriage, setShowTriage] = useState(false);
  const [formulation, setFormulation] = useState<any>(null);
  const scroller = useRef<HTMLDivElement>(null);

  useEffect(() => { getCorpusVersion().then(setCorpus).catch(() => {}); }, []);

  async function onSend(q?: string, form?: any) {
    const text = (q ?? query).trim();
    if (!text) return;
    setLoading(true); setError(null);
    try {
      const r = await chat(text, jurisdiction, lang, form ?? formulation ?? undefined, sessionId);
      setRes(r);
      // auto-scroll citations
      setTimeout(() => scroller.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 100);
    } catch (e: any) { setError(e.message || "request failed"); }
    finally { setLoading(false); }
  }

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="sticky top-0 z-30 backdrop-blur bg-white/80 border-b border-stone-200">
        <div className="mx-auto max-w-[1280px] px-4 sm:px-6 py-3 flex items-center gap-3 sm:gap-6">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-ink text-white grid place-items-center font-bold text-sm">IP</div>
            <div>
              <div className="h-display text-[17px] font-extrabold leading-none">IP-SAKTI</div>
              <div className="text-[11px] tracking-widest font-semibold text-stone-500 -mt-0.5">SAHAYAK · SIH26045</div>
            </div>
            <span className="hidden sm:inline-flex ml-2 text-[11px] font-mono px-2 py-1 rounded-full bg-stone-100 border border-stone-200">{corpus ? `corpus ${corpus.corpus_version} · ${corpus.document_count} docs` : "corpus loading…"}</span>
          </div>
          <div className="ml-auto hidden lg:flex items-center gap-2 text-xs text-stone-500">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" /> Deployable · Audited · DPDP-aligned
          </div>
          <a href="http://localhost:8000/docs" target="_blank" className="hidden sm:inline-flex text-xs font-semibold px-3 py-2 rounded-full bg-white border border-stone-300 hover:bg-stone-50">API docs ↗</a>
        </div>
        {/* Jurisdiction bar — senior: hard toggle, never conflated */}
        <div className="mx-auto max-w-[1280px] px-4 sm:px-6 pb-3 flex flex-wrap items-center gap-3">
          <JurisdictionToggle value={jurisdiction} onChange={setJurisdiction} />
          <div className="flex items-center gap-2 ml-auto">
            <label className="text-xs font-medium text-stone-600">Language</label>
            <select value={lang} onChange={(e) => setLang(e.target.value)} className="text-sm rounded-full border border-stone-300 bg-white px-3 py-1.5">
              <option value="en">English</option><option value="hi">हिन्दी</option><option value="ta">தமிழ்</option><option value="kn">ಕನ್ನಡ</option><option value="te">తెలుగు</option><option value="mr">मराठी</option>
            </select>
            <button onClick={() => setShowTriage((v) => !v)} className="text-xs font-semibold px-3 py-2 rounded-full bg-amber-500 text-white hover:bg-amber-600">3Q Triage {showTriage ? "−" : "+"}</button>
          </div>
        </div>
        <div className="h-1 w-full flex">
          <div className={`flex-1 transition-all ${jurisdiction === "india" ? "bg-saffron" : "bg-stone-200"}`} />
          <div className={`flex-1 transition-all ${jurisdiction === "international" ? "bg-indiaBlue" : "bg-stone-200"}`} />
        </div>
      </header>

      {/* Hero + main */}
      <main className="mx-auto max-w-[1280px] px-4 sm:px-6 py-6 grid grid-cols-1 lg:grid-cols-[1.15fr_0.85fr] gap-6">
        {/* Left: chat */}
        <div className="space-y-4">
          <div className="rounded-2xl bg-white border border-stone-200 shadow-card p-5">
            <h1 className="h-display text-2xl sm:text-3xl font-extrabold leading-tight">Ask IP & regulatory — <span className={jurisdiction === "india" ? "text-saffron-dark" : "text-indiaBlue"}>{jurisdiction === "india" ? "India" : "International"}</span> answers, <span className="underline decoration-amber-300 decoration-4 underline-offset-2">never mixed</span>.</h1>
            <p className="text-sm text-stone-600 mt-2 leading-relaxed">Every claim cites statute/rule/treaty span + registry record. Low confidence → abstains + escalates. Bhashini voice → preserves legal terms.</p>
            <div className="flex flex-wrap gap-2 mt-3">
              {EXAMPLES.map((ex) => (
                <button
                  key={ex.label}
                  onClick={() => { setQuery(ex.q); setJurisdiction(ex.jurisdiction); onSend(ex.q); }}
                  className={`text-xs font-medium px-3 py-1.5 rounded-full border ${jurisdiction === ex.jurisdiction ? "bg-stone-900 text-white border-stone-900" : "bg-white text-stone-700 border-stone-300 hover:bg-stone-50"}`}
                >
                  {ex.label} · {ex.jurisdiction === "india" ? "INDIA" : "INTL"} →
                </button>
              ))}
            </div>
          </div>

          {showTriage && (
            <FormulationFlow
              onComplete={(ans) => {
                setFormulation(ans);
                onSend(query || "Classify my formulation: classical vs proprietary vs phytopharma", ans);
              }}
            />
          )}

          <div className="rounded-2xl bg-white border border-stone-200 shadow-card p-4">
            <div className="flex gap-3">
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) onSend(); }}
                placeholder={jurisdiction === "india" ? "e.g., Is proprietary chyawanprash with novel honey ratio patentable under Sec 3(p)?" : "e.g., WIPO GRATK Art 3 disclosure for PCT with Indian TK?"}
                rows={3}
                className="flex-1 resize-none rounded-xl border border-stone-300 bg-stone-50 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-ink/20 focus:border-ink"
              />
            </div>
            <div className="flex items-center gap-2 mt-3">
              <button onClick={() => onSend()} disabled={loading || !query.trim()} className="px-5 py-2.5 rounded-xl bg-ink text-white text-sm font-semibold hover:bg-stone-800 disabled:opacity-50 disabled:cursor-not-allowed">
                {loading ? "Retrieving 4 sources…" : `Ask in ${jurisdiction.toUpperCase()} →`}
              </button>
              <span className="text-xs text-stone-500">⌘+Enter to send · Jurisdiction is hard toggle</span>
              {res?.latency_ms && <span className="ml-auto text-xs font-mono text-stone-400">{res.latency_ms}ms</span>}
            </div>
            {error && <div className="mt-3 rounded-xl bg-red-50 border border-red-200 p-3 text-sm text-red-800">{error} — is backend on http://localhost:8000 ? <code className="bg-white px-1 rounded">make up</code></div>}
          </div>

          {/* Answer */}
          {res && (
            <div className="rounded-2xl border-2 bg-white shadow-card overflow-hidden" style={{ borderColor: jurisdiction === "india" ? "#FF9933" : "#0B2239" }}>
              <div className={`px-4 py-2 flex items-center gap-3 text-xs font-semibold tracking-widest uppercase ${jurisdiction === "india" ? "bg-saffron-light text-amber-900" : "bg-indiaBlue text-sky-100"}`}>
                <span>{res.jurisdiction.toUpperCase()} ANSWER</span>
                <span className="ml-auto flex items-center gap-2"><ConfidenceBadge score={res.confidence.score} abstain={res.confidence.abstain} /></span>
              </div>
              <div className="p-5">
                <div className="prose prose-sm max-w-none whitespace-pre-wrap leading-relaxed text-[15px]">{res.answer}</div>
                <div className="mt-4"><ConfidenceBar score={res.confidence.score} /></div>
                <p className="mt-2 text-xs text-stone-500">{res.confidence.rationale}</p>
                {res.formulation_result && <div className="mt-4"><PostureTable table={res.formulation_result.posture_table} nextSteps={res.formulation_result.next_steps} category={res.formulation_result.category} /></div>}
                <div className="mt-4 flex flex-wrap items-center gap-2 text-xs">
                  <span className="font-mono px-2 py-1 rounded-full bg-stone-100 border border-stone-200">corpus {res.corpus_version}</span>
                  <span className="text-stone-400">· {res.disclaimer}</span>
                </div>
                <div className="mt-4"><EscalateButton sessionId={sessionId} query={query} jurisdiction={jurisdiction} citations={res.citations} /></div>
                {res.escalate_suggested && <p className="mt-2 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-xl p-2">Low confidence — suggested to escalate. All queries & citations are audit-logged (DPDP).</p>}
              </div>
            </div>
          )}

          {/* Empty state */}
          {!res && !loading && (
            <div className="rounded-2xl border border-dashed border-stone-300 bg-white p-6 text-sm text-stone-600">
              <div className="font-semibold text-ink">How it’s different from generic LLM / ip-sakti.vercel.app demo</div>
              <ul className="mt-2 space-y-1.5 list-disc pl-5">
                <li><b>Jurisdiction split</b> — India vs International never conflated (hard toggle + visibly separate columns).</li>
                <li><b>3Q triage</b> — classical vs proprietary vs phytopharma in one step.</li>
                <li><b>Triple citation + confidence + abstain</b> — not hallucinated sections.</li>
                <li><b>Version hash per answer</b> — proves 2024 Rules + GRATK freshness.</li>
                <li><b>DPDP audit + facilitator ticket</b> — every query logged with consent.</li>
              </ul>
            </div>
          )}
        </div>

        {/* Right: citations + meta */}
        <div className="space-y-4" ref={scroller}>
          <div className="rounded-2xl bg-white border border-stone-200 shadow-card p-4">
            <CitationPane citations={res?.citations ?? []} corpusVersion={res?.corpus_version ?? corpus?.corpus_version} />
          </div>

          <div className="rounded-2xl border border-stone-200 bg-stone-900 text-stone-100 p-4">
            <div className="text-xs font-semibold tracking-widest uppercase text-stone-400">Pipeline · observable · idempotent</div>
            <div className="mt-3 space-y-2 font-mono text-xs leading-relaxed">
              <div>query → Bhashini ASR → classifier → formulation (if needed) → 4× retriever (parallel) → Cohere rerank → cross-check → LLM (temp 0) → citation assembler → Bhashini TTS</div>
              <div className="text-stone-400">loader → chunker (800/120, section-aware) → embedder (batched, Redis cache) → pgvector/Qdrant upsert (doc_id#chunk_id)</div>
              <div className="flex gap-2 pt-2">
                <span className="px-2 py-1 rounded bg-white/10">FastAPI + LangGraph</span><span className="px-2 py-1 rounded bg-white/10">pgvector · Neo4j</span><span className="px-2 py-1 rounded bg-white/10">RAGAS</span>
              </div>
            </div>
          </div>

          <div className="rounded-2xl bg-white border border-stone-200 p-4 text-xs leading-relaxed text-stone-600">
            <div className="font-semibold text-ink">Demo script (2 min, judge’s delight)</div>
            <ol className="mt-2 space-y-1 list-decimal pl-5">
              <li>Hit <b>Classical?</b> · India → Sec 3(p) + TKDL pointer + confidence.</li>
              <li>Toggle <b>International</b> → WIPO GRATK Art 3 disclosure, PCT route — visibly separate column.</li>
              <li>Open 3Q triage → show posture table (IP/ABS/Regulatory) + next steps.</li>
              <li>Point to version hash + “Verify at” links. Click escalate → ticket.</li>
            </ol>
            <p className="mt-3 text-[11px] text-stone-400">Staged: W1–2 MVP (this) → W3 graph+agentic → W4 paid+voice. Theme MedTech 18 + Org Ayush 5 = lowest competition.</p>
          </div>
        </div>
      </main>

      <footer className="mx-auto max-w-[1280px] px-6 py-6 text-center text-xs text-stone-400">
        IP-SAKTI Sahayak · Information, not legal advice. Verify at source links before filing. · DPDP audit retained 365 days · Paid DB only with explicit consent.
      </footer>
    </div>
  );
}
