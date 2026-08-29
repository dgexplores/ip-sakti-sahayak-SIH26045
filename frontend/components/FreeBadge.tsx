"use client";
export function FreeBadge() {
  return (
    <span className="inline-flex items-center gap-1.5 text-[11px] font-bold px-2.5 py-1 rounded-full bg-emerald-500 text-white">
      <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
      100% FREE — no API keys · offline ready
    </span>
  );
}
export function OfflineReadyBanner() {
  return (
    <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-3 flex items-start gap-3">
      <span className="text-lg">✓</span>
      <div className="text-xs leading-relaxed">
        <div className="font-bold text-emerald-900">Zero-cost, zero-keys demo — runs on your laptop</div>
        <div className="text-emerald-800">Local MiniLM embeddings + offline extractive RAG + pgvector. No OpenAI, no Cohere, no billing. Works on airplane mode. Switch to Ollama/HF free tier anytime — see <code className="bg-white px-1 rounded">.env.example</code>.</div>
      </div>
    </div>
  );
}
