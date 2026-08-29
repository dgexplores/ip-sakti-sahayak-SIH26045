"use client";
import type { Citation } from "@/lib/api";

export function CitationPane({ citations, corpusVersion }: { citations: Citation[]; corpusVersion?: string }) {
  if (!citations?.length) {
    return (
      <div className="rounded-2xl border-2 border-dashed border-stone-300 bg-white p-5">
        <div className="w-10 h-10 rounded-xl bg-amber-100 border border-amber-200 grid place-items-center text-lg" aria-hidden>📜</div>
        <div className="text-sm font-bold mt-2">Yahan saboot dikhega</div>
        <p className="text-sm text-stone-600 leading-relaxed mt-1">Jawab ka har line ka kanoon ka saboot yahan aayega — Act, Rule, Treaty + link. Low bharosa = hum seedha `human` ko bhejenge.</p>
      </div>
    );
  }
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <h4 className="h-display text-sm font-bold">Saboot — har line ka source</h4>
        <span className="ml-auto text-xs font-mono px-2 py-1 rounded-full bg-stone-900 text-white">corpus {corpusVersion ?? "—"}</span>
      </div>
      <p className="text-xs text-stone-600 leading-relaxed">Har dawa = ek kaagaz ka line. Ugly print nahi — tap karke asli sarkari link kholo.</p>
      <div className="space-y-3">
        {citations.map((c, i) => (
          <a
            key={c.id}
            href={c.deep_link}
            target="_blank"
            rel="noreferrer"
            className="pressable block rounded-2xl border-2 border-stone-200 bg-white p-4 hover:border-ink/20 hover:shadow-card stagger-in"
            style={{ animationDelay: `${i * 48}ms` } as React.CSSProperties}
          >
            <div className="flex items-start gap-3">
              <span className="w-8 h-8 rounded-xl bg-amber-500 text-white grid place-items-center text-xs font-extrabold shrink-0">{i + 1}</span>
              <div className="min-w-0 flex-1">
                <div className="text-sm font-bold leading-tight line-clamp-2">{c.title}</div>
                <div className="text-xs font-bold text-emerald-700 mt-1">{c.locator} · {c.source_type}</div>
              </div>
              <span className="shrink-0 text-xs font-mono px-2 py-1 rounded-full bg-stone-100 border border-stone-200">{c.version_hash}</span>
            </div>
            <div className="mt-3 text-sm leading-relaxed text-ink border-l-4 border-amber-400 pl-3 bg-amber-50/70 py-2 rounded-r">“{c.span_text}”</div>
            <div className="mt-3 inline-flex items-center gap-1.5 text-xs font-bold px-3 py-2 rounded-full bg-sky-50 border border-sky-200 text-sky-800">
              ↗ Asli sarkari page kholo
            </div>
          </a>
        ))}
      </div>
      <p className="text-xs text-stone-500 leading-relaxed bg-stone-50 border border-stone-200 rounded-xl p-3">⚖️ Information only — vakil ki salah nahi. File karne se pehle link check karo. Paid DB bina permission nahi khulta.</p>
    </div>
  );
}
