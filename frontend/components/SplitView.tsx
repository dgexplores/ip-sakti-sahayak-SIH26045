"use client";
import { useState } from "react";
import { chat, type Jurisdiction, type ChatResponse } from "@/lib/api";
import { ConfidenceBadge, ConfidenceBar } from "@/components/ConfidenceBadge";
import { CitationPane } from "@/components/CitationPane";

export function SplitViewTrigger({ query, lang }: { query: string; lang: string }) {
  const [loading, setLoading] = useState(false);
  const [india, setIndia] = useState<ChatResponse | null>(null);
  const [intl, setIntl] = useState<ChatResponse | null>(null);

  async function run() {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const [a, b] = await Promise.all([
        chat(query, "india", lang, undefined, undefined, true),
        chat(query, "international", lang, undefined, undefined, true),
      ]);
      setIndia(a); setIntl(b);
    } catch {}
    setLoading(false);
  }

  return (
    <div className="rounded-2xl border border-sky-200 bg-sky-50 p-4">
      <div className="flex items-center gap-3">
        <div className="text-sm font-bold text-sky-900">🛡️ Jurisdiction split — see both sides</div>
        <button onClick={run} disabled={loading || !query.trim()} className="ml-auto text-xs font-semibold px-3 py-2 rounded-full bg-sky-600 text-white hover:bg-sky-700 disabled:opacity-50">
          {loading ? "Fetching both…" : "Show 🇮🇳 vs 🌐 side-by-side →"}
        </button>
      </div>
      <p className="text-xs text-sky-700 mt-1">PS requires “visibly separate answer-sets, never conflated” — this proves firewall.</p>
      {(india || intl) && (
        <div className="mt-4 grid grid-cols-1 lg:grid-cols-2 gap-4">
          {[
            { label: "🇮🇳 INDIA", color: "border-saffron", data: india },
            { label: "🌐 INTERNATIONAL", color: "border-indiaBlue", data: intl },
          ].map((col) => (
            <div key={col.label} className={`rounded-2xl border-2 bg-white overflow-hidden ${col.color}`}>
              <div className="px-3 py-2 text-xs font-bold tracking-widest uppercase flex items-center gap-2">
                {col.label} {col.data && <span className="ml-auto"><ConfidenceBadge score={col.data.confidence.score} abstain={col.data.confidence.abstain} /></span>}
              </div>
              {col.data ? (
                <div className="p-4">
                  <div className="text-sm leading-relaxed whitespace-pre-wrap">{col.data.answer.slice(0, 900)}{col.data.answer.length>900?"…":""}</div>
                  <div className="mt-3"><ConfidenceBar score={col.data.confidence.score} /></div>
                  <div className="mt-3 text-xs"><CitationPane citations={col.data.citations.slice(0,2)} corpusVersion={col.data.corpus_version} /></div>
                </div>
              ) : (
                <div className="p-8 text-center text-xs text-stone-400">No data — hit button</div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
