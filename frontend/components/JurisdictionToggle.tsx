"use client";
import { cn } from "@/lib/utils";

export type Jurisdiction = "india" | "international";

export function JurisdictionToggle({ value, onChange }: { value: Jurisdiction; onChange: (v: Jurisdiction) => void }) {
  return (
    <div className="inline-flex p-1 rounded-full bg-white shadow-toggle border border-stone-200" role="tablist" aria-label="Jurisdiction">
      <button
        role="tab"
        aria-selected={value === "india"}
        onClick={() => onChange("india")}
        className={cn(
          "px-5 py-2 rounded-full text-sm font-semibold transition-all flex items-center gap-2",
          value === "india" ? "bg-saffron text-white shadow-md" : "text-stone-600 hover:text-ink"
        )}
      >
        <span className={cn("w-2 h-2 rounded-full", value === "india" ? "bg-white" : "bg-saffron")} aria-hidden />
        INDIA
        <span className={cn("hidden sm:inline text-xs font-normal opacity-80", value === "india" ? "text-white" : "text-stone-500")}>— Patents Act, BDA, TKDL</span>
      </button>
      <button
        role="tab"
        aria-selected={value === "international"}
        onClick={() => onChange("international")}
        className={cn(
          "px-5 py-2 rounded-full text-sm font-semibold transition-all flex items-center gap-2",
          value === "international" ? "bg-indiaBlue text-white shadow-md" : "text-stone-600 hover:text-ink"
        )}
      >
        <span className={cn("w-2 h-2 rounded-full", value === "international" ? "bg-sky-300" : "bg-indiaBlue")} aria-hidden />
        INTERNATIONAL
        <span className={cn("hidden sm:inline text-xs font-normal opacity-80", value === "international" ? "text-sky-200" : "text-stone-500")}>— WIPO GRATK, PCT, CBD</span>
      </button>
    </div>
  );
}
