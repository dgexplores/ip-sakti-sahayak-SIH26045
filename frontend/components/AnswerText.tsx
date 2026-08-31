"use client";
import { Fragment, type ReactNode } from "react";
import { GlossaryText } from "@/components/GlossaryTooltip";

/** Renders the answer's markdown.
 *
 * The answer was previously printed with `whitespace-pre-wrap`, so the
 * generator's own markup showed up literally: readers saw `**Q:**` and a
 * leading `>` instead of a bold label and a quoted statute span. On the
 * single most-read element of the product that reads as broken.
 *
 * The generator emits a small, fixed subset (bold, italic, inline code,
 * links, blockquotes, list items, a rule), and this is the only producer,
 * so a targeted renderer is enough. A full markdown library would add a
 * dependency and an HTML-sanitising problem for markup we already control.
 */

const INLINE = /(\*\*[^*]+\*\*|\*[^*\n]+\*|`[^`]+`|\[[^\]]+\]\([^)]+\))/g;

function inline(text: string, keyBase: string): ReactNode[] {
  return text.split(INLINE).filter(Boolean).map((part, i) => {
    const key = `${keyBase}-${i}`;
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={key} className="font-bold text-ink">{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("*") && part.endsWith("*") && part.length > 2) {
      return <em key={key}>{part.slice(1, -1)}</em>;
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code key={key} className="font-mono text-[0.85em] px-1 py-0.5 rounded bg-stone-100 border border-stone-200">
          {part.slice(1, -1)}
        </code>
      );
    }
    const link = /^\[([^\]]+)\]\(([^)]+)\)$/.exec(part);
    if (link) {
      return (
        <a
          key={key}
          href={link[2]}
          target="_blank"
          rel="noreferrer"
          className="font-semibold text-indiaBlue underline decoration-indiaBlue/30 underline-offset-2 hover:decoration-indiaBlue"
        >
          {link[1]}
        </a>
      );
    }
    // Plain run: hand it to the glossary so legal terms keep their definitions.
    return <GlossaryText key={key}>{part}</GlossaryText>;
  });
}

export function AnswerText({ children }: { children: string }) {
  const lines = children.split("\n");
  const out: ReactNode[] = [];
  let quote: string[] = [];

  const flushQuote = () => {
    if (!quote.length) return;
    const body = quote.join("\n");
    out.push(
      <blockquote
        key={`q-${out.length}`}
        className="my-2 rounded-r-xl bg-stone-50 border border-stone-200 px-3 py-2 text-[15px] leading-relaxed text-stone-800"
      >
        {body.split("\n").map((l, i) => (
          <span key={i} className="block">{inline(l, `q${out.length}-${i}`)}</span>
        ))}
      </blockquote>
    );
    quote = [];
  };

  lines.forEach((raw, i) => {
    const line = raw.trimEnd();
    if (line.startsWith(">")) {
      quote.push(line.replace(/^>\s?/, ""));
      return;
    }
    flushQuote();
    if (!line.trim()) {
      out.push(<div key={`sp-${i}`} className="h-2" />);
      return;
    }
    if (/^-{3,}$/.test(line.trim())) {
      out.push(<hr key={`hr-${i}`} className="my-3 border-stone-200" />);
      return;
    }
    if (/^[-*]\s+/.test(line)) {
      out.push(
        <div key={`li-${i}`} className="flex gap-2 pl-1">
          <span aria-hidden className="mt-2 w-1 h-1 rounded-full bg-stone-400 shrink-0" />
          <span>{inline(line.replace(/^[-*]\s+/, ""), `li${i}`)}</span>
        </div>
      );
      return;
    }
    out.push(<p key={`p-${i}`}>{inline(line, `p${i}`)}</p>);
  });
  flushQuote();

  return <div className="space-y-0.5">{out.map((n, i) => <Fragment key={i}>{n}</Fragment>)}</div>;
}
