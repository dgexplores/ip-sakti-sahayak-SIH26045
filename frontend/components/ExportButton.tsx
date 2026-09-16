"use client";
import type { Citation, Confidence } from "@/lib/api";
import { Icon } from "@/components/Icon";
import { t } from "@/lib/i18n";

export function ExportButton({ answer, citations, jurisdiction, corpusVersion, confidence, lang = "en" }: { answer: string; citations: Citation[]; jurisdiction: string; corpusVersion: string; confidence?: Confidence | null; lang?: string }) {
  const s = t(lang);
  function onExport() {
    // The confidence line lives here rather than in the answer body: the body is
    // shared with the on-screen view, which already renders a badge, a bar and
    // the rationale, so printing it in the body showed the reader the same
    // sentence twice. The exported report has no UI, so it needs it back.
    const confLine = confidence
      ? `**Confidence:** ${confidence.score.toFixed(0)}/100 — ${confidence.rationale}${confidence.abstain ? " (abstained)" : ""}\n\n`
      : "";
    const md = `# IP-SAKTI Sahayak — ${jurisdiction.toUpperCase()} Report\n\n**Corpus:** ${corpusVersion}\n**Jurisdiction:** ${jurisdiction}\n**Date:** ${new Date().toLocaleString()}\n\n---\n\n${answer}\n\n${confLine}---\n\n## Citations\n${citations.map((c) => `- **${c.title}** — ${c.locator} — ${c.deep_link} — \`${c.version_hash}\`\n  > ${c.span_text.slice(0, 280)}`).join("\n")}\n\n---\n${s.disclaimer}\n`;
    const blob = new Blob([md], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `sakti-${jurisdiction}-${Date.now()}.md`; a.click();
    URL.revokeObjectURL(url);
  }
  function onPrint() { window.print(); }
  return (
    <div className="flex gap-2">
      <button
        onClick={onExport}
        className="pressable touch-48 inline-flex items-center justify-center gap-2 px-4 rounded-xl border-2 border-stone-200 bg-white text-sm font-bold text-stone-700 hover:border-stone-300"
       >
        <Icon name="download" className="w-4 h-4" />
        {s.export}
      </button>
      <button
        onClick={onPrint}
        className="pressable touch-48 inline-flex items-center justify-center gap-2 px-4 rounded-xl border-2 border-stone-200 bg-white text-sm font-bold text-stone-700 hover:border-stone-300"
       >
        <Icon name="print" className="w-4 h-4" />
        {s.print}
      </button>
    </div>
  );
}
