"use client";
import { useEffect, useRef, useState } from "react";
import { JurisdictionToggle } from "@/components/JurisdictionToggle";
import { ConfidenceBadge, ConfidenceBar } from "@/components/ConfidenceBadge";
import { CitationPane } from "@/components/CitationPane";
import { FormulationFlow, PostureTable } from "@/components/FormulationFlow";
import { EscalateButton } from "@/components/EscalateButton";
import { ExportButton } from "@/components/ExportButton";
import { VoiceButton } from "@/components/VoiceButton";
import { FreeBadge } from "@/components/FreeBadge";
import { SplitViewTrigger } from "@/components/SplitView";
import { HowItWorks, ComparisonTable } from "@/components/HowItWorks";
import { Icon, type IconName } from "@/components/Icon";
import { AnswerText } from "@/components/AnswerText";
import { chat, getCorpusVersion, type ChatResponse, type FormulationAnswer, type Jurisdiction } from "@/lib/api";

// Villager examples — short, plain, Hindi-leaning labels, tap does all
const EXAMPLES = [
  { label: "Purana churna patent?", icon: "classical" as IconName, jurisdiction: "india" as Jurisdiction, q: "Is classical Ashwagandha churna as per Charaka Samhita patentable in India?" },
  { label: "Naya extract banaaya", icon: "novel" as IconName, jurisdiction: "india" as Jurisdiction, q: "I made a novel Ashwagandha extract with 10x withanolide by new process, patentable?" },
  { label: "Videsh me patent?", icon: "world" as IconName, jurisdiction: "international" as Jurisdiction, q: "WIPO GRATK disclosure requirement for PCT filing with Indian genetic resource" },
  { label: "Aloe ke liye permission?", icon: "plant" as IconName, jurisdiction: "india" as Jurisdiction, q: "Do I need NBA approval to source aloe vera from Kerala for cosmetic export?" },
];

