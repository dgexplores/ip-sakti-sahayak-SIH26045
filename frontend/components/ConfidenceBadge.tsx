"use client";
import { cn } from "@/lib/utils";

export function ConfidenceBadge({ score, abstain }: { score: number; abstain?: boolean }) {
  const level = abstain ? "abstain" : score >= 80 ? "high" : score >= 60 ? "mid" : "low";
  const styles: Record<string, string> = {
    high: "bg-emerald-50 text-emerald-700 border-emerald-200",
    mid: "bg-amber-50 text-amber-700 border-amber-200",
    low: "bg-red-50 text-red-700 border-red-200",
    abstain: "bg-stone-100 text-stone-700 border-stone-300",
  };
  return (
    <span className={cn("inline-flex items-center gap-2 px-2.5 py-1 rounded-full text-xs font-semibold border", styles[level])}>
      <span className={cn("w-2 h-2 rounded-full", level === "high" ? "bg-emerald-500" : level === "mid" ? "bg-amber-500" : level === "low" ? "bg-red-500" : "bg-stone-400")} />
      {abstain ? "ABSTAIN" : `${score.toFixed(0)}%`} confidence
    </span>
  );
}

export function ConfidenceBar({ score }: { score: number }) {
  return (
    <div className="confidence-track w-full">
      <div className="h-full bg-ink transition-all" style={{ width: `${Math.min(100, Math.max(0, score))}%`, opacity: 0.9 }} />
    </div>
  );
}
