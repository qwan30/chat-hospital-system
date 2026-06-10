import { apiFetch, type ApiClientOptions } from "@/lib/api-client";

export interface LoginResponse {
  token: string;
  user: { id: string; full_name: string; email: string; role: string; department: string };
}

export interface MfaResponse {
  mfa_required: boolean;
  session_id?: string;
}

export interface MfaVerifyResponse {
  token: string;
  user: { id: string; full_name: string; email: string; role: string; department: string };
}

export function login(opts: { apiUrl: string }, body: { email: string; password: string }): Promise<LoginResponse> {
  return apiFetch<LoginResponse>("/auth/login", { ...opts, token: "", method: "POST", body: JSON.stringify(body) });
}

export function verifyMfa(opts: { apiUrl: string }, body: { session_id: string; code: string }): Promise<MfaVerifyResponse> {
  return apiFetch<MfaVerifyResponse>("/auth/mfa/verify", { ...opts, token: "", method: "POST", body: JSON.stringify(body) });
}

export function getCurrentUser(opts: ApiClientOptions): Promise<{ id: string; full_name: string; email: string; role: string; department: string }> {
  return apiFetch("/auth/me", { ...opts, method: "GET" });
}
