"use client";
import { useEffect, useState } from "react";
import { readStoredLang, t } from "@/lib/i18n";

/** The skip link lives in the root layout, which is a server component and so
 *  cannot read the reader's language. This is the smallest client island that
 *  can. It is only read by screen readers, but "every UI string" means every
 *  UI string.
 */
export function SkipLink() {
  const [lang, setLang] = useState("en");
  useEffect(() => {
    setLang(readStoredLang() ?? "en");
  }, []);
  return (
    <a href="#main" className="skip-link">
      {t(lang).skipLink}
    </a>
  );
}
