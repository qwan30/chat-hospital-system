import { apiFetch } from "../api-client";

export interface TimelineEventProjection {
  event_id?: string | null;
  event_type: string;
  clinical_date: string | null;
  recorded_date: string;
  recorded_at?: string;
  evidence_ids: string[];
  confidence: number;
  reviewer_state: string;
  conflict_state: "none" | "date_conflict" | "value_conflict";
  supersession_lineage: string[];
}

export interface DocumentTimelineFilters {
  revision?: string;
  date_from?: string;
  date_to?: string;
  event_types?: string[];
  include_superseded?: boolean;
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
    if (filters.event_types) {
      filters.event_types.forEach((t) => params.append("event_types", t));
    }
    if (filters.include_superseded !== undefined) {
      params.append("include_superseded", String(filters.include_superseded));
    }
  }
  const queryString = params.toString();
  const path = queryString
    ? `/documents/${documentId}/timeline?${queryString}`
    : `/documents/${documentId}/timeline`;
  return apiFetch<DocumentTimelineResponse>(path);
}
