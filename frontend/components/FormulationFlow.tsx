"use client";
import { useState } from "react";
import { cn } from "@/lib/utils";
import type { FormulationCategory } from "@/lib/api";

type Props = {
  onComplete: (ans: { q_source_text: boolean; q_novelty: boolean; q_category: FormulationCategory }) => void;
  compact?: boolean;
};

export function FormulationFlow({ onComplete, compact }: Props) {
  const [q1, setQ1] = useState<boolean | null>(null);
  const [q2, setQ2] = useState<boolean | null>(null);
  const [q3, setQ3] = useState<FormulationCategory | null>(null);

  const done = q1 !== null && q2 !== null && q3 !== null;

  const Option = ({ active, onClick, children }: { active?: boolean; onClick: () => void; children: React.ReactNode }) => (
    <button onClick={onClick} className={cn("px-3 py-1.5 rounded-full text-sm font-medium border transition", active ? "bg-ink text-white border-ink" : "bg-white text-stone-700 border-stone-300 hover:border-stone-400")}>
      {children}
    </button>
  );

  return (
    <div className={cn("rounded-2xl border bg-white shadow-card", compact ? "p-4" : "p-5")}>
      <div className="flex items-center gap-2 mb-3">
        <span className="w-7 h-7 rounded-full bg-amber-500 text-white grid place-items-center text-xs font-bold">3Q</span>
        <h3 className="text-sm font-bold tracking-tight">Formulation triage — classify before filing</h3>
        <span className="ml-auto text-xs text-stone-500">Sec 3(p) • TKDL • BDA</span>
      </div>

      <div className="space-y-4">
        <div>
          <p className="text-sm font-medium">1. Is it in a classical text (Charaka / First Schedule)?</p>
          <p className="text-xs text-stone-500 mb-2">Yes → classical path (Sec 3(p) bar, TKDL defence). No → proprietary/phytopharma.</p>
          <div className="flex gap-2"><Option active={q1 === true} onClick={() => setQ1(true)}>Yes, classical</Option><Option active={q1 === false} onClick={() => setQ1(false)}>No, not classical</Option></div>
        </div>
        <div>
          <p className="text-sm font-medium">2. Novel ingredient / ratio / process / dosage?</p>
          <p className="text-xs text-stone-500 mb-2">Novelty required for patentability.</p>
          <div className="flex gap-2"><Option active={q2 === true} onClick={() => setQ2(true)}>Yes, novel</Option><Option active={q2 === false} onClick={() => setQ2(false)}>No, same as verse</Option></div>
        </div>
        <div>
          <p className="text-sm font-medium">3. Intended category?</p>
          <div className="flex flex-wrap gap-2 mt-2">
            {(["classical","proprietary","phytopharmaceutical","new_drug","ayurveda_aahar","cosmetic"] as FormulationCategory[]).map((c) => (
              <Option key={c} active={q3 === c} onClick={() => setQ3(c)}>{c.replaceAll("_"," ")}</Option>
            ))}
          </div>
        </div>

        <button disabled={!done} onClick={() => done && onComplete({ q_source_text: q1!, q_novelty: q2!, q_category: q3! })} className={cn("w-full py-2.5 rounded-xl text-sm font-semibold transition", done ? "bg-saffron text-white hover:bg-saffron-dark" : "bg-stone-100 text-stone-400 cursor-not-allowed")}>
          {done ? "Show my IP / ABS posture →" : "Answer all 3 to classify"}
        </button>
        <p className="text-[11px] text-stone-400 text-center">Reduces 60% of follow-ups. Result table maps to Patents Act, BDA 2023, FSSAI Aahar.</p>
      </div>
    </div>
  );
}

export function PostureTable({ table, nextSteps, category }: { table: Record<string,string>; nextSteps: string[]; category: string }) {
  return (
    <div className="rounded-2xl border border-emerald-200 bg-emerald-50/60 p-4">
      <div className="text-xs font-semibold tracking-widest text-emerald-700 uppercase">Result — {category.replaceAll("_"," ")}</div>
      <div className="mt-3 grid gap-3 sm:grid-cols-3">
        {Object.entries(table).map(([k,v]) => (
          <div key={k} className="rounded-xl bg-white border border-emerald-100 p-3">
            <div className="text-xs font-bold tracking-widest text-stone-500 uppercase">{k}</div>
            <div className="text-sm leading-relaxed mt-1">{v}</div>
          </div>
        ))}
      </div>
      <div className="mt-3">
        <div className="text-xs font-semibold text-stone-600">Next steps</div>
        <ul className="mt-1.5 space-y-1">
          {nextSteps.map((s) => <li key={s} className="text-sm flex gap-2"><span className="text-emerald-600">→</span><span>{s}</span></li>)}
        </ul>
      </div>
    </div>
  );
}
