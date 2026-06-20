import { apiFetch } from "../api-client";

export interface RagTraceEvidence {
  evidence_id: string;
  chunk_id: string;
  rank: number;
  retrieval_score: number;
  rerank_score?: number | null;
  retrieval_method: string;
  rerank_method?: string | null;
  citation_label: string;
  content?: string | null;
  document_title?: string | null;
  page?: number | null;
}

export interface RagTraceResponse {
  query_id: string;
  question: string;
  answer?: string | null;
  status: string;
  pipeline?: string | null;
  model?: string | null;
  latency_ms?: number | null;
  evidence: RagTraceEvidence[];
  created_at: string;
}

export async function getQueryTrace(queryId: string): Promise<RagTraceResponse> {
  return apiFetch<RagTraceResponse>(`/chat/queries/${queryId}/trace`);
}
