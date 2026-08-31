"use client";
import { cn } from "@/lib/utils";
import { Icon } from "@/components/Icon";
import { t } from "@/lib/i18n";

export type Jurisdiction = "india" | "international";

export function JurisdictionToggle({ value, onChange, lang = "en" }: { value: Jurisdiction; onChange: (v: Jurisdiction) => void; lang?: string }) {
  const s = t(lang);
  return (
    <div className="inline-flex p-1 rounded-full bg-white shadow-toggle border border-stone-200 touch-48" role="tablist" aria-label={`${s.india} / ${s.world}`}>
      <button
        role="tab"
        aria-selected={value === "india"}
        onClick={() => onChange("india")}
        className={cn(
          "pressable px-5 py-3 rounded-full text-[15px] font-bold flex items-center gap-2 touch-48",
          value === "india" ? "bg-saffron text-white shadow-md" : "text-stone-700 hover:text-ink"
        )}
        style={{ transition: "transform 160ms var(--ease-out), background-color 180ms var(--ease-out)" }}
      >
        <span className={cn("w-2.5 h-2.5 rounded-full shrink-0", value === "india" ? "bg-white" : "bg-saffron")} aria-hidden />
        <Icon name="india" className="w-4 h-4" />
        {s.india}
        <span className={cn("hidden sm:inline text-xs font-semibold opacity-90", value === "india" ? "text-white" : "text-stone-600")}>{s.indiaSub}</span>
      </button>
      <button
        role="tab"
        aria-selected={value === "international"}
        onClick={() => onChange("international")}
        className={cn(
          "pressable px-5 py-3 rounded-full text-[15px] font-bold flex items-center gap-2 touch-48",
          value === "international" ? "bg-indiaBlue text-white shadow-md" : "text-stone-700 hover:text-ink"
        )}
        style={{ transition: "transform 160ms var(--ease-out), background-color 180ms var(--ease-out)" }}
      >
        <span className={cn("w-2.5 h-2.5 rounded-full shrink-0", value === "international" ? "bg-sky-300" : "bg-indiaBlue")} aria-hidden />
        <Icon name="world" className="w-4 h-4" />
        {s.world}
        <span className={cn("hidden sm:inline text-xs font-semibold opacity-90", value === "international" ? "text-sky-200" : "text-stone-600")}>{s.worldSub}</span>
      </button>
    </div>
  );
}
