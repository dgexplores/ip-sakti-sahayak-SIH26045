"use client";
export function ExportButton({ answer, citations, jurisdiction, corpusVersion }: { answer: string; citations: any[]; jurisdiction: string; corpusVersion: string }) {
  function onExport() {
    const md = `# IP-SAKTI Sahayak — ${jurisdiction.toUpperCase()} Report\n\n**Corpus:** ${corpusVersion}\n**Jurisdiction:** ${jurisdiction}\n**Date:** ${new Date().toLocaleString()}\n\n---\n\n${answer}\n\n---\n\n## Citations\n${citations.map((c: any) => `- **${c.title}** — ${c.locator} — ${c.deep_link} — \`${c.version_hash}\`\n  > ${c.span_text.slice(0, 280)}`).join("\n")}\n\n---\nInformation only — not legal advice. Verify at source links before filing.\n`;
    const blob = new Blob([md], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `sakti-${jurisdiction}-${Date.now()}.md`; a.click();
    URL.revokeObjectURL(url);
  }
  function onPrint() { window.print(); }
  return (
    <div className="flex gap-2">
      <button onClick={onExport} className="text-xs font-semibold px-3 py-2 rounded-full bg-white border border-stone-300 hover:bg-stone-50">⬇ Export report (.md)</button>
      <button onClick={onPrint} className="text-xs font-semibold px-3 py-2 rounded-full bg-ink text-white hover:bg-stone-800">⎙ Print</button>
    </div>
  );
}
