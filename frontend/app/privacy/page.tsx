import Link from "next/link";

export const metadata = {
  title: "Privacy — IP-SAKTI Sahayak",
  description: "Privacy notice for IP-SAKTI Sahayak demo.",
};

export default function Privacy() {
  return (
    <div className="min-h-screen bg-[#FFFBF5] p-4 sm:p-6">
      <div className="mx-auto max-w-[760px] rounded-[20px] bg-white border-2 border-stone-200 shadow-card p-6 space-y-4">
        <h1 className="h-display text-balance text-xl font-extrabold tracking-tight">Privacy notice</h1>
        <p className="text-sm text-stone-700 leading-relaxed">
          Demo build. Every visit is an anonymous session — no accounts, no login, no tracking
          cookies. Questions are sent to the backend to retrieve citations and are not sold or
          shared. Voice input uses your browser&apos;s own speech recognition and never leaves
          your device except as transcribed text.
        </p>
        <p className="text-sm text-stone-700 leading-relaxed">
          Do not paste personal identifiers or confidential formulation details into the demo.
        </p>
        <Link href="/" className="pressable inline-flex items-center rounded-full bg-ink text-white text-sm font-bold px-5 py-2.5">
          Back to Sahayak
        </Link>
      </div>
    </div>
  );
}
