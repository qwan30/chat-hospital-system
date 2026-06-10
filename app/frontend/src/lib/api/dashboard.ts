import { apiFetch, type ApiClientOptions, type DashboardSummary } from "@/lib/api-client";

export function getDashboardSummary(opts: ApiClientOptions): Promise<DashboardSummary> {
  return apiFetch<DashboardSummary>("/dashboard/summary", { ...opts, method: "GET" });
}
