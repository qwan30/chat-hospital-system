import { apiFetch } from "../api-client";

export interface VectorMetricsResponse {
  indexed_document_count: number;
  active_chunk_count: number;
  sources: Array<{ document_id: string; chunk_count: number }>;
}

export async function getVectorMetrics(): Promise<VectorMetricsResponse> {
  return await apiFetch<VectorMetricsResponse>("/api/v1/metrics/vector");
}
