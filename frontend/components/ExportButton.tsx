"use client";
import type { Citation } from "@/lib/api";

export function ExportButton({ answer, citations, jurisdiction, corpusVersion }: { answer: string; citations: Citation[]; jurisdiction: string; corpusVersion: string }) {
  function onExport() {
    const md = `# IP-SAKTI Sahayak — ${jurisdiction.toUpperCase()} Report\n\n**Corpus:** ${corpusVersion}\n**Jurisdiction:** ${jurisdiction}\n**Date:** ${new Date().toLocaleString()}\n\n---\n\n${answer}\n\n---\n\n## Citations\n${citations.map((c) => `- **${c.title}** — ${c.locator} — ${c.deep_link} — \`${c.version_hash}\`\n  > ${c.span_text.slice(0, 280)}`).join("\n")}\n\n---\nInformation only — not legal advice. Verify at source links before filing.\n`;
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
        className="pressable touch-48 px-4 rounded-xl border-2 border-stone-200 bg-white text-sm font-bold text-stone-700 hover:border-stone-300"
      >
        ⬇ Export .md
      </button>
      <button
        onClick={onPrint}
        className="pressable touch-48 px-4 rounded-xl border-2 border-stone-200 bg-white text-sm font-bold text-stone-700 hover:border-stone-300"
      >
        ⎙ Print
      </button>
    </div>
  );
}
