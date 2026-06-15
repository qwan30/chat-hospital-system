export interface TraceSpan {
  id: string;
  name: string;
  service: string;
  startOffsetMs: number;
  durationMs: number;
  status: "ok" | "error" | "warn";
  attributes?: Record<string, string>;
}

export interface Trace {
  id: string;
  query: string;
  user: string;
  patient?: string;
  totalMs: number;
  ts: string;
  spans: TraceSpan[];
}

export const traces: Trace[] = [
  {
    id: "tr-001",
    query: "Latest LV ejection fraction and trend over last year",
    user: "Dr. Sarah Chen",
    patient: "Eleanor Vance (MRN-48201)",
    totalMs: 1842,
    ts: "2026-06-12T16:01:00Z",
    spans: [
      { id: "s1", name: "POST /api/chat", service: "BFF", startOffsetMs: 0, durationMs: 1842, status: "ok" },
      { id: "s2", name: "Auth · verify session", service: "Auth", startOffsetMs: 4, durationMs: 12, status: "ok" },
      { id: "s3", name: "Permission · ABAC eval", service: "AccessControl", startOffsetMs: 18, durationMs: 22, status: "ok", attributes: { policy: "treatment-relationship", result: "allow" } },
      { id: "s4", name: "Audit · log query", service: "Audit", startOffsetMs: 42, durationMs: 8, status: "ok" },
      { id: "s5", name: "Retrieval · hybrid search", service: "RAG", startOffsetMs: 52, durationMs: 384, status: "ok", attributes: { topK: "8", reranked: "true" } },
      { id: "s6", name: "LLM · generate (Qwen2.5-7B)", service: "Ollama", startOffsetMs: 440, durationMs: 1380, status: "ok" },
      { id: "s7", name: "Citation · resolve sources", service: "RAG", startOffsetMs: 1820, durationMs: 22, status: "ok" },
    ],
  },
  {
    id: "tr-002",
    query: "Recommended anticoagulation for AFib in CKD stage 3",
    user: "Dr. Sarah Chen",
    patient: "Eleanor Vance (MRN-48201)",
    totalMs: 920,
    ts: "2026-06-12T15:42:00Z",
    spans: [
      { id: "s1", name: "POST /api/chat", service: "BFF", startOffsetMs: 0, durationMs: 920, status: "warn" },
      { id: "s2", name: "Permission · ABAC eval", service: "AccessControl", startOffsetMs: 12, durationMs: 18, status: "ok" },
      { id: "s3", name: "Retrieval · hybrid search", service: "RAG", startOffsetMs: 36, durationMs: 280, status: "ok" },
      { id: "s4", name: "LLM · refused (insufficient evidence)", service: "Ollama", startOffsetMs: 320, durationMs: 600, status: "warn", attributes: { refusal: "insufficient_evidence", citations: "0" } },
    ],
  },
];

export function getTrace(id: string) {
  return traces.find((t) => t.id === id);
}