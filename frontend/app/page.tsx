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
import { FluidButton } from "@/components/ui/FluidButtons";
import { Toolbar } from "@/components/ui/Materials";
import { GlossaryBar } from "@/components/GlossaryTooltip";
import { LANGS, EXAMPLES, t, readStoredLang, storeLang } from "@/lib/i18n";
import { chat, getCorpusVersion, ApiError, type ChatResponse, type FormulationAnswer, type Jurisdiction } from "@/lib/api";

/** Session id for the audit trail.
 *
 * `Math.random()` is not a source of uniqueness — it is seeded per engine and
 * yields roughly 41 bits here. Two visitors whose ids collide share an audit
 * trail, which is the one place a session id has to be dependable. `randomUUID`
 * is available in every browser this app targets and in Node 19+.
 */
function newSessionId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return `sess_${crypto.randomUUID().replace(/-/g, "").slice(0, 16)}`;
  }
  if (typeof crypto !== "undefined" && typeof crypto.getRandomValues === "function") {
    const bytes = crypto.getRandomValues(new Uint8Array(8));
    return `sess_${Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("")}`;
  }
  // Last resort for a non-secure context. Weaker, but at least documented.
  return `sess_${Date.now().toString(36)}${Math.random().toString(36).slice(2, 10)}`;
}

