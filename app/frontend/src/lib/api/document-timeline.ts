import { apiFetch } from "../api-client";

export interface TimelineEventProjection {
  event_id?: string | null;
  event_type: string;
  clinical_date: string | null;
  recorded_date: string;
  recorded_at?: string;
  evidence_ids: string[];
  confidence: number | null;
  reviewer_state: string;
  conflict_state: "none" | "date_conflict" | "value_conflict";
  supersession_lineage: string[];
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

export interface DocumentTimelineFilters {
  revision?: string;
  date_from?: string;
  date_to?: string;
  min_confidence?: number;
}

export interface DocumentTimelineResponse {
  document_id?: string;
  events: TimelineEventProjection[];
}

export async function getDocumentTimeline(
  documentId: string,
  filters?: DocumentTimelineFilters,
): Promise<DocumentTimelineResponse> {
  const params = new URLSearchParams();
  if (filters) {
    if (filters.revision) params.append("revision", filters.revision);
    if (filters.date_from) params.append("date_from", filters.date_from);
    if (filters.date_to) params.append("date_to", filters.date_to);
    if (filters.min_confidence !== undefined)
      params.append("min_confidence", String(filters.min_confidence));
  }
  const queryString = params.toString();
  const path = queryString
    ? `/documents/${documentId}/timeline?${queryString}`
    : `/documents/${documentId}/timeline`;
  return apiFetch<DocumentTimelineResponse>(path);
}
