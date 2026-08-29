"use client";
export function HowItWorks() {
  const steps = [
    { n: 1, icon: "🎙️", t: "Bolo ya likho", d: "Tap mic — Hindi/Tamil/English. Type bhi chalega. Dono muft." },
    { n: 2, icon: "👆", t: "3 dabao, ho gaya", d: "Kitab me hai? Naya kya? Kya bechoge? — 3 tap me faisla." },
    { n: 3, icon: "📜", t: "Saboot ke saath jawab", d: "Har line ka kanoon + link. Kam bharosa → hum khud rokte hain." },
  ];
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
      {steps.map((s, i) => (
        <div key={s.n} className="stagger-in rounded-2xl bg-white border-2 border-stone-200 p-4 flex gap-3 items-start" style={{ animationDelay: `${i * 48}ms` } as React.CSSProperties}>
          <span className="w-10 h-10 rounded-xl bg-ink text-white grid place-items-center text-sm font-extrabold shrink-0">{s.n}</span>
          <span>
            <span className="block text-sm font-bold leading-none"><span aria-hidden className="mr-1">{s.icon}</span>{s.t}</span>
            <span className="block text-xs text-stone-600 leading-relaxed mt-1">{s.d}</span>
          </span>
        </div>
      ))}
    </div>
  );
}

export function ComparisonTable() {
  return (
    <div className="overflow-x-auto rounded-2xl border-2 border-stone-200 bg-white">
      <table className="w-full text-xs">
        <thead className="bg-stone-900 text-white text-xs">
          <tr><th className="text-left p-3 font-extrabold">Feature</th><th className="p-3 font-bold">ChatGPT</th><th className="p-3 font-bold">Demo site</th><th className="p-3 bg-emerald-600 font-extrabold">Hamara ✓</th></tr>
        </thead>
        <tbody className="divide-y divide-stone-200">
          {[
            ["India / World alag?", "Mix kar deta", "No split", "Hard firewall, rang alag"],
            ["Kitab vs naya triage", "Nahi", "Nahi", "3Q → table"],
            ["Har line ka saboot", "Number banata", "No cite", "Link + hash + confidence"],
            ["2024 Rules + GRATK", "Purana", "Static", "Hash per jawaab"],
            ["Chalane ka kharch", "$ lagta", "Free but no RAG", "₹0 offline"],
            ["Samajhna aasaan?", "Vakil bhasha", "English only", "ELI5 + boli + awaaz"],
          ].map(([f, a, b, c]) => (
            <tr key={f} className="hover:bg-stone-50">
              <td className="p-3 font-bold">{f}</td><td className="p-3 text-stone-600">{a}</td><td className="p-3 text-stone-600">{b}</td><td className="p-3 font-bold text-emerald-700 bg-emerald-50/60">{c}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
