import { apiFetch } from "../api-client";

export interface DocumentGraphFilters {
  node_limit?: number;
  edge_limit?: number;
  hop_depth?: number;
  entity_types?: string[];
  relation_types?: string[];
  min_confidence?: number;
  document_scope?: string[];
  approved_revision_set_id?: string | null;
  date_from?: string | null;
  date_to?: string | null;
  layout?: "force" | "timeline" | "hierarchical";
  include_superseded?: boolean;
}

export interface GraphMentionRead {
  entity_id: string;
  generation_id: string;
  source_active_generation_id: string;
  normalized_label: string;
  entity_type: string;
  confidence: number;
}

export interface GraphAssertionRead {
  id: string;
  relation_type: string;
  evidence_ids: string[];
}

export interface DocumentGraphNode {
  id: string;
  type: string;
  label: string;
  sublabel?: string | null;
  source_document_id?: string | null;
  source_chunk_id?: string | null;
  x: number;
  y: number;
}

export interface DocumentGraphEdge {
  id: string;
  from_node: string;
  to_node: string;
  label: string;
  source_document_id?: string | null;
  source_chunk_id?: string | null;
}

export interface DocumentGraphRead {
  mentions: GraphMentionRead[];
  assertions: GraphAssertionRead[];
  document_id?: string;
  nodes?: DocumentGraphNode[];
  edges?: DocumentGraphEdge[];
  metadata?: Record<string, unknown>;
}

export async function getDocumentGraph(
  documentId: string,
  filters?: DocumentGraphFilters,
): Promise<DocumentGraphRead> {
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
    ? `/documents/${documentId}/graph?${queryString}`
    : `/documents/${documentId}/graph`;
  return apiFetch<DocumentGraphRead>(path);
}
