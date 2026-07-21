import { apiFetch } from "../api-client";

export interface GraphNode {
  id: string;
  type: string;
  label: string;
  sublabel?: string | null;
  source_document_id?: string | null;
  source_chunk_id?: string | null;
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
}

export interface GraphPathStep {
  from_node: string;
  to_node: string;
  relation: string;
  evidence: string;
  source_document_id?: string | null;
  source_chunk_id?: string | null;
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
  metadata?: any;
}

export async function getPatientGraph(patientId: string): Promise<GraphDataResponse> {
  return apiFetch<GraphDataResponse>(`/graph/patients/${patientId}`);
}
