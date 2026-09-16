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
          cookies. Voice input uses your browser&apos;s own speech recognition and the audio never
          leaves your device; only the transcribed text is sent.
        </p>
        <p className="text-sm text-stone-700 leading-relaxed">
          <strong className="font-bold">Your question is written to an audit log.</strong> Each
          question is stored together with the citations that were attached, the confidence score,
          the corpus version, and a random session id. The log exists so that a facilitator can
          trace how an answer was reached when you escalate a query to a human. The question text
          is kept up to 500 characters; the log is retained for the duration of the demo.
        </p>
        <p className="text-sm text-stone-700 leading-relaxed">
          The audit log is not readable over the API: the session-trail endpoint returns the
          system&apos;s behaviour — citations, confidence, corpus version — and never the question
          text. Questions are not sold, and are not shared with anyone except a facilitator you
          escalate to.
        </p>
        <p className="text-sm text-stone-700 leading-relaxed">
          <strong className="font-bold">Do not paste personal identifiers or confidential
          formulation details into the demo.</strong> The question you type is the one field we
          cannot pseudonymise and still keep useful for escalation.
        </p>
        <Link href="/" className="pressable inline-flex items-center rounded-full bg-ink text-white text-sm font-bold px-5 py-2.5">
          Back to Sahayak
        </Link>
      </div>
    </div>
  );
}
