import { apiFetch } from "../api-client";

export interface GraphProvenance {
  document_id?: string | null;
  generation_id?: string | null;
  revision_set_id?: string | null;
  page_revision_id?: string | null;
  page?: number | null;
  chunk_id?: string | null;
  start_offset?: number | null;
  end_offset?: number | null;
  bounding_boxes?: unknown;
  alignment_status?: string | null;
}

export interface GraphNode {
  id: string;
  type: string;
  label: string;
  sublabel?: string | null;
  source_document_id?: string | null;
  source_chunk_id?: string | null;
  source_generation_id?: string | null;
  source_revision_set_id?: string | null;
  source_page_revision_id?: string | null;
  source_page?: number | null;
  source_start_offset?: number | null;
  source_end_offset?: number | null;
  source_bounding_boxes?: unknown;
  source_alignment_status?: string | null;
  x: number;
  y: number;
}

export interface GraphEdge {
  id: string;
  from_node: string;
  to_node: string;
  label: string;
  source_document_id?: string | null;
  source_chunk_id?: string | null;
  source_generation_id?: string | null;
  source_revision_set_id?: string | null;
  source_page_revision_id?: string | null;
  source_page?: number | null;
  source_start_offset?: number | null;
  source_end_offset?: number | null;
  source_bounding_boxes?: unknown;
  source_alignment_status?: string | null;
}

export interface GraphPathStep {
  from_node: string;
  to_node: string;
  relation: string;
  evidence: string;
  source_document_id?: string | null;
  source_chunk_id?: string | null;
  source_generation_id?: string | null;
  source_revision_set_id?: string | null;
  source_page_revision_id?: string | null;
  source_page?: number | null;
  source_start_offset?: number | null;
  source_end_offset?: number | null;
  source_bounding_boxes?: unknown;
  source_alignment_status?: string | null;
}

export interface GraphPath {
  id: string;
  rationale: string;
  steps: GraphPathStep[];
}

export interface GraphDataResponse {
  patient_id: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  reasoning_path: GraphPath[];
  metadata?: Record<string, unknown>;
}

export async function getPatientGraph(patientId: string): Promise<GraphDataResponse> {
  return apiFetch<GraphDataResponse>(`/graph/patients/${patientId}`);
}
