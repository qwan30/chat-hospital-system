import { apiFetch, type ApiClientOptions, type MetricsSummary } from "@/lib/api-client";

export interface TimeSeriesPoint {
  date: string;
  value: number;
}

export interface DepartmentVolume {
  department: string;
  count: number;
}

export function getMetricsSummary(opts: ApiClientOptions): Promise<MetricsSummary> {
  return apiFetch<MetricsSummary>("/metrics/summary", { ...opts, method: "GET" });
}

export function getQueryVolumeTrend(opts: ApiClientOptions, days?: number): Promise<TimeSeriesPoint[]> {
  const qs = days ? "?days=" + days : "";
  return apiFetch<{ points: TimeSeriesPoint[] }>("/metrics/trend" + qs, { ...opts, method: "GET" }).then((d) => d.points);
}

export function getDepartmentVolumes(opts: ApiClientOptions): Promise<DepartmentVolume[]> {
  return apiFetch<{ departments: DepartmentVolume[] }>("/metrics/departments", { ...opts, method: "GET" }).then((d) => d.departments);
}
