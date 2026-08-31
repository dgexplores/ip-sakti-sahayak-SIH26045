"use client";
import {
  AlertTriangle, ArrowRight, BookOpen, Check, Download, Droplet, Equal,
  ExternalLink, FlaskConical, Globe, Landmark, Leaf, Mic, Pill, Printer,
  Quote, Scale, ScrollText, ShieldCheck, Soup, Sparkles, Sprout, Square,
  Tag, UserRound,
} from "lucide-react";

/** One icon system, one stroke weight.
 *
 * These were emoji before. Emoji render differently on every platform (the
 * scroll is a beige blob on one, a line drawing on another), so a row of them
 * has no shared stroke, weight or optical size, and flag emoji degrade to
 * letter pairs on some Windows builds. Naming them semantically here also
 * means a concept is restyled in one place rather than hunted across files.
 */
const ICONS = {
  classical: ScrollText,      // formulation drawn from a classical text
  novel: FlaskConical,        // new extract or process
  world: Globe,               // international jurisdiction
  india: Landmark,            // Indian jurisdiction
  plant: Sprout,              // biological resource / ABS
  voice: Mic,
  firewall: ShieldCheck,      // jurisdiction firewall verdict
  simple: Sparkles,           // plain-language (ELI5) answer
  inBook: BookOpen,
  same: Equal,
  proprietary: Tag,
  phyto: Leaf,
  newDrug: Pill,
  aahar: Soup,
  cosmetic: Droplet,
  human: UserRound,           // escalate to a human facilitator
  warn: AlertTriangle,
  check: Check,
  legal: Scale,
  download: Download,
  print: Printer,
  verify: ExternalLink,       // open the official source
  cite: Quote,
  stop: Square,               // stop recording
  next: ArrowRight,
} as const;

export type IconName = keyof typeof ICONS;

export function Icon({
  name,
  className = "w-4 h-4",
  strokeWidth = 2,
}: {
  name: IconName;
  className?: string;
  strokeWidth?: number;
}) {
  const Glyph = ICONS[name];
  // Decorative by default: every icon in this UI sits beside its own text label.
  return <Glyph className={className} strokeWidth={strokeWidth} aria-hidden />;
}
