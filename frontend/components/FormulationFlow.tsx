"use client";
import { useState } from "react";
import { cn } from "@/lib/utils";
import type { FormulationCategory } from "@/lib/api";
import { Icon, type IconName } from "@/components/Icon";
import { tri } from "@/lib/i18n";

const CATEGORY_ICON: Record<FormulationCategory, IconName> = {
  classical: "classical",
  proprietary: "proprietary",
  phytopharmaceutical: "phyto",
  new_drug: "newDrug",
  ayurveda_aahar: "aahar",
  cosmetic: "cosmetic",
  unknown: "check",
};

type Props = {
  onComplete: (ans: { q_source_text: boolean; q_novelty: boolean; q_category: FormulationCategory }) => void;
  compact?: boolean;
  lang?: string;
};

export function FormulationFlow({ onComplete, compact, lang = "en" }: Props) {
  const x = tri(lang);
  const [step, setStep] = useState(1);
  const [q1, setQ1] = useState<boolean | null>(null);
  const [q2, setQ2] = useState<boolean | null>(null);
  const [q3, setQ3] = useState<FormulationCategory | null>(null);

  const done = q1 !== null && q2 !== null && q3 !== null;

  const BigYesNo = ({ active, onClick, icon, title, sub }: { active?: boolean; onClick: () => void; icon: IconName; title: string; sub: string }) => (
    <button
      onClick={onClick}
      className={cn(
        "pressable touch-48 rounded-2xl border-2 p-4 text-left flex gap-3 items-center transition-colors",
        active ? "bg-ink text-white border-ink shadow-card" : "bg-white border-stone-200 hover:border-stone-300"
      )}
      aria-pressed={active}
    >
      <span className={cn("w-12 h-12 rounded-xl grid place-items-center shrink-0", active ? "bg-white/15" : "bg-stone-50 border border-stone-200")}><Icon name={icon} className="w-5 h-5" /></span>
      <span>
        <span className={cn("block text-[15px] font-bold leading-none", active ? "text-white" : "text-ink")}>{title}</span>
        <span className={cn("block text-xs leading-relaxed mt-1", active ? "text-white/70" : "text-stone-500")}>{sub}</span>
      </span>
    </button>
  );

  return (
    <div className={cn("rounded-[20px] border bg-white shadow-card overflow-hidden", compact ? "p-4" : "p-0")}>
      {/* Progress — 3 dots, width via transform scaleX */}
      <div className="px-5 pt-5 flex items-center gap-3">
        <span className="w-8 h-8 rounded-full bg-amber-500 text-white grid place-items-center text-xs font-extrabold">3Q</span>
        <div className="flex-1 h-1.5 rounded-full bg-stone-100 overflow-hidden flex gap-1 p-1">
          {[1, 2, 3].map((n) => (
            <span key={n} className={cn("flex-1 h-full rounded-full transition-colors", n <= (q1 !== null ? 1 : 0) + (q2 !== null ? 1 : 0) + (q3 !== null ? 1 : 0) ? "bg-ink" : "bg-stone-200")} style={{ transition: "background-color 200ms var(--ease-out)" }} />
          ))}
        </div>
        <span className="text-xs font-bold text-stone-600">{x.step} {step}/3</span>
      </div>

      <div className="p-5 space-y-5">
        {/* Step 1 — always visible first, progressive */}
        <div className="space-y-3">
          <h3 className="h-display text-lg font-bold leading-tight">1. {x.q1}</h3>
          <p className="text-sm text-stone-600 leading-relaxed">{x.q1hint}</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <BigYesNo active={q1 === true} onClick={() => { setQ1(true); setStep(2); }} icon="inBook" title={x.q1yes} sub={x.q1yesSub} />
            <BigYesNo active={q1 === false} onClick={() => { setQ1(false); setStep(2); }} icon="novel" title={x.q1no} sub={x.q1noSub} />
          </div>
        </div>

        <div className={cn("space-y-3 pt-4 border-t border-stone-100 transition-opacity", q1 === null ? "opacity-40 pointer-events-none" : "opacity-100")}>
          <h3 className="h-display text-lg font-bold leading-tight">2. {x.q2}</h3>
          <p className="text-sm text-stone-600 leading-relaxed">{x.q2hint}</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <BigYesNo active={q2 === true} onClick={() => { setQ2(true); setStep(3); }} icon="novel" title={x.q2yes} sub={x.q2yesSub} />
            <BigYesNo active={q2 === false} onClick={() => { setQ2(false); setStep(3); }} icon="same" title={x.q2no} sub={x.q2noSub} />
          </div>
        </div>

        <div className={cn("space-y-3 pt-4 border-t border-stone-100", q2 === null ? "opacity-40 pointer-events-none" : "opacity-100")}>
          <h3 className="h-display text-lg font-bold leading-tight">3. {x.q3}</h3>
          <p className="text-sm text-stone-600">{x.q3hint}</p>
          <div className="grid grid-cols-2 gap-2">
            {(["classical", "proprietary", "phytopharmaceutical", "new_drug", "ayurveda_aahar", "cosmetic"] as FormulationCategory[]).map((c) => (
              <button
                key={c}
                onClick={() => setQ3(c)}
                className={cn(
                  "pressable touch-48 rounded-xl border-2 px-3 py-3 text-sm font-bold leading-tight",
                  q3 === c ? "bg-ink text-white border-ink" : "bg-white text-stone-700 border-stone-200 hover:border-stone-300"
                )}
                aria-pressed={q3 === c}
              >
                <span className="grid place-items-center mb-1"><Icon name={CATEGORY_ICON[c]} className="w-5 h-5" /></span>
                {x.cat[c] ?? c.replaceAll("_", " ")}
              </button>
            ))}
          </div>
        </div>

        <button
          disabled={!done}
          onClick={() => done && onComplete({ q_source_text: q1!, q_novelty: q2!, q_category: q3! })}
          className={cn(
            "pressable w-full touch-48 py-4 rounded-xl text-[16px] font-extrabold flex items-center justify-center gap-2",
            done ? "bg-saffron text-white shadow-md hover:bg-saffron-dark" : "bg-stone-100 text-stone-400 cursor-not-allowed"
          )}
          style={{ transition: "transform 160ms var(--ease-out), background-color 180ms var(--ease-out)" }}
        >
          {done ? x.submit : x.incomplete}
          {done && <Icon name="next" className="w-4 h-4" />}
        </button>
        <p className="text-xs text-center text-stone-600 leading-relaxed">{x.footnote}</p>
      </div>
    </div>
  );
}