export default function Page() {
  const [jurisdiction, setJurisdiction] = useState<Jurisdiction>("india");
  const [query, setQuery] = useState("");
  const [lang, setLang] = useState("hi");
  const [eli5, setEli5] = useState(true);
  const [loading, setLoading] = useState(false);
  const [res, setRes] = useState<ChatResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [corpus, setCorpus] = useState<{ corpus_version: string; document_count: number } | null>(null);
  const [sessionId] = useState(newSessionId);
  // Closed by default. It used to open on arrival, so a first-time visitor met
  // three questions and six category buttons before the thing they came to do.
  const [showTriage, setShowTriage] = useState(false);
  const [formulation, setFormulation] = useState<FormulationAnswer | null>(null);
  const [corpusError, setCorpusError] = useState(false);
  const [showLegalDetail, setShowLegalDetail] = useState(false);
  const sendingRef = useRef(false);
  const answerRef = useRef<HTMLDivElement>(null);

  const s = t(lang);

  useEffect(() => {
    getCorpusVersion().then(setCorpus).catch(() => setCorpusError(true));
  }, []);

  // Read after mount, not during render: the server has no storage, so
  // seeding state from it would break hydration.
  useEffect(() => {
    const stored = readStoredLang();
    if (stored) setLang(stored);
  }, []);

  function chooseLang(id: string) {
    setLang(id);
    storeLang(id);
  }

  async function onSend(q?: string, form?: FormulationAnswer) {
    const text = (q ?? query).trim();
    if (!text || sendingRef.current) return;
    sendingRef.current = true;
    setLoading(true);
    setError(null);
    try {
      const r = await chat(text, jurisdiction, lang, form ?? formulation ?? undefined, sessionId, eli5);
      setRes(r);
      setShowLegalDetail(!r.answer_simple);
      setShowTriage(false);
      setTimeout(() => answerRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 120);
    } catch (e) {
      // A transport failure gets the localised hint; a rejection from the
      // backend carries its own message, which is English (the corpus and the
      // API are English) and is shown as-is rather than swallowed.
      setError(
        e instanceof ApiError && e.code === "timeout"
          ? s.requestTimedOut
          : e instanceof ApiError && e.code === "network"
            ? s.errorHint
            : e instanceof Error
              ? e.message
              : s.errorHint
      );
    } finally {
      sendingRef.current = false;
      setLoading(false);
    }
  }

  const steps = [s.step1, s.step2, s.step3];
  const activeStage = res ? 3 : 1;

  return (
    <div className="min-h-screen overflow-x-hidden bg-[#f5f2ea] text-ink selection:bg-saffron/30">
      <Toolbar className="border-b border-[#ddd7c9] bg-[#fbfaf6]">
        <div className="mx-auto flex max-w-[1240px] flex-wrap items-center gap-3 px-4 py-3 sm:flex-nowrap sm:px-6">
          <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-indiaBlue text-xs font-extrabold tracking-tight text-white">IP</div>
          <div className="min-w-0">
            <div className="h-display text-[18px] font-extrabold leading-none">IP-SAKTI Sahayak</div>
            <div className="mt-1 text-xs text-stone-600">{s.tagline}</div>
          </div>
          <div className="order-3 flex w-full items-center justify-start gap-3 sm:order-none sm:ml-auto sm:w-auto sm:justify-end">
            <span className={`hidden text-[11px] font-mono tabular-nums sm:inline ${corpusError ? "text-red-800" : "text-stone-500"}`}>
              {corpus ? `${corpus.document_count} ${s.proofTitle.toLowerCase()}` : corpusError ? s.backendOffline : s.loading}
            </span>
            <div className="flex items-center gap-0.5 rounded-lg border border-[#ddd7c9] bg-white p-1">
              {LANGS.map((l) => (
                <button
                  key={l.id}
                  onClick={() => chooseLang(l.id)}
                  aria-pressed={lang === l.id}
                  title={l.english}
                  className={`rounded-md px-2.5 py-1.5 text-sm font-bold transition-colors ${lang === l.id ? "bg-indiaBlue text-white" : "text-stone-700 hover:bg-stone-100"}`}
                >
                  {l.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </Toolbar>

      <main id="main" className="mx-auto max-w-[1240px] px-4 pb-10 pt-8 sm:px-6 sm:pt-12">
        <div className="grid items-start gap-8 lg:grid-cols-[minmax(0,1fr)_320px]">
          <div className="min-w-0">
            {!res && (
              <section className="stagger-in max-w-[780px]">
                <h1 className="h-display text-balance text-[34px] font-extrabold leading-[1.04] tracking-[-0.03em] text-ink sm:text-[52px]">
                  {s.headline} <span className="text-saffron-dark">{s.headlineAccent}</span>
                </h1>
                <p className="mt-5 max-w-[63ch] text-[16px] leading-7 text-stone-700 sm:text-[17px]">{s.subhead}</p>
              </section>
            )}

            <ol className={`my-8 grid max-w-[760px] grid-cols-1 gap-3 border-y border-[#ddd7c9] py-4 sm:grid-cols-3 sm:gap-0 ${res ? "mt-0" : ""}`} aria-label="How IP-SAKTI works">
              {steps.map((label, i) => {
                const current = i + 1 === activeStage;
                const complete = i + 1 < activeStage;
                return (
                  <li key={label} className="flex min-w-0 items-center gap-2 pr-3 text-sm">
                    <span className={`grid h-7 w-7 shrink-0 place-items-center rounded-full text-xs font-extrabold ${current ? "bg-saffron text-white" : complete ? "bg-indiaBlue text-white" : "bg-[#e7e2d8] text-stone-600"}`}>{complete ? <Icon name="check" className="w-3.5 h-3.5" strokeWidth={3} /> : i + 1}</span>
                    <span className={`min-w-0 leading-snug ${current ? "font-bold text-ink" : "text-stone-600"}`}>{label}</span>
                  </li>
                );
              })}
            </ol>

            <section className="overflow-hidden rounded-2xl border border-[#d7d0c2] bg-white shadow-[0_12px_30px_rgba(48,42,30,0.08)]">
              <div className="border-b border-[#e5dfd3] bg-[#fffdf9] px-5 py-4 sm:px-6">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <h2 className="h-display text-[22px] font-extrabold leading-tight">{s.askTitle}</h2>
                    <p className="mt-1 text-sm leading-relaxed text-stone-600">{s.askHint}</p>
                  </div>
                  <JurisdictionToggle value={jurisdiction} onChange={setJurisdiction} lang={lang} />
                </div>
              </div>

              <div className="p-5 sm:p-6">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-stretch">
                  <textarea
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={(e) => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) onSend(); }}
                    placeholder={s.placeholder}
                    rows={4}
                    aria-label={s.askTitle}
                    className="min-h-[132px] w-full flex-1 resize-none rounded-xl border border-[#cfc7b9] bg-[#fcfbf8] px-4 py-3 text-[16px] leading-7 placeholder:text-stone-500 focus:border-indiaBlue focus:bg-white focus:outline-none"
                  />
                  <div className="flex shrink-0 items-center justify-center border-t border-[#e5dfd3] pt-4 sm:w-[152px] sm:border-l sm:border-t-0 sm:pl-4 sm:pt-0">
                    <VoiceButton lang={lang} onTranscript={(v) => { setQuery(v); onSend(v); }} />
                  </div>
                </div>

                <div className="mt-4 flex flex-col gap-3 border-t border-[#e5dfd3] pt-4 sm:flex-row sm:items-center">
                  <label className="flex cursor-pointer items-start gap-2.5 text-sm sm:flex-1">
                    <input type="checkbox" checked={eli5} onChange={(e) => setEli5(e.target.checked)} className="mt-0.5 h-4 w-4 accent-indiaBlue" />
                    <span><span className="font-bold text-ink">{s.simpleMode}</span><span className="ml-1.5 text-stone-600">{s.simpleModeHint}</span></span>
                  </label>
                  <FluidButton onClick={() => onSend()} disabled={loading || !query.trim()} className="sm:min-w-[220px]" size="lg" loading={loading} loadingText={s.sending} icon={<Icon name="next" className="w-4 h-4" />}>
                    {s.send}
                  </FluidButton>
                </div>

                {error && (
                  <div className="mt-4 flex gap-3 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-900" role="alert">
                    <Icon name="warn" className="mt-0.5 h-4 w-4 shrink-0" />
                    <div className="min-w-0 flex-1"><p>{error}</p><button type="button" onClick={() => onSend()} className="mt-2 font-bold underline underline-offset-2 hover:no-underline">{s.errRetry}</button></div>
                  </div>
                )}

                <div className="mt-5">
                  <div className="text-xs font-bold tracking-[0.08em] text-stone-500">{s.examplesLabel}</div>
                  <div className="mt-2.5 flex flex-wrap gap-x-4 gap-y-2">
                    {EXAMPLES.map((ex) => (
                      <button key={ex.q} type="button" onClick={() => { setQuery(ex.q); setJurisdiction(ex.jurisdiction as Jurisdiction); onSend(ex.q); }} className="inline-flex items-center gap-1.5 text-sm font-bold text-indiaBlue underline decoration-indiaBlue/30 underline-offset-4 hover:decoration-indiaBlue">
                        <Icon name={ex.icon as IconName} className="h-3.5 w-3.5" />
                        {ex.label[lang as keyof typeof ex.label] ?? ex.label.en}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </section>

          {/* Offered, not imposed. */}
          {!showTriage ? (
            <button
              onClick={() => setShowTriage(true)}
              className="pressable mt-5 flex w-full items-center gap-3 border-y border-[#ddd7c9] py-5 text-left hover:text-indiaBlue stagger-in"
              style={{ animationDelay: "120ms" }}
            >
              <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-saffron-light text-saffron-dark">
                <Icon name="check" className="w-4 h-4" />
              </span>
              <span className="min-w-0">
                <span className="block text-sm font-bold">{s.notSure}</span>
                <span className="block text-sm text-stone-600 mt-0.5">{s.notSureHint}</span>
              </span>
              <span className="ml-auto hidden whitespace-nowrap text-sm font-bold text-indiaBlue sm:flex items-center gap-1">
                {s.openTriage}
                <Icon name="next" className="w-3.5 h-3.5" />
              </span>
            </button>
          ) : (
            <div className="mt-5 stagger-in">
              <FormulationFlow
                lang={lang}
                onComplete={(ans) => { setFormulation(ans); onSend(query || "Classify my Ayurvedic formulation", ans); }}
              />
              <FluidButton variant="ghost" size="sm" onClick={() => setShowTriage(false)} className="mt-2 mx-auto">
                {s.closeTriage}
              </FluidButton>
            </div>
          )}

          {res?.firewall?.mixed_query && <SplitViewTrigger query={query} lang={lang} />}

          {res && (
            <section ref={answerRef} className="mt-8 overflow-hidden rounded-2xl border border-[#d7d0c2] bg-white shadow-[0_12px_30px_rgba(48,42,30,0.08)] stagger-in">
              <div className={`flex items-center gap-3 px-5 py-3 ${jurisdiction === "india" ? "bg-indiaBlue text-white" : "bg-[#314a65] text-white"}`}>
                <span className="inline-flex items-center gap-2 text-sm font-extrabold">
                  <Icon name={res.jurisdiction === "india" ? "india" : "world"} className="w-4 h-4" />
                  {res.jurisdiction === "india" ? s.answerIndia : s.answerWorld}
                </span>
                <span className="ml-auto"><ConfidenceBadge score={res.confidence.score} abstain={res.confidence.abstain} label={s.confidence} /></span>
              </div>

              <div className="p-5 sm:p-6">
                {res.firewall && res.firewall.status !== "clean" && (
                  <div className="mb-5 flex gap-2 border-b border-sky-200 bg-sky-50 px-3 py-3 text-sm font-medium text-sky-900">
                    <Icon name="firewall" className="w-4 h-4 shrink-0 mt-0.5 text-sky-700" />
                    <span>{res.firewall.message}</span>
                  </div>
                )}

                {res.answer_simple && (
                  <div className="border-b-2 border-saffron bg-saffron-light px-4 py-4">
                    <div className="flex items-center gap-2 text-xs font-extrabold tracking-[0.08em] text-amber-900">
                      <Icon name="simple" className="w-3.5 h-3.5" />
                      {s.simpleHeading}
                    </div>
                    <div className="text-[15px] leading-7 mt-2 text-amber-950"><AnswerText lang={lang}>{res.answer_simple}</AnswerText></div>
                  </div>
                )}

                <div className="mt-5 overflow-hidden border-y border-[#e5dfd3] bg-[#fffdf9]">
                  <button
                    type="button"
                    onClick={() => setShowLegalDetail((value) => !value)}
                    aria-expanded={showLegalDetail}
                    className="pressable flex w-full items-center gap-3 px-4 py-4 text-left hover:bg-[#f7f4ed]"
                  >
                    <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-[#e9e4da] text-indiaBlue">
                      <Icon name="cite" className="w-4 h-4" />
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="block text-sm font-extrabold">{s.legalDetailTitle}</span>
                      <span className="block mt-0.5 text-sm text-stone-600">{s.legalDetailHint}</span>
                    </span>
                    <Icon name="next" className={`w-4 h-4 shrink-0 transition-transform ${showLegalDetail ? "rotate-90" : ""}`} />
                  </button>
                  {showLegalDetail && (
                    <div className="border-t border-[#e5dfd3] px-4 py-5 text-[16px] leading-7 text-ink">
                      <AnswerText lang={lang}>{res.answer}</AnswerText>
                    </div>
                  )}
                </div>

                {res.formulation_result && (
                  <div className="mt-5">
                    <PostureTable table={res.formulation_result.posture_table} nextSteps={res.formulation_result.next_steps} category={res.formulation_result.category} />
                  </div>
                )}

                <div className="mt-6 border-b border-[#e5dfd3] pb-5">
                  <ConfidenceBar score={res.confidence.score} />
                  <p className="mt-2 text-sm text-stone-700 leading-relaxed">{res.confidence.rationale}</p>
                </div>

                {res.escalate_suggested && (
                  <p className="mt-4 text-sm font-medium bg-amber-50 border-2 border-amber-200 rounded-xl p-3 flex gap-2 text-amber-900">
                    <Icon name="warn" className="w-4 h-4 shrink-0 mt-0.5" />
                    <span>{s.lowTrust}</span>
                  </p>
                )}

                <div className="mt-5 flex flex-col gap-2 sm:flex-row">
                  <div className="flex-1"><EscalateButton sessionId={sessionId} query={query} jurisdiction={jurisdiction} citations={res.citations} lang={lang} /></div>
                  <ExportButton answer={res.answer} citations={res.citations} jurisdiction={jurisdiction} corpusVersion={res.corpus_version} confidence={res.confidence} lang={lang} />
                </div>

                <p className="mt-4 text-xs text-stone-600 leading-relaxed">{s.disclaimer}</p>
              </div>
            </section>
          )}
          </div>

          <aside className="space-y-6 lg:sticky lg:top-[88px]">
            <section className="border-y border-[#d7d0c2] py-5">
              <div className="flex items-center gap-2 text-sm font-extrabold text-indiaBlue"><Icon name="firewall" className="h-4 w-4" />{s.proofTitle}</div>
              <p className="mt-2 text-sm leading-6 text-stone-600">{s.proofHint}</p>
              <div className="mt-4 flex flex-wrap gap-2 text-xs font-bold">
                {[s.noFees, s.free, s.offline, s.languages].map((label) => (
                  <span key={label} className="inline-flex items-center gap-1.5 rounded-md bg-[#e8f2ee] px-2.5 py-1.5 text-emerald-900"><Icon name="check" className="h-3.5 w-3.5" strokeWidth={2.5} />{label}</span>
                ))}
              </div>
            </section>

            {res && (
              <section className="border-b border-[#d7d0c2] pb-6">
                <CitationPane citations={res.citations} corpusVersion={res.corpus_version ?? corpus?.corpus_version} lang={lang} />
              </section>
            )}

            <section>
              <div className="text-xs font-extrabold tracking-[0.08em] text-stone-500">{s.glossaryTitle}</div>
              <div className="mt-3"><GlossaryBar lang={lang} /></div>
            </section>
          </aside>
        </div>
      </main>

      <footer className="mx-auto max-w-[1240px] px-4 pb-8 sm:px-6">
        <div className="flex flex-col items-start gap-2 border-t border-[#d7d0c2] pt-5 text-xs text-stone-600 sm:flex-row sm:items-center">
          <span className="font-bold text-stone-800">IP-SAKTI Sahayak</span>
          <span className="leading-relaxed">{s.footerNote}</span>
          <span className="flex gap-4 font-bold sm:ml-auto">
              <a href="/privacy" className="hover:text-ink underline-offset-2 hover:underline">{s.privacy}</a>
              <a href="/terms" className="hover:text-ink underline-offset-2 hover:underline">{s.terms}</a>
          </span>
        </div>
      </footer>
    </div>
  );
}
