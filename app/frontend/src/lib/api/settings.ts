import { apiFetch, type ApiClientOptions } from "@/lib/api-client";

export interface UserPreferences {
  default_patient_view: string;
  evidence_panel: boolean;
  auto_summary: boolean;
  confidence_warnings: boolean;
  theme: string;
  language: string;
}

export function getUserPreferences(opts: ApiClientOptions): Promise<UserPreferences> {
  return apiFetch<UserPreferences>("/users/me/preferences", { ...opts, method: "GET" });
}

export function updateUserPreferences(opts: ApiClientOptions, prefs: Partial<UserPreferences>): Promise<UserPreferences> {
  return apiFetch<UserPreferences>("/users/me/preferences", { ...opts, method: "PUT", body: JSON.stringify(prefs) });
}
