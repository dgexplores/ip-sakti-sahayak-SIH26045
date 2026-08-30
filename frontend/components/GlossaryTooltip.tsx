"use client";
import { useState } from "react";

const GLOSSARY: Record<string, string> = {
  "Sec 3(p)": "Patents Act bar: traditional knowledge = not patentable. Copy-paste from old book → no patent.",
  "TKDL": "Traditional Knowledge Digital Library — govt DB that blocks foreign patents by proving prior art.",
  "ABS": "Access & Benefit Sharing — you used Indian plant/knowledge? Share benefits, get NBA/SBB permission.",
  "BDA": "Biological Diversity Act 2023 — law for using Indian biological resources.",
  "NBA": "National Biodiversity Authority — approves foreign use of Indian plants.",
  "SBB": "State Biodiversity Board — approve/intimate for Indian users.",
  "GRATK": "WIPO treaty 2024 — disclose where genetic resource / TK came from in patent filing.",
  "PCT": "Patent Cooperation Treaty — one filing to go international.",
  "Classical": "Recipe exactly as in old texts (First Schedule) — Sec 3(p) bar applies.",
  "Proprietary": "Changed ratio/process/dose from classical — may be patentable.",
  "Phytopharmaceutical": "Purified plant drug with 4+ markers — CDSCO pathway.",
};

// Longest term first, so "Sec 3(p)" doesn't get shadowed by a shorter overlapping key.
const GLOSSARY_TERMS = Object.keys(GLOSSARY).sort((a, b) => b.length - a.length);
const GLOSSARY_RE = new RegExp(`(${GLOSSARY_TERMS.map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})`, "g");

export function GlossaryText({ children }: { children: string }) {
  const [openKey, setOpenKey] = useState<string | null>(null);
  const parts = children.split(GLOSSARY_RE);
  if (parts.length === 1) return <span>{children}</span>;

  return (
    <span>
      {parts.map((part, i) => {
        const term = GLOSSARY[part];
        if (!term) return <span key={i}>{part}</span>;
        const key = `${part}-${i}`;
        return (
          <span
            key={key}
            className="underline decoration-dotted decoration-2 underline-offset-2 cursor-help font-semibold text-ink relative"
            onMouseEnter={() => setOpenKey(key)}
            onMouseLeave={() => setOpenKey(null)}
            onClick={() => setOpenKey(openKey === key ? null : key)}
          >
            {part}
            {openKey === key && (
              <span className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 w-64 p-3 rounded-xl bg-ink text-white text-xs leading-relaxed shadow-xl z-20">
                {term}
                <span className="absolute top-full left-1/2 -translate-x-1/2 w-2 h-2 bg-ink rotate-45 -mt-1" />
              </span>
            )}
          </span>
        );
      })}
    </span>
  );
}

export function GlossaryBar() {
  const top = ["Sec 3(p)", "TKDL", "ABS", "GRATK", "PCT"] as const;
  return (
    <div className="flex flex-wrap gap-1.5">
      {top.map((k) => (
        <span key={k} className="text-[11px] px-2 py-1 rounded-full bg-amber-50 border border-amber-200 text-amber-900 font-medium" title={GLOSSARY[k]}>
          {k}: {GLOSSARY[k].slice(0, 44)}…
        </span>
      ))}
    </div>
  );
}
