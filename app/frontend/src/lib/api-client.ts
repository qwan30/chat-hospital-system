/**
 * Centralized API client with JWT auth header injection.
 * All frontend data access goes through this module.
 *
 * Backend base URL is configured via VITE_API_URL env var (defaults to
 * http://localhost:8000/api/v1). In dev, Vite proxies /api -> backend.
 */

const DEFAULT_API_URL = "/api";

function getBaseUrl(): string {
  // SSR needs absolute URL; browser uses relative /api → Vite proxy → backend
  if (typeof window === "undefined") return "http://localhost:8000/api/v1";
  return (import.meta.env.VITE_API_URL as string) || DEFAULT_API_URL;
}

let memoryToken: string | null = null;

export function getToken(): string | null {
  return memoryToken;
}

export interface ApiClientOptions {
  /** Override the default base URL (rarely needed). */
  baseUrl?: string;
}

export class ApiError extends Error {
  status: number;
  code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
  opts: ApiClientOptions = {},
): Promise<T> {
  const baseUrl = opts.baseUrl || getBaseUrl();
  const normalizedBase = baseUrl.replace(/\/+$/, "");

  const url = `${normalizedBase}${path}`;
  const token = getToken();

  const headers: Record<string, string> = {
    ...(init.headers as Record<string, string>),
  };

  if (!(init.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(url, { ...init, headers });

  if (!response.ok) {
    let errorData: { error?: string; message?: string; detail?: string } = {};
    try {
      errorData = await response.json();
    } catch {
      // ignore parse error
    }
    throw new ApiError(
      response.status,
      errorData.error || "UNKNOWN",
      errorData.message || errorData.detail || response.statusText,
    );
  }

  if (response.status === 204) return undefined as unknown as T;

  const data = await response.json();
  return data as unknown as T;
}

// ── Auth helpers ─────────────────────────────────────────────────────

export async function verifyToken(
  apiUrl: string,
  token: string,
): Promise<{
  id: string;
  email: string;
  full_name: string;
  department?: string;
  workspace?: string;
  role: string;
  is_active: boolean;
} | null> {
  try {
    const res = await fetch(`${apiUrl.replace(/\/+$/, "")}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export function persistToken(token: string): void {
  memoryToken = token;
}

export function clearToken(): void {
  memoryToken = null;
}

export function getStoredApiUrl(): string {
  if (typeof window === "undefined") return DEFAULT_API_URL;
  return localStorage.getItem("hospital_ai_api_url") || DEFAULT_API_URL;
}

export function persistApiUrl(url: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem("hospital_ai_api_url", url);
}
