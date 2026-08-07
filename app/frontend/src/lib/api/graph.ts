import { apiFetch } from "../api-client";
import type { DocumentGraphFilters } from "./document-graph";

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

export async function getPatientGraph(
  patientId: string,
  filters?: DocumentGraphFilters,
): Promise<GraphDataResponse> {
  const params = new URLSearchParams();
  if (filters) {
    if (filters.node_limit !== undefined) params.append("node_limit", String(filters.node_limit));
    if (filters.edge_limit !== undefined) params.append("edge_limit", String(filters.edge_limit));
    if (filters.hop_depth !== undefined) params.append("hop_depth", String(filters.hop_depth));
    if (filters.min_confidence !== undefined)
      params.append("min_confidence", String(filters.min_confidence));
    if (filters.entity_types) {
      filters.entity_types.forEach((t) => params.append("entity_types", t));
    }
    if (filters.relation_types) {
      filters.relation_types.forEach((t) => params.append("relation_types", t));
    }
    if (filters.document_scope) {
      filters.document_scope.forEach((doc) => params.append("document_scope", doc));
    }
    if (filters.approved_revision_set_id) {
      params.append("approved_revision_set_id", filters.approved_revision_set_id);
    }
    if (filters.date_from) params.append("date_from", filters.date_from);
    if (filters.date_to) params.append("date_to", filters.date_to);
    if (filters.layout) params.append("layout", filters.layout);
    if (filters.include_superseded !== undefined) {
      params.append("include_superseded", String(filters.include_superseded));
    }
  }
  const queryString = params.toString();
  const path = queryString
    ? `/graph/patients/${patientId}?${queryString}`
    : `/graph/patients/${patientId}`;
  return apiFetch<GraphDataResponse>(path);
}
