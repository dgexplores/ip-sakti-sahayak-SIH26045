"use client";
export function HowItWorks() {
  const steps = [
    { n: 1, t: "Ask in any language", d: "Type or speak (Bhashini). We keep India's law and World law separate — never mixed.", c: "bg-saffron" },
    { n: 2, t: "3 taps to classify", d: "Is it old book? New mix? Food or drug? 3 questions decide your IP/ABS path instantly.", c: "bg-amber-500" },
    { n: 3, t: "Get proof, not talk", d: "Every line cites Act/Rule/Treaty + link + confidence. Low confidence → we say 'no' and connect you to a human.", c: "bg-emerald-600" },
  ];
  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
      {steps.map((s) => (
        <div key={s.n} className="rounded-2xl bg-white border border-stone-200 p-4">
          <div className={`w-8 h-8 rounded-full ${s.c} text-white grid place-items-center text-sm font-bold`}>{s.n}</div>
          <div className="text-sm font-bold mt-2">{s.t}</div>
          <div className="text-xs text-stone-600 leading-relaxed mt-1">{s.d}</div>
        </div>
      ))}
    </div>
  );
}

export function ComparisonTable() {
  return (
    <div className="overflow-x-auto rounded-2xl border border-stone-200 bg-white">
      <table className="w-full text-xs">
        <thead className="bg-stone-900 text-white text-[11px] tracking-widest uppercase">
          <tr><th className="text-left p-3">Feature</th><th className="p-3">Generic LLM</th><th className="p-3">ip-sakti demo</th><th className="p-3 bg-emerald-600">IP-SAKTI (us) ✓</th></tr>
        </thead>
        <tbody className="divide-y divide-stone-200">
          {[
            ["India / International split", "Merges, hallucinates", "No split", "Hard toggle, firewall, visibly separate"],
            ["Classical vs proprietary triage", "None", "None", "3Q flow → posture table"],
            ["Citation per claim", "Fabricates Sec numbers", "None", "Triple cite + deep link + hash"],
            ["Knows 2024 Rules + GRATK 2024", "No (old cutoff)", "Static", "Git version hash per answer"],
            ["Cost to run demo", "$ keys needed", "Free but no RAG", "100% FREE offline (local MiniLM)"],
            ["Abstain when unsure", "Never", "Never", "Confidence gate + escalate ticket"],
          ].map(([f, a, b, c]) => (
            <tr key={f} className="hover:bg-stone-50">
              <td className="p-3 font-semibold">{f}</td><td className="p-3 text-stone-500">{a}</td><td className="p-3 text-stone-500">{b}</td><td className="p-3 font-semibold text-emerald-700 bg-emerald-50/50">{c}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
