# IP-SAKTI Sahayak — Design record

## Purpose

IP-SAKTI Sahayak is a calm, India-first public-service decision desk for Ayurveda-related intellectual-property and regulatory questions. It guides a person through a simple route: ask in their own language, understand a direct answer, then verify it with official material or escalate to an expert.

This document records the implemented home surface in `frontend/app/page.tsx`. It describes current behaviour, rather than a proposal.

## Experience thesis

The interface should feel more like a helpful public-service desk than a legal database:

- A warm paper field (`#f5f2ea`) reduces the severity of an unfamiliar legal task.
- Navy creates the institutional frame; saffron marks the active route and the plain-language answer.
- Source Serif 4 carries the service’s editorial, trustworthy voice; Source Sans 3 keeps controls and explanatory copy clear.
- Evidence is present but quiet: it occupies a right-hand rail on large screens and does not interrupt the first question.

The India jurisdiction is selected on arrival. International guidance remains an explicit, adjacent choice, preserving the product rule that India and international law must never be conflated.

## First viewport

The arrival sequence is deliberately narrow:

1. A compact product header identifies IP-SAKTI Sahayak, exposes Hindi, English, and Tamil controls, and shows corpus status when available.
2. An India-first headline promises “government proof” and says the user may ask in their own words.
3. A three-stage route makes the journey legible: ask, search the law, read the answer and proof. The current stage is saffron; completed stages become navy.
4. One question card holds the jurisdiction control, typing surface, voice input, simple-language preference, submit action, and examples. Optional formulation triage is offered below rather than imposed.
5. The support rail explains the proof model and service commitments without competing with the question task.

The default UI language is Hindi, then a saved language preference is restored after hydration. Hindi, English, and Tamil switch the visible UI copy; legal terms remain recognisable in Latin script when needed for source matching.

## Layout and responsive behaviour

| Viewport | Structure | Reading/action order |
| --- | --- | --- |
| Desktop (`lg` and above) | Main task column plus a 320px sticky evidence rail within a 1240px container. | Prompt and question card → optional triage → answer → citations in rail. |
| Tablet / small desktop | The header may wrap its controls while the task stays centered and readable. The question controls change from row to stacked layouts as space tightens. | Same primary route, without requiring a horizontal scan. |
| Mobile | The grid becomes one column. The guide, question card, optional triage, answer, support material, citations, and glossary stack vertically. Voice input moves below the textarea and actions become full-width/vertically ordered where needed. | Guide → ask → get answer → act → proof. |

The header uses a max-width content frame and practical page gutters (`16px` on small screens, `24px` from `sm`). The question card is the visual anchor: a white, bordered, softly shadowed surface against the paper ground. Subtle entrance motion is decorative only, and is removed for people who prefer reduced motion.

## Answer and evidence model

After a successful request, the route advances to stage three and the page scrolls the answer into view. The result surface follows this order:

1. A jurisdiction-coloured answer band identifies either India or international guidance and exposes the confidence score.
2. When supplied, a saffron-tinted “In simple words” block gives the direct answer first.
3. Legal reasoning is a user-controlled disclosure, not an automatic wall of legal text.
4. A formulation posture table appears only when the formulation flow produced one.
5. Confidence rationale, a low-confidence warning when relevant, expert escalation, report export, and the information-only disclaimer support the next decision.
6. Citations appear in the evidence rail on large screens and naturally follow the answer in the stacked mobile flow.

Mixed-jurisdiction questions may expose a separate split-view trigger. This protects the legal boundary rather than combining India and international conclusions in one answer.

## States and guardrails

- **Before asking:** shows the India-first prompt, examples, voice input, language choice, and optional three-question formulation triage.
- **Loading:** submit shows localized sending feedback and avoids duplicate sends.
- **Service/corpus unavailable:** the header reflects offline corpus status; request failures appear as a visible retryable alert.
- **Low confidence:** the answer explicitly recommends escalation rather than overstating certainty.
- **No source-free answer claim:** the surface describes itself as information, not legal advice, and directs people to official source links before filing.

## Accessibility and interaction

- Semantic `main`, ordered route list, section headings, and a keyboard-accessible skip link create a usable reading order.
- Language buttons expose pressed state; the legal-detail control exposes expanded state; the textarea has an accessible label; errors use `role="alert"`.
- Focus is consistently visible in navy. Controls use legible body sizing, generous spacing, and large mobile-friendly touch targets where the component system supplies them.
- The interface respects reduced motion, increased contrast, and reduced transparency preferences.
- Voice is a convenience path, never the only route; typing remains available if speech recognition is unsupported or fails.

## Visual tokens in use

| Role | Implemented treatment |
| --- | --- |
| Ground | `#f5f2ea` warm paper background |
| Institutional structure | `indiaBlue` / `#0B2239`, including header mark and India answer band |
| Active decision path | saffron `#FF9933`; pale saffron `#FFF3E0` for the direct-answer panel |
| Content surfaces | white or near-white (`#fffdf9`, `#fcfbf8`) with warm gray borders |
| Display type | Source Serif 4 |
| Body/UI type | Source Sans 3, with Noto Sans Devanagari fallback |
| Technical status text | JetBrains Mono where compact corpus status is shown |

## Deliberate non-goals

- The home surface does not present itself as a substitute for legal counsel.
- It does not lead with a corpus browser, dense citation list, or legal taxonomy.
- It does not force formulation classification before a user can ask a question.
- It does not merge Indian and international regimes into a single conclusion.

## Implementation anchors

- Primary composition and state transitions: `frontend/app/page.tsx`
- Brand tokens: `frontend/tailwind.config.js`
- Typography, motion, focus, and preference accommodations: `frontend/app/globals.css`
- Localised UI copy and language options: `frontend/lib/i18n.ts`
- Product constraints and audience: `PRODUCT.md`
