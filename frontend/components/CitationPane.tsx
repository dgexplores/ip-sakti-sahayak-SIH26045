"use client";
import type { Citation } from "@/lib/api";
import { Icon } from "@/components/Icon";
import { t } from "@/lib/i18n";


/** Source spans come straight from the corpus markdown, so a quoted span can
 *  carry "## " headings and "> " markers that mean nothing once the text is
 *  already inside a styled quote block. Strip the markup, keep the words. */
function plain(span: string): string {
  return span
    .replace(/^#{1,6}\s+/gm, "")
    .replace(/^>\s?/gm, "")
    .replace(/\*\*(.+?)\*\*/g, "$1")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/\s*\n\s*/g, " ")
    .trim();
}

export function CitationPane({ citations, corpusVersion, lang = "en" }: { citations: Citation[]; corpusVersion?: string; lang?: string }) {
  const s = t(lang);
  if (!citations?.length) {
    return (
      <div className="rounded-2xl border-2 border-dashed border-stone-300 bg-white p-5">
        <div className="w-10 h-10 rounded-xl bg-amber-100 border border-amber-200 grid place-items-center text-amber-700"><Icon name="cite" className="w-5 h-5" /></div>
        <div className="text-sm font-bold mt-2">{s.proofEmpty}</div>
        <p className="text-sm text-stone-600 leading-relaxed mt-1">{s.proofHint}</p>
      </div>
    );
  }
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <h4 className="h-display text-sm font-bold">{s.proofTitle}</h4>
        <span className="ml-auto text-xs font-mono px-2 py-1 rounded-full bg-stone-900 text-white">corpus {corpusVersion ?? "—"}</span>
      </div>
      <p className="text-xs text-stone-600 leading-relaxed">{s.proofHint}</p>
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
            <blockquote className="relative mt-3 rounded-xl bg-amber-50/70 border border-amber-200/70 px-3 py-2.5 text-sm leading-relaxed text-ink">
              <Icon name="cite" className="absolute right-2.5 top-2.5 w-3.5 h-3.5 text-amber-400/70" />
              <span className="block pr-5">{plain(c.span_text)}</span>
            </blockquote>
            <div className="mt-3 inline-flex items-center gap-1.5 text-xs font-bold px-3 py-2 rounded-full bg-sky-50 border border-sky-200 text-sky-800">
              <Icon name="verify" className="w-3.5 h-3.5" />
              {s.openSource}
            </div>
          </a>
        ))}
      </div>
      <p className="text-xs text-stone-500 leading-relaxed bg-stone-50 border border-stone-200 rounded-xl p-3">{s.disclaimer}</p>
    </div>
  );
}
