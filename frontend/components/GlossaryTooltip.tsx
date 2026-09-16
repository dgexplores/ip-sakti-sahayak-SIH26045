"use client";
import { useState } from "react";
import { glossary, GLOSSARY_TERMS } from "@/lib/i18n";

/** Legal-term tooltips.
 *
 * The definitions live in `lib/i18n.ts` alongside every other UI string, so
 * the language switch reaches them too. They used to be English-only prose
 * hardcoded here, which quietly falsified the multilingual claim.
 *
 * The term keys stay in Latin script on purpose — a reader has to be able to
 * match "Sec 3(p)" or "TKDL" against the official record, and the answer
 * text prints those tokens verbatim.
 */
const GLOSSARY_RE = new RegExp(
  `(${GLOSSARY_TERMS.map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})`,
  "g"
);

export function GlossaryText({ children, lang = "en" }: { children: string; lang?: string }) {
  const [openKey, setOpenKey] = useState<string | null>(null);
  const dict = glossary(lang);
  const parts = children.split(GLOSSARY_RE);
  if (parts.length === 1) return <span>{children}</span>;

  return (
    <span>
      {parts.map((part, i) => {
        const term = dict[part];
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

/** The five terms worth surfacing before a reader has asked anything. */
const TOP_TERMS = ["Sec 3(p)", "TKDL", "ABS", "GRATK", "PCT"] as const;

export function GlossaryBar({ lang = "en" }: { lang?: string }) {
  const dict = glossary(lang);
  return (
    <div className="flex flex-wrap gap-1.5">
      {TOP_TERMS.map((k) => (
        <span
          key={k}
          className="text-[11px] px-2 py-1 rounded-full bg-amber-50 border border-amber-200 text-amber-900 font-medium"
          title={dict[k]}
        >
          {k}: {dict[k].slice(0, 44)}…
        </span>
      ))}
    </div>
  );
}
