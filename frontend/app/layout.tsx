import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "IP-SAKTI Sahayak — Ayurveda IP & Regulatory Guidance",
  description: "Jurisdiction-aware, citation-grounded RAG for Ayurveda IP — India vs International, always cited, never conflated.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
