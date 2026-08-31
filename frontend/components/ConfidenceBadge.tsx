"use client";
import { cn } from "@/lib/utils";

export function ConfidenceBadge({ score, abstain, label = "confidence" }: { score: number; abstain?: boolean; label?: string }) {
  const level = abstain ? "abstain" : score >= 80 ? "high" : score >= 60 ? "mid" : "low";
  const styles: Record<string, string> = {
    high: "bg-emerald-500 text-white border-emerald-600",
    mid: "bg-amber-500 text-white border-amber-600",
    low: "bg-red-500 text-white border-red-600",
    abstain: "bg-stone-700 text-white border-stone-800",
  };
  return (
    <span className={cn("inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-extrabold border shadow-sm", styles[level])}>
      <span className={cn("w-2 h-2 rounded-full bg-white", abstain && "animate-pulse")} aria-hidden />
      {abstain ? "?" : `${score.toFixed(0)}%`} {label}
    </span>
  );
}

export function ConfidenceBar({ score }: { score: number }) {
  const pct = Math.min(100, Math.max(0, score));
  return (
    <div className="confidence-track w-full" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
      <div className="confidence-fill bg-ink" style={{ transform: `scaleX(${pct / 100})` }} />
    </div>
  );
}
