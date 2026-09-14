import Link from "next/link";

export const metadata = {
  title: "Terms — IP-SAKTI Sahayak",
  description: "Terms of use for IP-SAKTI Sahayak demo.",
};

export default function Terms() {
  return (
    <div className="min-h-screen bg-[#FFFBF5] p-4 sm:p-6">
      <div className="mx-auto max-w-[760px] rounded-[20px] bg-white border-2 border-stone-200 shadow-card p-6 space-y-4">
        <h1 className="h-display text-balance text-xl font-extrabold tracking-tight">Terms of use</h1>
        <p className="text-sm text-stone-700 leading-relaxed">
          IP-SAKTI Sahayak gives citation-grounded information, not legal advice. Every answer
          links to its sources — verify against the official record and consult a registered IP
          facilitator before acting. Low-confidence answers abstain on purpose; that is the safe
          behavior, not a defect.
        </p>
        <p className="text-sm text-stone-700 leading-relaxed">
          Law summaries in the corpus are public-domain government text, condensed for retrieval.
          Demo provided as-is for SIH evaluation.
        </p>
        <Link href="/" className="pressable inline-flex items-center rounded-full bg-ink text-white text-sm font-bold px-5 py-2.5">
          Back to Sahayak
        </Link>
      </div>
    </div>
  );
}
