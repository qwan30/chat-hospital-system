/**
 * Centralized API client with JWT auth header injection.
 * All frontend data access goes through this module.
 *
 * Backend base URL is configured via VITE_API_URL env var (defaults to
 * http://localhost:8000/api/v1). In dev, Vite proxies /api -> backend.
 */

const DEFAULT_API_URL = "http://localhost:8000/api/v1";

function getBaseUrl(): string {
  if (typeof window === "undefined") return DEFAULT_API_URL;
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

function mapIds(obj: any, mapFn: (val: string) => string): any {
  if (obj === null || obj === undefined) return obj;
  if (typeof obj === "string") return mapFn(obj);
  if (Array.isArray(obj)) return obj.map((item) => mapIds(item, mapFn));
  if (typeof obj === "object") {
    const res: any = {};
    for (const key in obj) {
      if (Object.prototype.hasOwnProperty.call(obj, key)) {
        res[key] = mapIds(obj[key], mapFn);
      }
    }
    return res;
  }
  return obj;
}

export function mapIdsToUuids(input: string): string {
  return input.replace(/\b(p-0(0[1-9]|1[0-2]))\b/g, (match) => {
    const num = parseInt(match.substring(2), 10);
    return "20000000-0000-0000-0000-" + num.toString().padStart(12, "0");
  });
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
  opts: ApiClientOptions = {},
): Promise<T> {
  const baseUrl = opts.baseUrl || getBaseUrl();
  const normalizedBase = baseUrl.replace(/\/+$/, "");

  // Map p-001..p-012 to backend UUIDs in the request path
  const mappedPath = mapIdsToUuids(path);

  const url = `${normalizedBase}${mappedPath}`;
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

  // Map p-001..p-012 to backend UUIDs in request body
  let body = init.body;
  if (typeof body === "string") {
    body = mapIdsToUuids(body);
  }

  const response = await fetch(url, { ...init, body, headers });

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
  // Map backend UUIDs back to p-001..p-012 in response
  return mapIds(data, (val) => {
    if (val.startsWith("20000000-0000-0000-0000-")) {
      const hex = val.substring(24);
      const num = parseInt(hex, 10);
      if (num >= 1 && num <= 12) {
        return `p-${num.toString().padStart(3, "0")}`;
      }
    }
    return val;
  });
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
