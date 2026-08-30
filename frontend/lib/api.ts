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

export type FormulationAnswer = {
  q_source_text: boolean;
  q_novelty: boolean;
  q_category: FormulationCategory;
};

export type ChatResponse = {
  answer: string;
  answer_simple?: string | null;
  jurisdiction: Jurisdiction;
  citations: Citation[];
  confidence: Confidence;
  corpus_version: string;
  escalate_suggested: boolean;
  escalate_ticket_id?: string | null;
  formulation_result?: { category: FormulationCategory; posture_table: Record<string, string>; next_steps: string[]; citations: Citation[] } | null;
  firewall?: { status: string; message: string; foreign_ratio: number; mixed_query: boolean } | null;
  disclaimer: string;
  latency_ms?: number;
  free_tier?: boolean;
};

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/** Shared fetch wrapper: surfaces backend `{error:{message}}` bodies as real Error messages
 * instead of letting callers hit an opaque JSON-parse failure or silently-wrong data. */
async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API}${path}`, init);
  } catch {
    throw new Error("Can't reach the server. Check the backend is running (`make up`).");
  }
  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      message = body?.error?.message || message;
    } catch {
      // response wasn't JSON, keep the generic status message
    }
    throw new Error(message);
  }
  return res.json() as Promise<T>;
}

export async function chat(
  query: string,
  jurisdiction: Jurisdiction,
  language = "en",
  formulation?: FormulationAnswer,
  sessionId?: string,
  explainSimple = false
): Promise<ChatResponse> {
  return fetchJson<ChatResponse>("/api/v1/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, jurisdiction, language, formulation, session_id: sessionId, explain_simple: explainSimple }),
  });
}

export async function classify(query: string) {
  return fetchJson<{ jurisdiction: Jurisdiction; ip_type: string; confidence: number; needs_formulation_flow: boolean }>(
    "/api/v1/classify",
    { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ query }) }
  );
}

export async function getCorpusVersion(): Promise<{ corpus_version: string; document_count: number }> {
  return fetchJson("/api/v1/corpus/version", { cache: "no-store" });
}

export async function escalate(session_id: string, query: string, reason: string, jurisdiction: Jurisdiction, citations: Citation[] = []) {
  return fetchJson<{ ticket_id: string; status: string; message: string }>("/api/v1/escalate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id, query, reason, jurisdiction, citations }),
  });
}

export async function getFormulationQuestions() {
  return fetchJson<{ questions: unknown[] }>("/api/v1/formulation-questions");
}
