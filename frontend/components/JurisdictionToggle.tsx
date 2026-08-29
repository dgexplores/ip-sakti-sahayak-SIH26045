"use client";
import { cn } from "@/lib/utils";

export type Jurisdiction = "india" | "international";

export function JurisdictionToggle({ value, onChange }: { value: Jurisdiction; onChange: (v: Jurisdiction) => void }) {
  return (
    <div className="inline-flex p-1 rounded-full bg-white shadow-toggle border border-stone-200 touch-48" role="tablist" aria-label="Jurisdiction — hard firewall, never conflated">
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
        🇮🇳 INDIA
        <span className={cn("hidden sm:inline text-xs font-semibold opacity-90", value === "india" ? "text-white" : "text-stone-500")}>— Bharat ke niyam</span>
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
        🌐 WORLD
        <span className={cn("hidden sm:inline text-xs font-semibold opacity-90", value === "international" ? "text-sky-200" : "text-stone-500")}>— Videsh ke niyam</span>
      </button>
    </div>
  );
}
