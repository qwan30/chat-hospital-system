import { apiFetch } from "../api-client";

export interface AuditLog {
  id: string;
  actor_user_id: string | null;
  action: string;
  object_type: string;
  object_id: string | null;
  patient_id?: string | null;
  outcome: string;
  trace_id?: string | null;
  ip_address?: string | null;
  metadata?: Record<string, unknown> | null;
  created_at: string;
}

export interface AuditLogList {
  items: AuditLog[];
}

export interface AuditLogFilters {
  patient_id?: string;
  action?: string;
  outcome?: string;
  limit?: number;
}

export async function getAuditLogs(filters?: AuditLogFilters): Promise<AuditLogList> {
  const params = new URLSearchParams();
  if (filters?.patient_id) params.append("patient_id", filters.patient_id);
  if (filters?.action) params.append("action", filters.action);
  if (filters?.outcome) params.append("outcome", filters.outcome);
  if (filters?.limit) params.append("limit", filters.limit.toString());

  return apiFetch<AuditLogList>(`/audit/logs?${params.toString()}`);
}
