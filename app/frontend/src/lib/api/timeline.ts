import { apiFetch } from "../api-client";

export interface TimelineEvent {
  event_id: string;
  timestamp: string;
  type: "chat" | "document" | "audit";
  title: string;
  body: string;
  patient_id?: string;
  metadata: Record<string, any>;
}

export interface TimelineResponse {
  events: TimelineEvent[];
  total_count: number;
}

export async function getGlobalTimeline(limit = 50, offset = 0): Promise<TimelineResponse> {
  return apiFetch(`/timeline?limit=${limit}&offset=${offset}`);
}
