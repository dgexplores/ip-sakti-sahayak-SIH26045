"use client";
import { Icon, type IconName } from "@/components/Icon";
export function FreeBadge() {
  return (
    <span className="inline-flex items-center gap-1.5 text-xs font-extrabold px-3 py-1.5 rounded-full bg-emerald-500 text-white shadow-sm">
      <span className="w-2 h-2 rounded-full bg-white animate-pulse" aria-hidden />
      ₹0 — bina key, offline
    </span>
  );
}
export function OfflineReadyBanner() {
  return (
    <div className="stagger-in rounded-2xl bg-emerald-50 border-2 border-emerald-200 p-4 flex gap-3" style={{ animationDelay: "0ms" } as React.CSSProperties}>
      <span className="w-9 h-9 rounded-xl bg-emerald-600 text-white grid place-items-center shrink-0"><Icon name="check" className="w-4 h-4" strokeWidth={3} /></span>
      <div className="text-sm leading-relaxed">
        <div className="font-extrabold text-emerald-900">Bina internet, bina paise — laptop pe chalega</div>
        <div className="text-emerald-800">MiniLM (80MB) + offline jawaab + pgvector. No `OpenAI` key. Network gaya bhi to jawab + saboot dikhega.</div>
      </div>
    </div>
  );
}
