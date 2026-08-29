"use client";
import type { Citation } from "@/lib/api";

export function CitationPane({ citations, corpusVersion }: { citations: Citation[]; corpusVersion?: string }) {
  if (!citations?.length) {
    return (
      <div className="rounded-xl border border-dashed border-stone-300 bg-white p-4 text-sm text-stone-500">
        No citations — answer abstained or corpus not loaded. Try a jurisdiction-specific query (e.g., “Sec 3(p) India” vs “WIPO GRATK Art 3”).
      </div>
    );
  }
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-xs font-semibold tracking-widest text-stone-500 uppercase">Triple-cited sources</h4>
        {corpusVersion && <span className="text-[11px] font-mono text-stone-400">corpus {corpusVersion}</span>}
      </div>
      <div className="space-y-2.5">
        {citations.map((c) => (
          <a key={c.id} href={c.deep_link} target="_blank" rel="noreferrer" className="block rounded-xl border border-stone-200 bg-white p-3.5 hover:border-ink/20 hover:shadow-card transition">
            <div className="flex items-start justify-between gap-3">
              <div className="text-sm font-semibold text-ink leading-tight">{c.title}</div>
              <span className="shrink-0 text-[11px] font-mono px-2 py-1 rounded-full bg-stone-100 text-stone-600 border border-stone-200">{c.version_hash}</span>
            </div>
            <div className="mt-1 text-xs font-medium text-stone-500">{c.locator} · {c.source_type}</div>
            <div className="mt-2 text-sm leading-relaxed text-stone-700 border-l-2 border-amber-300 pl-3 bg-amber-50/50 py-2 rounded-r">“{c.span_text}”</div>
            <div className="mt-2 text-xs font-medium text-sky-700 flex items-center gap-1">↗ Verify at source <span className="truncate text-stone-400 font-normal">{c.deep_link}</span></div>
          </a>
        ))}
      </div>
      <p className="text-[11px] text-stone-400 leading-relaxed">Information only — not legal advice. Verify at source links before filing. Paid DB hits require explicit consent (logged).</p>
    </div>
  );
}
