"use client";
import { useState } from "react";
import { escalate } from "@/lib/api";
import type { Citation, Jurisdiction } from "@/lib/api";

export function EscalateButton({ sessionId, query, jurisdiction, citations }: { sessionId: string; query: string; jurisdiction: Jurisdiction; citations: Citation[] }) {
  const [ticket, setTicket] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  async function onClick() {
    setLoading(true);
    try {
      const res = await escalate(sessionId, query, "low confidence / needs human IP facilitator", jurisdiction, citations);
      setTicket(res.ticket_id);
    } catch { setTicket("failed — try again"); }
    finally { setLoading(false); }
  }
  if (ticket) return <div className="rounded-xl bg-sky-50 border border-sky-200 p-3 text-sm"><div className="font-semibold text-sky-800">Ticket {ticket} created</div><div className="text-xs text-sky-700 mt-1">Facilitator will review with full trace (queries, citations, confidence, corpus versions). DPDP-consented log retained.</div></div>;
  return (
    <button onClick={onClick} disabled={loading} className="w-full py-2.5 rounded-xl bg-white border border-stone-300 text-sm font-semibold hover:bg-stone-50 disabled:opacity-60">
      {loading ? "Creating ticket…" : "Talk to IP Facilitator → escalate with trace"}
    </button>
  );
}
