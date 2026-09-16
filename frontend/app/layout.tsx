import "./globals.css";
import type { Metadata } from "next";
import { SkipLink } from "@/components/SkipLink";

export const metadata: Metadata = {
  title: "IP-SAKTI Sahayak — Ayurveda IP & Regulatory Guidance",
  description: "Jurisdiction-aware, citation-grounded RAG for Ayurveda IP — India vs International, always cited, never conflated.",
  icons: { icon: "/icon.svg" },
  openGraph: {
    title: "IP-SAKTI Sahayak — Ayurveda IP & Regulatory Guidance",
    description: "Jurisdiction-aware, citation-grounded answers for Ayurveda IP. India vs International, always cited.",
    type: "website",
  },
  twitter: {
    card: "summary",
    title: "IP-SAKTI Sahayak — Ayurveda IP & Regulatory Guidance",
    description: "Jurisdiction-aware, citation-grounded answers for Ayurveda IP. India vs International, always cited.",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <SkipLink />
        {children}
      </body>
    </html>
  );
}
