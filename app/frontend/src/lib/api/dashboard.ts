import { apiFetch } from "../api-client";

// ── Types matching backend schemas/dashboard.py ──────────────────────

export interface RecentPatient {
  id: string;
  full_name: string;
  mrn: string;
  last_accessed: string | null;
}

export interface DocumentStats {
  indexed: number;
  processing: number;
  failed: number;
}

export interface DashboardMetrics {
  hours_saved: number;
  cost_saved_usd: number;
}

export interface SystemsHealth {
  hms_api: string;
  ollama_inference: string;
}

export interface DashboardSummaryResponse {
  recent_patients: RecentPatient[];
  document_stats: DocumentStats;
  metrics: DashboardMetrics;
  systems_health: SystemsHealth;
}

// ── API call ─────────────────────────────────────────────────────────

export async function getDashboardSummary(): Promise<DashboardSummaryResponse> {
  return apiFetch<DashboardSummaryResponse>("/dashboard/summary");
}