export function PostureTable({ table, nextSteps, category, lang = "en" }: { table: Record<string, string>; nextSteps: string[]; category: string; lang?: string }) {
  const x = tri(lang);
  const icons: Record<string, IconName> = { IP: "firewall", ABS: "plant", Regulatory: "legal" };
  return (
    <div className="rounded-2xl border-2 border-emerald-200 bg-emerald-50/70 overflow-hidden">
      <div className="px-4 py-3 flex items-center gap-2 bg-emerald-600 text-white">
        <span className="text-sm font-extrabold tracking-tight">{x.resultTitle}: {x.cat[category] ?? category.replaceAll("_", " ")}</span>
        <span className="ml-auto inline-flex items-center gap-1 text-xs font-bold px-2 py-1 rounded-full bg-white/20"><Icon name="check" className="w-3 h-3" strokeWidth={3} />{x.done}</span>
      </div>
      <div className="p-4 grid gap-3 sm:grid-cols-3">
        {Object.entries(table).map(([k, v], i) => (
          <div key={k} className="stagger-in rounded-xl bg-white border border-emerald-100 p-3 shadow-sm" style={{ animationDelay: `${i * 48}ms` }}>
            <div className="flex items-center gap-2">
              <span className="w-7 h-7 rounded-lg bg-emerald-50 border border-emerald-200 grid place-items-center text-emerald-700"><Icon name={icons[k] ?? "check"} className="w-3.5 h-3.5" /></span>
              <span className="text-xs font-extrabold tracking-widest text-emerald-700 uppercase">{k}</span>
            </div>
            <div className="text-sm leading-relaxed mt-2 text-ink">{v}</div>
          </div>
        ))}
      </div>
      <div className="px-4 pb-4">
        <div className="text-xs font-extrabold tracking-widest text-stone-600 uppercase">{x.nextSteps}</div>
        <ul className="mt-2 space-y-2">
          {nextSteps.map((s, i) => (
            <li key={s} className="stagger-in flex gap-2 text-sm leading-relaxed bg-white border border-stone-200 rounded-xl px-3 py-2.5" style={{ animationDelay: `${140 + i * 48}ms` }}>
              <span className="w-6 h-6 rounded-full bg-ink text-white grid place-items-center text-xs font-bold shrink-0">{i + 1}</span>
              <span>{s}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
