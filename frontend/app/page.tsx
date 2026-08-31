"use client";
import { useEffect, useRef, useState } from "react";
import { JurisdictionToggle } from "@/components/JurisdictionToggle";
import { ConfidenceBadge, ConfidenceBar } from "@/components/ConfidenceBadge";
import { CitationPane } from "@/components/CitationPane";
import { FormulationFlow, PostureTable } from "@/components/FormulationFlow";
import { EscalateButton } from "@/components/EscalateButton";
import { ExportButton } from "@/components/ExportButton";
import { VoiceButton } from "@/components/VoiceButton";
import { SplitViewTrigger } from "@/components/SplitView";
import { Icon, type IconName } from "@/components/Icon";
import { AnswerText } from "@/components/AnswerText";
import { LANGS, EXAMPLES, t } from "@/lib/i18n";
import { chat, getCorpusVersion, type ChatResponse, type FormulationAnswer, type Jurisdiction } from "@/lib/api";

export default function Page() {
  const [jurisdiction, setJurisdiction] = useState<Jurisdiction>("india");
  const [query, setQuery] = useState("");
  const [lang, setLang] = useState("hi");
  const [eli5, setEli5] = useState(true);
  const [loading, setLoading] = useState(false);
  const [res, setRes] = useState<ChatResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [corpus, setCorpus] = useState<{ corpus_version: string; document_count: number } | null>(null);
  const [sessionId] = useState(() => `sess_${Math.random().toString(36).slice(2, 10)}`);
  // Closed by default. It used to open on arrival, so a first-time visitor met
  // three questions and six category buttons before the thing they came to do.
  const [showTriage, setShowTriage] = useState(false);
  const [formulation, setFormulation] = useState<FormulationAnswer | null>(null);
  const [corpusError, setCorpusError] = useState(false);
  const answerRef = useRef<HTMLDivElement>(null);

  const s = t(lang);

  useEffect(() => {
    getCorpusVersion().then(setCorpus).catch(() => setCorpusError(true));
  }, []);

  async function onSend(q?: string, form?: FormulationAnswer) {
    const text = (q ?? query).trim();
    if (!text) return;
    setLoading(true);
    setError(null);
    try {
      const r = await chat(text, jurisdiction, lang, form ?? formulation ?? undefined, sessionId, eli5);
      setRes(r);
      setShowTriage(false);
      setTimeout(() => answerRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 120);
    } catch (e) {
      setError(e instanceof Error ? e.message : s.errorHint);
    } finally {
      setLoading(false);
    }
  }

  const steps = [s.step1, s.step2, s.step3];

  return (
    <div className="min-h-screen bg-[#FFFBF5]">
      <header className="sticky top-0 z-30 bg-white/95 backdrop-blur border-b border-stone-200">
        <div className="mx-auto max-w-[1180px] px-4 sm:px-6 py-3 flex flex-wrap items-center gap-x-3 gap-y-2">
          <div className="w-9 h-9 rounded-xl bg-ink text-white grid place-items-center font-extrabold text-xs shrink-0">IP</div>
          <div className="min-w-0">
            <div className="h-display text-[17px] font-extrabold leading-none">IP-SAKTI Sahayak</div>
            <div className="text-xs text-stone-600">{s.tagline}</div>
          </div>

          <div className="ml-auto order-3 sm:order-none w-full sm:w-auto flex items-center justify-center gap-1 p-1 rounded-full bg-stone-100 border border-stone-200">
            {LANGS.map((l) => (
              <button
                key={l.id}
                onClick={() => setLang(l.id)}
                aria-pressed={lang === l.id}
                title={l.english}
                className={`px-3 py-1.5 rounded-full text-sm font-bold transition-colors ${
                  lang === l.id ? "bg-ink text-white" : "text-stone-700 hover:bg-white"
                }`}
              >
                {l.label}
              </button>
            ))}
          </div>
        </div>

        <div className="mx-auto max-w-[1180px] px-4 sm:px-6 pb-3 flex flex-wrap items-center gap-3">
          <JurisdictionToggle value={jurisdiction} onChange={setJurisdiction} lang={lang} />
          <span
            className={`ml-auto text-[11px] font-mono px-2 py-1 rounded-full border ${
              corpusError ? "bg-red-50 border-red-200 text-red-800" : "bg-stone-50 border-stone-200 text-stone-600"
            }`}
          >
            {corpus ? `${corpus.document_count} docs · ${corpus.corpus_version}` : corpusError ? s.backendOffline : s.loading}
          </span>
        </div>
        <div className="h-1 w-full flex" aria-hidden>
          <div className={`flex-1 ${jurisdiction === "india" ? "bg-saffron" : "bg-stone-200"}`} style={{ transition: "background-color 180ms var(--ease-out)" }} />
          <div className={`flex-1 ${jurisdiction === "international" ? "bg-indiaBlue" : "bg-stone-200"}`} style={{ transition: "background-color 180ms var(--ease-out)" }} />
        </div>
      </header>

      <main className="mx-auto max-w-[1180px] px-4 sm:px-6 py-6 grid grid-cols-1 lg:grid-cols-[1.15fr_0.85fr] gap-6 items-start">
        <div className="space-y-5 min-w-0">
          {!res && (
            <div className="stagger-in">
              <h1 className="h-display text-[26px] sm:text-[32px] font-extrabold leading-[1.15] tracking-tight">
                {s.headline}{" "}
                <span className={jurisdiction === "india" ? "text-saffron-dark" : "text-indiaBlue"}>{s.headlineAccent}</span>
              </h1>
              <p className="text-[15px] leading-relaxed text-stone-700 mt-3 max-w-[56ch]">{s.subhead}</p>

              <ol className="mt-5 grid gap-2 sm:grid-cols-3">
                {steps.map((label, i) => (
                  <li key={label} className="flex items-center gap-2.5 text-sm">
                    <span className="w-6 h-6 rounded-full bg-ink text-white grid place-items-center text-xs font-bold shrink-0">{i + 1}</span>
                    <span className="text-stone-700 leading-snug">{label}</span>
                  </li>
                ))}
              </ol>
            </div>
          )}

          {/* The one thing to do on this page. */}
          <section className="rounded-[20px] bg-white border-2 border-stone-200 shadow-card overflow-hidden stagger-in" style={{ animationDelay: "60ms" }}>
            <div className="px-5 pt-5 pb-4">
              <h2 className="h-display text-lg font-extrabold leading-tight">{s.askTitle}</h2>
              <p className="text-sm text-stone-600 mt-1">{s.askHint}</p>

              <div className="mt-4 flex flex-col items-center gap-3">
                <VoiceButton lang={lang} onTranscript={(v) => { setQuery(v); onSend(v); }} />
                <span className="text-xs font-bold uppercase tracking-widest text-stone-400">{s.or}</span>
                <textarea
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) onSend(); }}
                  placeholder={s.placeholder}
                  rows={3}
                  aria-label={s.askTitle}
                  className="w-full resize-none rounded-2xl border-2 border-stone-200 bg-stone-50 px-4 py-3 text-[16px] leading-relaxed placeholder:text-stone-500 focus:outline-none focus:border-ink focus:bg-white"
                  style={{ transition: "border-color 160ms var(--ease-out), background-color 160ms var(--ease-out)" }}
                />
              </div>

              <button
                onClick={() => onSend()}
                disabled={loading || !query.trim()}
                className="pressable touch-48 mt-3 w-full py-4 rounded-2xl bg-ink text-white text-[16px] font-extrabold disabled:opacity-40 inline-flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <span className="w-4 h-4 rounded-full border-2 border-white/30 border-t-white" style={{ animation: "spin 0.7s linear infinite" }} aria-hidden />
                    {s.sending}
                  </>
                ) : (
                  <>
                    {s.send}
                    <Icon name="next" className="w-4 h-4" />
                  </>
                )}
              </button>

              <label className="mt-3 flex items-center gap-2.5 text-sm cursor-pointer">
                <input type="checkbox" checked={eli5} onChange={(e) => setEli5(e.target.checked)} className="w-4 h-4 accent-ink" />
                <span className="font-bold">{s.simpleMode}</span>
                <span className="text-stone-600">{s.simpleModeHint}</span>
              </label>

              {error && (
                <div className="mt-3 rounded-xl bg-red-50 border-2 border-red-200 p-3 text-sm text-red-900 flex gap-2">
                  <Icon name="warn" className="w-4 h-4 shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}
            </div>

            <div className="border-t border-stone-200 bg-stone-50/70 px-5 py-4">
              <div className="text-xs font-bold uppercase tracking-widest text-stone-500">{s.examplesLabel}</div>
              <div className="mt-2.5 flex flex-wrap gap-2">
                {EXAMPLES.map((ex) => (
                  <button
                    key={ex.q}
                    onClick={() => { setQuery(ex.q); setJurisdiction(ex.jurisdiction as Jurisdiction); onSend(ex.q); }}
                    className="pressable inline-flex items-center gap-2 pl-2.5 pr-3.5 py-2 rounded-full bg-white border border-stone-300 text-sm font-semibold text-stone-800 hover:border-ink/40"
                  >
                    <span className={`w-6 h-6 rounded-full grid place-items-center shrink-0 ${ex.jurisdiction === "india" ? "bg-saffron/15 text-saffron-dark" : "bg-indiaBlue/10 text-indiaBlue"}`}>
                      <Icon name={ex.icon as IconName} className="w-3.5 h-3.5" />
                    </span>
                    {ex.label[lang as keyof typeof ex.label] ?? ex.label.en}
                  </button>
                ))}
              </div>
            </div>
          </section>

          {/* Offered, not imposed. */}
          {!showTriage ? (
            <button
              onClick={() => setShowTriage(true)}
              className="pressable w-full text-left rounded-2xl border-2 border-dashed border-stone-300 bg-white p-4 flex items-center gap-3 hover:border-stone-400 stagger-in"
              style={{ animationDelay: "120ms" }}
            >
              <span className="w-10 h-10 rounded-xl bg-amber-50 border border-amber-200 grid place-items-center text-amber-700 shrink-0">
                <Icon name="check" className="w-4 h-4" />
              </span>
              <span className="min-w-0">
                <span className="block text-sm font-bold">{s.notSure}</span>
                <span className="block text-sm text-stone-600 mt-0.5">{s.notSureHint}</span>
              </span>
              <span className="ml-auto text-sm font-bold text-ink whitespace-nowrap hidden sm:flex items-center gap-1">
                {s.openTriage}
                <Icon name="next" className="w-3.5 h-3.5" />
              </span>
            </button>
          ) : (
            <div className="stagger-in">
              <FormulationFlow
                lang={lang}
                onComplete={(ans) => { setFormulation(ans); onSend(query || "Classify my Ayurvedic formulation", ans); }}
              />
              <button onClick={() => setShowTriage(false)} className="pressable mt-2 mx-auto block text-sm font-bold text-stone-600 px-4 py-2 rounded-full hover:bg-stone-100">
                {s.closeTriage}
              </button>
            </div>
          )}

          {res?.firewall?.mixed_query && <SplitViewTrigger query={query} lang={lang} />}

          {res && (
            <div ref={answerRef} className="rounded-[20px] border-2 bg-white shadow-card overflow-hidden stagger-in" style={{ borderColor: jurisdiction === "india" ? "#FF9933" : "#0B2239" }}>
              <div className={`px-5 py-3 flex items-center gap-3 ${jurisdiction === "india" ? "bg-saffron text-white" : "bg-indiaBlue text-white"}`}>
                <span className="inline-flex items-center gap-2 text-sm font-extrabold">
                  <Icon name={res.jurisdiction === "india" ? "india" : "world"} className="w-4 h-4" />
                  {res.jurisdiction === "india" ? s.answerIndia : s.answerWorld}
                </span>
                <span className="ml-auto"><ConfidenceBadge score={res.confidence.score} abstain={res.confidence.abstain} label={s.confidence} /></span>
              </div>

              <div className="p-5">
                {res.firewall && res.firewall.status !== "clean" && (
                  <div className="mb-4 rounded-xl bg-sky-50 border-2 border-sky-200 p-3 text-sm font-medium text-sky-900 flex gap-2">
                    <Icon name="firewall" className="w-4 h-4 shrink-0 mt-0.5 text-sky-700" />
                    <span>{res.firewall.message}</span>
                  </div>
                )}

                <div className="text-[17px] leading-7 text-ink"><AnswerText>{res.answer}</AnswerText></div>

                {res.answer_simple && (
                  <div className="mt-5 rounded-2xl bg-amber-50 border-2 border-amber-200 p-4">
                    <div className="text-xs font-extrabold tracking-widest uppercase text-amber-900 flex items-center gap-2">
                      <Icon name="simple" className="w-3.5 h-3.5" />
                      {s.simpleHeading}
                    </div>
                    <div className="text-[15px] leading-7 mt-2 text-amber-950"><AnswerText>{res.answer_simple}</AnswerText></div>
                  </div>
                )}

                {res.formulation_result && (
                  <div className="mt-5">
                    <PostureTable table={res.formulation_result.posture_table} nextSteps={res.formulation_result.next_steps} category={res.formulation_result.category} />
                  </div>
                )}

                <div className="mt-5">
                  <ConfidenceBar score={res.confidence.score} />
                  <p className="mt-2 text-sm text-stone-700 leading-relaxed">{res.confidence.rationale}</p>
                </div>

                {res.escalate_suggested && (
                  <p className="mt-4 text-sm font-medium bg-amber-50 border-2 border-amber-200 rounded-xl p-3 flex gap-2 text-amber-900">
                    <Icon name="warn" className="w-4 h-4 shrink-0 mt-0.5" />
                    <span>{s.lowTrust}</span>
                  </p>
                )}

                <div className="mt-5 pt-4 border-t border-stone-200 flex flex-col sm:flex-row gap-2">
                  <div className="flex-1"><EscalateButton sessionId={sessionId} query={query} jurisdiction={jurisdiction} citations={res.citations} lang={lang} /></div>
                  <ExportButton answer={res.answer} citations={res.citations} jurisdiction={jurisdiction} corpusVersion={res.corpus_version} lang={lang} />
                </div>

                <p className="mt-4 text-xs text-stone-600 leading-relaxed">{s.disclaimer}</p>
              </div>
            </div>
          )}
        </div>

        <aside className="space-y-4 lg:sticky lg:top-[132px] min-w-0">
          <div className="rounded-[20px] bg-white border-2 border-stone-200 shadow-card p-4">
            <CitationPane citations={res?.citations ?? []} corpusVersion={res?.corpus_version ?? corpus?.corpus_version} lang={lang} />
          </div>

          <div className="flex flex-wrap gap-2 text-xs font-bold">
            {[s.noFees, s.free, s.offline, s.languages].map((label) => (
              <span key={label} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-900">
                <Icon name="check" className="w-3.5 h-3.5" strokeWidth={2.5} />
                {label}
              </span>
            ))}
          </div>
        </aside>
      </main>
    </div>
  );
}
