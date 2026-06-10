import { apiFetch, type ApiClientOptions, type AuditEvent, type ListEnvelope } from "@/lib/api-client";

export interface AuditFilterParams {
  user_id?: string;
  action?: string;
  patient_id?: string;
  outcome?: string;
  from?: string;
  to?: string;
  page?: number;
  limit?: number;
}

export function listAuditEvents(opts: ApiClientOptions, params?: AuditFilterParams): Promise<AuditEvent[]> {
  const qs = params ? "?" + new URLSearchParams(
    Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined).map(([k, v]) => [k, String(v)]))
  ).toString() : "";
  return apiFetch<ListEnvelope<AuditEvent>>("/audit/events" + qs, { ...opts, method: "GET" }).then((d) => d.items);
}

export function getAuditEvent(opts: ApiClientOptions, eventId: string): Promise<AuditEvent> {
  return apiFetch<AuditEvent>("/audit/events/" + eventId, { ...opts, method: "GET" });
}