export default function Page() {
  const [jurisdiction, setJurisdiction] = useState<Jurisdiction>("india");
  const [query, setQuery] = useState("");
  const [lang, setLang] = useState("hi"); // villager default = Hindi
  const [eli5, setEli5] = useState(true);
  const [loading, setLoading] = useState(false);
  const [res, setRes] = useState<ChatResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [corpus, setCorpus] = useState<{ corpus_version: string; document_count: number } | null>(null);
  const [sessionId] = useState(() => `sess_${Math.random().toString(36).slice(2, 10)}`);
  const [showTriage, setShowTriage] = useState(true); // villager: show triage upfront, not hidden
  const [formulation, setFormulation] = useState<FormulationAnswer | null>(null);
  const [corpusError, setCorpusError] = useState(false);
  const scroller = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getCorpusVersion().then(setCorpus).catch(() => setCorpusError(true));
  }, []);

  async function onSend(q?: string, form?: FormulationAnswer) {
    const text = (q ?? query).trim();
    if (!text) return;
    setLoading(true); setError(null);
    try {
      const r = await chat(text, jurisdiction, lang, form ?? formulation ?? undefined, sessionId, eli5);
      setRes(r);
      setTimeout(() => scroller.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 180);
    } catch (e) { setError(e instanceof Error ? e.message : "Request failed."); }
    finally { setLoading(false); }
  }

  return (
    <div className="min-h-screen bg-[#FFFBF5]">
      {/* --- Header: villager trust — big, high contrast, no small gray --- */}
      <header className="sticky top-0 z-30 bg-white border-b-2 border-stone-200">
        <div className="mx-auto max-w-[1280px] px-4 sm:px-6 py-3 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-ink text-white grid place-items-center font-extrabold text-sm">IP</div>
          <div>
            <div className="h-display text-lg font-extrabold leading-none">IP-SAKTI Sahayak</div>
            <div className="text-xs font-bold tracking-widest text-stone-600">Ayurveda ka kanoon dost · SIH26045</div>
          </div>
          <span className="hidden md:inline-flex ml-3"><FreeBadge /></span>
          <span className={`hidden sm:inline-flex ml-auto text-xs font-mono px-2 py-1 rounded-full border ${corpusError ? "bg-red-50 border-red-200 text-red-800" : "bg-stone-100 border-stone-200"}`}>
            {corpus ? `corpus ${corpus.corpus_version}` : corpusError ? "backend offline" : "loading…"}
          </span>
        </div>
        {/* Emil: jurisdiction toggle — spring-like, transform only */}
        <div className="mx-auto max-w-[1280px] px-4 sm:px-6 pb-3 flex flex-wrap items-center gap-3">
          <JurisdictionToggle value={jurisdiction} onChange={setJurisdiction} />
          <div className="ml-auto flex items-center gap-2">
            {/* Villager lang: 3 big pills, not dropdown */}
            {[
              { id: "hi", label: "हिन्दी", sub: "Hindi" },
              { id: "en", label: "English", sub: "En" },
              { id: "ta", label: "தமிழ்", sub: "Tamil" },
            ].map((l) => (
              <button
                key={l.id}
                onClick={() => setLang(l.id)}
                className={`pressable touch-48 px-4 py-2 rounded-full border-2 text-sm font-bold ${lang === l.id ? "bg-ink text-white border-ink" : "bg-white border-stone-300 text-stone-700"}`}
                aria-pressed={lang === l.id}
              >
                {l.label} <span className="text-xs font-normal opacity-70 hidden sm:inline">·{l.sub}</span>
              </button>
            ))}
          </div>
        </div>
        <div className="h-1.5 w-full flex">
          <div className={`flex-1 ${jurisdiction === "india" ? "bg-saffron" : "bg-stone-200"}`} style={{ transition: "background-color 180ms var(--ease-out)" }} />
          <div className={`flex-1 ${jurisdiction === "international" ? "bg-indiaBlue" : "bg-stone-200"}`} style={{ transition: "background-color 180ms var(--ease-out)" }} />
        </div>
      </header>

      <main className="mx-auto max-w-[1280px] px-4 sm:px-6 py-5 grid grid-cols-1 lg:grid-cols-[1.08fr_0.92fr] gap-5">
        {/* LEFT: villager wizard — voice first, then triage, then answer */}
        <div className="space-y-4">
          {/* Hero — one line, 22px, Hindi default */}
          <div className="rounded-[20px] bg-white border-2 border-stone-200 shadow-card p-5 stagger-in">
            <h1 className="h-display text-[22px] sm:text-[26px] font-extrabold leading-tight">
              {lang === "hi" ? <>Aapka sawaal, <span className={jurisdiction === "india" ? "text-saffron" : "text-indiaBlue"}>sarkari saboot</span> ke saath</> : <>Your question, with <span className={jurisdiction === "india" ? "text-saffron" : "text-indiaBlue"}>govt proof</span></>}
            </h1>
            <p className="text-[15px] leading-relaxed text-stone-700 mt-2">{lang === "hi" ? "Bolo ya likho — har jawab ka kanoon + link. Kam bharosa ho to hum khud rok dete hain, human ko bhejte hain." : "Speak or type — every line has Act + link. Low trust → we stop and send to human."}</p>
            <div className="mt-4 flex flex-wrap items-center gap-2 text-xs font-bold">
              {[
                ["No vakil fees", "bg-emerald-50 border-emerald-200 text-emerald-800"],
                ["₹0 offline", "bg-sky-50 border-sky-200 text-sky-800"],
                ["6 bhasha", "bg-amber-50 border-amber-200 text-amber-900"],
              ].map(([label, tone]) => (
                <span key={label} className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border ${tone}`}>
                  <Icon name="check" className="w-3.5 h-3.5" strokeWidth={2.5} />
                  {label}
                </span>
              ))}
            </div>
          </div>

          {/* Emil: stagger examples — 48ms each, not all at once */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {EXAMPLES.map((ex, i) => (
              <button
                key={ex.label}
                onClick={() => { setQuery(ex.q); setJurisdiction(ex.jurisdiction); onSend(ex.q); }}
                className="pressable touch-48 stagger-in text-left rounded-2xl border-2 border-stone-200 bg-white p-4 flex gap-3 items-center hover:border-stone-300"
                style={{ animationDelay: `${i * 48}ms` } as React.CSSProperties}
              >
                <span className={`w-11 h-11 rounded-xl grid place-items-center shrink-0 border ${ex.jurisdiction === "india" ? "bg-saffron/10 border-saffron/30 text-saffron-dark" : "bg-indiaBlue/5 border-indiaBlue/20 text-indiaBlue"}`}>
                  <Icon name={ex.icon} className="w-5 h-5" />
                </span>
                <span className="min-w-0">
                  <span className="block text-sm font-bold leading-tight">{ex.label}</span>
                  <span className="flex items-center gap-1 text-xs text-stone-600 mt-1">
                    <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${ex.jurisdiction === "india" ? "bg-saffron" : "bg-indiaBlue"}`} aria-hidden />
                    {ex.jurisdiction === "india" ? "Bharat" : "World"} · tap karo
                    <Icon name="next" className="w-3 h-3" />
                  </span>
                </span>
              </button>
            ))}
          </div>

          {/* Primary action: VOICE — 48px+ touch, scale 0.97 on press, no all-property transition */}
          <div className="rounded-[20px] bg-white border-2 border-stone-200 shadow-card p-5 stagger-in flex flex-col items-center gap-4" style={{ animationDelay: "160ms" } as React.CSSProperties}>
            <VoiceButton lang={lang} onTranscript={(t) => { setQuery(t); onSend(t); }} />
            <div className="text-xs font-bold text-stone-400 tracking-widest uppercase">— ya —</div>
            <div className="w-full flex gap-3">
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) onSend(); }}
                placeholder={lang === "hi" ? "Yahan likho — jaise bolte ho waise..." : "Type here — like you speak..."}
                rows={2}
                className="flex-1 resize-none rounded-2xl border-2 border-stone-200 bg-stone-50 px-4 py-3 text-[16px] leading-relaxed placeholder:text-stone-400 focus:outline-none focus:border-ink focus:bg-white"
                style={{ transition: "border-color 160ms var(--ease-out), background-color 160ms var(--ease-out)" }}
              />
            </div>
            <div className="w-full flex gap-2">
              <button onClick={() => onSend()} disabled={loading || !query.trim()} className="pressable touch-48 flex-1 py-4 rounded-2xl bg-ink text-white text-[16px] font-extrabold disabled:opacity-40 flex items-center justify-center gap-2">
                {loading ? <><span className="w-4 h-4 rounded-full border-2 border-white/30 border-t-white" style={{ animation: "spin 0.7s linear infinite" }} aria-hidden /> <span>Jaanch rahe…</span></> : <><span>Bhejo →</span><span className="text-xs font-bold px-2 py-1 rounded-full bg-white/15">⌘+Enter</span></>}
              </button>
              <label className="pressable touch-48 inline-flex items-center gap-2 px-3 rounded-2xl border-2 border-stone-200 bg-white text-xs font-bold">
                <input type="checkbox" checked={eli5} onChange={(e) => setEli5(e.target.checked)} className="w-4 h-4" />
                Simple
              </label>
            </div>
            {error && <div className="w-full rounded-xl bg-red-50 border-2 border-red-200 p-3 text-sm text-red-800">{error} — backend `make up`?</div>}
            {res?.free_tier && <span className="text-xs font-bold px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700">FREE — bina paise</span>}
          </div>

          {/* Triage — villager wizard default open, progressive */}
          {showTriage && (
            <FormulationFlow
              onComplete={(ans) => { setFormulation(ans); onSend(query || "Classify my formulation", ans); }}
            />
          )}
          <button onClick={() => setShowTriage((v) => !v)} className="pressable text-xs font-bold px-3 py-2 rounded-full bg-white border-2 border-stone-200 mx-auto block">
            {showTriage ? "3Q band karo −" : "3Q triage kholo + (3 tap me faisla)"}
          </button>

          {/* Split view */}
          {res?.firewall?.mixed_query && <SplitViewTrigger query={query} lang={lang} />}

          {/* Answer — villager: 18px body, icon posture, never light gray */}
          {res && (
            <div className="rounded-[20px] border-2 bg-white shadow-card overflow-hidden stagger-in" style={{ borderColor: jurisdiction === "india" ? "#FF9933" : "#0B2239" }}>
              <div className={`px-4 py-3 flex items-center gap-3 ${jurisdiction === "india" ? "bg-saffron text-white" : "bg-indiaBlue text-white"}`}>
                <span className="inline-flex items-center gap-2 text-sm font-extrabold tracking-tight">
                  <Icon name={res.jurisdiction === "india" ? "india" : "world"} className="w-4 h-4" />
                  {res.jurisdiction === "india" ? "Bharat ka jawab" : "World ka jawab"}
                </span>
                <span className="ml-auto"><ConfidenceBadge score={res.confidence.score} abstain={res.confidence.abstain} /></span>
              </div>
              <div className="p-5">
                {res.firewall && res.firewall.status !== "clean" && (
                  <div className="mb-3 rounded-xl bg-sky-50 border-2 border-sky-200 p-3 text-sm font-medium text-sky-900 flex gap-2">
                    <Icon name="firewall" className="w-4 h-4 shrink-0 mt-0.5 text-sky-700" />
                    <span>{res.firewall.message}</span>
                  </div>
                )}
                <div className="text-[17px] leading-7 text-ink"><AnswerText>{res.answer}</AnswerText></div>
                {res.answer_simple && (
                  <div className="mt-4 rounded-2xl bg-amber-50 border-2 border-amber-200 p-4 stagger-in" style={{ animationDelay: "80ms" } as React.CSSProperties}>
                    <div className="text-xs font-extrabold tracking-widest uppercase text-amber-900 flex items-center gap-2">
                      <Icon name="simple" className="w-3.5 h-3.5" />
                      Simple me, koi bhi samjhe
                    </div>
                    <div className="text-[15px] leading-7 mt-2 text-amber-950"><AnswerText>{res.answer_simple}</AnswerText></div>
                  </div>
                )}
                <div className="mt-4"><ConfidenceBar score={res.confidence.score} /></div>
                <p className="mt-2 text-sm text-stone-700 leading-relaxed">{res.confidence.rationale}</p>
                {res.formulation_result && <div className="mt-4"><PostureTable table={res.formulation_result.posture_table} nextSteps={res.formulation_result.next_steps} category={res.formulation_result.category} /></div>}
                <div className="mt-4 flex flex-wrap gap-2 text-xs font-mono">
                  <span className="px-3 py-1.5 rounded-full bg-stone-900 text-white">corpus {res.corpus_version}</span>
                  <span className="px-3 py-1.5 rounded-full bg-stone-100 border border-stone-200 text-stone-700">{res.disclaimer.slice(0, 44)}…</span>
                </div>
                <div className="mt-4 flex flex-col sm:flex-row gap-2">
                  <div className="flex-1"><EscalateButton sessionId={sessionId} query={query} jurisdiction={jurisdiction} citations={res.citations} /></div>
                  <ExportButton answer={res.answer} citations={res.citations} jurisdiction={jurisdiction} corpusVersion={res.corpus_version} />
                </div>
                {res.escalate_suggested && (
                  <p className="mt-3 text-sm font-medium bg-amber-50 border-2 border-amber-200 rounded-xl p-3 flex gap-2 text-amber-900">
                    <Icon name="warn" className="w-4 h-4 shrink-0 mt-0.5" />
                    <span>Bharosa kam, human ko bhejna behtar. Sab trace DPDP me safe.</span>
                  </p>
                )}
              </div>
            </div>
          )}

          {!res && !loading && (
            <div className="rounded-2xl border-2 border-dashed border-stone-300 bg-white p-5 stagger-in">
              <div className="w-10 h-10 rounded-xl bg-ink text-white grid place-items-center font-bold">i</div>
              <div className="text-sm font-bold mt-2">ChatGPT se alag kya?</div>
              <div className="mt-2 grid gap-2 text-sm">
                {([
                  ["firewall", "Bharat vs World alag", "Mix nahi karte, rang alag."],
                  ["cite", "Har line ka kaagaz", "Jhootha Sec number nahi."],
                  ["check", "₹0 kharcha", "Bina key, offline chalega."],
                ] as [IconName, string, string][]).map(([icon, t, d]) => (
                  <div key={t} className="flex items-start gap-3 p-3 rounded-xl bg-stone-50 border border-stone-200">
                    <Icon name={icon} className="w-4 h-4 shrink-0 mt-0.5 text-stone-500" />
                    <span className="font-bold">{t}</span>
                    <span className="text-stone-600 ml-auto text-right">{d}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {!res && !loading && (
            <div className="space-y-3 stagger-in" style={{ animationDelay: "80ms" } as React.CSSProperties}>
              <h2 className="h-display text-sm font-bold text-stone-600 uppercase tracking-widest">Kaise kaam karta hai</h2>
              <HowItWorks />
              <ComparisonTable />
            </div>
          )}
        </div>

        {/* RIGHT: citations + pipeline — villager: big verify, not tiny mono */}
        <div className="space-y-4" ref={scroller}>
          <div className="rounded-[20px] bg-white border-2 border-stone-200 shadow-card p-4">
            <CitationPane citations={res?.citations ?? []} corpusVersion={res?.corpus_version ?? corpus?.corpus_version} />
          </div>
          <div className="rounded-2xl bg-stone-900 text-stone-100 p-4">
            <div className="text-xs font-extrabold tracking-widest uppercase text-stone-400">Free pipeline — ₹0</div>
            <div className="mt-3 font-mono text-xs leading-relaxed space-y-1">
              <div className="text-stone-100">bolo → classifier → 3Q → 5× retriever (MiniLM) → rerank → firewall → offline jawaab</div>
              <div className="text-stone-400">loader → chunker 800/120 § → pgvector</div>
            </div>
          </div>
        </div>
      </main>

      <footer className="mx-auto max-w-[1280px] px-6 py-6 text-center text-xs font-medium text-stone-500">
        IP-SAKTI Sahayak · Information only — vakil nahi. Link check karke file karo. · DPDP 365 din · Paid DB bina permission band.
      </footer>
    </div>
  );
}
