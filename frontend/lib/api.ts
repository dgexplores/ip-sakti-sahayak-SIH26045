export type Jurisdiction = "india" | "international";

export type Citation = {
  id: string;
  source_type: string;
  title: string;
  span_text: string;
  deep_link: string;
  locator: string;
  version_hash: string;
};

export type Confidence = { score: number; rationale: string; abstain: boolean };

export type FormulationCategory = "classical" | "proprietary" | "phytopharmaceutical" | "new_drug" | "ayurveda_aahar" | "cosmetic" | "unknown";

export type ChatResponse = {
  answer: string;
  jurisdiction: Jurisdiction;
  citations: Citation[];
  confidence: Confidence;
  corpus_version: string;
  escalate_suggested: boolean;
  escalate_ticket_id?: string | null;
  formulation_result?: { category: FormulationCategory; posture_table: Record<string, string>; next_steps: string[]; citations: Citation[] } | null;
  disclaimer: string;
  latency_ms?: number;
};

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function chat(query: string, jurisdiction: Jurisdiction, language = "en", formulation?: any, sessionId?: string): Promise<ChatResponse> {
  const res = await fetch(`${API}/api/v1/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, jurisdiction, language, formulation, session_id: sessionId }),
  });
  if (!res.ok) throw new Error(`chat failed ${res.status}`);
  return res.json();
}

export async function classify(query: string) {
  const res = await fetch(`${API}/api/v1/classify`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ query }) });
  return res.json();
}

export async function getCorpusVersion(): Promise<{ corpus_version: string; document_count: number }> {
  const res = await fetch(`${API}/api/v1/corpus/version`, { cache: "no-store" });
  return res.json();
}

export async function escalate(session_id: string, query: string, reason: string, jurisdiction: Jurisdiction, citations: Citation[] = []) {
  const res = await fetch(`${API}/api/v1/escalate`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ session_id, query, reason, jurisdiction, citations }) });
  return res.json();
}

export async function getFormulationQuestions() {
  const res = await fetch(`${API}/api/v1/formulation-questions`);
  return res.json();
}
