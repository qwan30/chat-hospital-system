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

const ID_KEYS = new Set(["id", "from_node", "to_node"]);

function isIdentifierKey(key: string | undefined): boolean {
  return key !== undefined && (ID_KEYS.has(key) || key.endsWith("_id"));
}

function mapApiIds(value: unknown, mapFn: (value: string) => string, key?: string): unknown {
  if (typeof value === "string") {
    return isIdentifierKey(key) ? mapFn(value) : value;
  }
  if (Array.isArray(value)) {
    return value.map((item) => mapApiIds(item, mapFn, key));
  }
  if (value !== null && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value).map(([childKey, childValue]) => [
        childKey,
        mapApiIds(childValue, mapFn, childKey),
      ]),
    );
  }
  return value;
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
  opts: ApiClientOptions = {},
): Promise<T> {
  const baseUrl = opts.baseUrl || getBaseUrl();
  const normalizedBase = baseUrl.replace(/\/+$/, "");

  // Map p-001..p-012 and ar-001..ar-099 to backend UUIDs in the request path
  const mappedPath = path
    .replace(/\b(p-0(0[1-9]|1[0-2]))\b/g, (match) => {
      const num = parseInt(match.substring(2), 10);
      return "20000000-0000-0000-0000-" + num.toString().padStart(12, "0");
    })
    .replace(/\b(ar-0(0[1-9]|[1-9][0-9]))\b/g, (match) => {
      const num = parseInt(match.substring(3), 10);
      return "90000000-0000-0000-0000-" + num.toString().padStart(12, "0");
    });

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

  // Map p-001..p-012 and ar-001..ar-099 to backend UUIDs in request body
  let body = init.body;
  if (typeof body === "string") {
    try {
      body = JSON.stringify(
        mapApiIds(JSON.parse(body), (value) =>
          value
            .replace(/\b(p-0(0[1-9]|1[0-2]))\b/g, (match) => {
              const num = parseInt(match.substring(2), 10);
              return "20000000-0000-0000-0000-" + num.toString().padStart(12, "0");
            })
            .replace(/\b(ar-0(0[1-9]|[1-9][0-9]))\b/g, (match) => {
              const num = parseInt(match.substring(3), 10);
              return "90000000-0000-0000-0000-" + num.toString().padStart(12, "0");
            }),
        ),
      );
    } catch {
      // Non-JSON bodies pass through unchanged.
    }
  }

  const response = await fetch(url, { ...init, body, headers });

  if (!response.ok) {
    let errorData: { error?: string; message?: string; detail?: any } = {};
    try {
      errorData = await response.json();
    } catch {
      // ignore parse error
    }

    let errMsg = response.statusText;
    if (errorData.message) {
      errMsg =
        typeof errorData.message === "string"
          ? errorData.message
          : JSON.stringify(errorData.message);
    } else if (errorData.detail) {
      if (typeof errorData.detail === "string") {
        errMsg = errorData.detail;
      } else if (Array.isArray(errorData.detail)) {
        try {
          errMsg = errorData.detail
            .map((err: any) => {
              const loc = err.loc
                ? err.loc
                    .filter((l: any) => l !== "body" && l !== "query" && l !== "path")
                    .join(".")
                : "";
              return loc ? `${loc}: ${err.msg}` : err.msg;
            })
            .join("; ");
        } catch {
          errMsg = JSON.stringify(errorData.detail);
        }
      } else {
        errMsg = JSON.stringify(errorData.detail);
      }
    }

    throw new ApiError(response.status, errorData.error || "UNKNOWN", errMsg);
  }

  if (response.status === 204) return undefined as unknown as T;

  const data = await response.json();
  // Map backend UUIDs back to p-001..p-012, and ar-001..ar-099 in response
  return mapApiIds(data, (val) => {
    if (val.startsWith("20000000-0000-0000-0000-")) {
      const hex = val.substring(24);
      const num = parseInt(hex, 10);
      if (num >= 1 && num <= 12) {
        return `p-${num.toString().padStart(3, "0")}`;
      }
    }
    if (val.startsWith("90000000-0000-0000-0000-")) {
      const hex = val.substring(24);
      const num = parseInt(hex, 10);
      if (num >= 1 && num <= 99) {
        return `ar-${num.toString().padStart(3, "0")}`;
      }
    }
    return val;
  }) as T;
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
