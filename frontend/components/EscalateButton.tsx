"use client";
import { useState } from "react";
import { escalate } from "@/lib/api";
import type { Citation, Jurisdiction } from "@/lib/api";
import { Icon } from "@/components/Icon";
import { t } from "@/lib/i18n";

export function EscalateButton({ sessionId, query, jurisdiction, citations, lang = "en" }: { sessionId: string; query: string; jurisdiction: Jurisdiction; citations: Citation[]; lang?: string }) {
  const s = t(lang);
  const [ticket, setTicket] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);
  const [loading, setLoading] = useState(false);
  async function onClick() {
    setLoading(true);
    setFailed(false);
    try {
      const res = await escalate(sessionId, query, "low confidence / needs human IP facilitator", jurisdiction, citations);
      setTicket(res.ticket_id);
    } catch { setFailed(true); }
    finally { setLoading(false); }
  }
  // A failure used to reuse the success panel, so the reader saw the heading
  // "Sent to an expert" directly above the words "failed — try again".
  if (failed) return (
    <div className="stagger-in rounded-2xl bg-red-50 border-2 border-red-200 p-4 flex gap-3">
      <span className="w-9 h-9 rounded-xl bg-red-500 text-white grid place-items-center shrink-0"><Icon name="warn" className="w-4 h-4" /></span>
      <div className="text-sm text-red-900 leading-relaxed">{s.escalateFailed}</div>
    </div>
  );
  if (ticket) return (
    <div className="stagger-in rounded-2xl bg-emerald-50 border-2 border-emerald-200 p-4" style={{ animationDelay: "0ms" } as React.CSSProperties}>
      <div className="flex gap-3">
        <span className="w-9 h-9 rounded-xl bg-emerald-600 text-white grid place-items-center"><Icon name="check" className="w-4 h-4" strokeWidth={3} /></span>
        <div>
          <div className="text-sm font-extrabold text-emerald-900">{s.escalateDone} · {ticket}</div>
          <div className="text-sm text-emerald-800 leading-relaxed mt-1">{s.escalateDoneBody}</div>
        </div>
      </div>
    </div>
  );
  return (
    <button
      onClick={onClick}
      disabled={loading}
      className="pressable touch-48 w-full py-4 rounded-xl bg-white border-2 border-stone-300 text-[15px] font-bold flex items-center justify-center gap-2 hover:border-stone-400 disabled:opacity-60"
    >
      <span className="w-8 h-8 rounded-xl bg-ink text-white grid place-items-center"><Icon name="human" className="w-4 h-4" /></span>
      {loading ? s.escalateSending : s.escalate}
    </button>
  );
}
