"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { readStoredLang, t } from "@/lib/i18n";

/** Client component only so the 404 can honour the reader's language. It is a
 *  leaf with no data dependency, so the cost is a few hundred bytes.
 */
export default function NotFound() {
  const [lang, setLang] = useState("en");
  useEffect(() => {
    setLang(readStoredLang() ?? "en");
  }, []);
  const s = t(lang);

  return (
    <div className="min-h-screen bg-[#FFFBF5] grid place-items-center p-6">
      <div className="max-w-md w-full rounded-[20px] bg-white border-2 border-stone-200 shadow-card p-6 text-center space-y-4 stagger-in">
        <div className="w-12 h-12 mx-auto rounded-xl bg-indiaBlue text-white grid place-items-center text-sm font-extrabold" aria-hidden>IP</div>
        <div>
          <h1 className="h-display text-balance text-lg font-extrabold leading-tight">{s.nfTitle}</h1>
          <p className="text-sm text-stone-600 leading-relaxed mt-2">{s.nfBody}</p>
        </div>
        <Link
          href="/"
          className="pressable touch-48 w-full py-3 rounded-2xl bg-ink text-white text-[15px] font-extrabold inline-flex items-center justify-center"
        >
          {s.nfBack}
        </Link>
      </div>
    </div>
  );
}
