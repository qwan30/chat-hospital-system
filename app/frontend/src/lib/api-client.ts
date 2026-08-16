/**
 * Centralized API client with JWT auth header injection.
 * All frontend data access goes through this module.
 *
 * Backend base URL is configured via VITE_API_URL env var. When unset, the
 * browser uses /api and Vite rewrites that local path to /api/v1.
 */

const DEFAULT_API_URL = "/api";
const BUILD_TIME_API_URL = ((import.meta.env.VITE_API_URL as string | undefined) ?? "").trim();

function normalizeBaseUrl(url: string): string {
  return url.trim().replace(/\/+$/, "");
}

function getBuildTimeApiUrl(): string {
  return BUILD_TIME_API_URL;
}

export function resolveApiUrl(buildTimeApiUrl = BUILD_TIME_API_URL, storedApiUrl = ""): string {
  const buildTime = buildTimeApiUrl.trim();
  if (buildTime) return normalizeBaseUrl(buildTime);
  const stored = storedApiUrl.trim();
  if (stored) return normalizeBaseUrl(stored);
  return DEFAULT_API_URL;
}

export function getStoredApiUrl(): string {
  const buildTimeApiUrl = getBuildTimeApiUrl();
  if (buildTimeApiUrl) return normalizeBaseUrl(buildTimeApiUrl);
  if (typeof window === "undefined") return DEFAULT_API_URL;
  return resolveApiUrl("", localStorage.getItem("hospital_ai_api_url") || "");
}

function getBaseUrl(): string {
  return normalizeBaseUrl(getStoredApiUrl());
}

let memoryToken: string | null = null;

export function getToken(): string | null {
  if (memoryToken) return memoryToken;
  if (typeof window !== "undefined" && window.sessionStorage) {
    try {
      const stored = sessionStorage.getItem("hospital_ai_jwt");
      if (stored) {
        memoryToken = stored;
        return stored;
      }
    } catch {
      // Ignore
    }
  }
  return null;
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
  const baseUrl = normalizeBaseUrl(opts.baseUrl || getBaseUrl());

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

  const url = `${baseUrl}${mappedPath}`;
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

/** Fetch protected binary content while preserving the in-memory bearer token policy. */
export async function apiFetchBlob(path: string, opts: ApiClientOptions = {}): Promise<Blob> {
  const baseUrl = normalizeBaseUrl(opts.baseUrl || getBaseUrl());
  const token = getToken();
  const headers: Record<string, string> = {};
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(`${baseUrl}${path}`, { headers });
  if (!response.ok) {
    throw new ApiError(response.status, "BLOB_FETCH_FAILED", response.statusText);
  }
  return response.blob();
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
  if (typeof window !== "undefined" && window.sessionStorage) {
    try {
      sessionStorage.setItem("hospital_ai_jwt", token);
    } catch {
      // Ignore
    }
  }
}

export function clearToken(): void {
  memoryToken = null;
  if (typeof window !== "undefined" && window.sessionStorage) {
    try {
      sessionStorage.removeItem("hospital_ai_jwt");
    } catch {
      // Ignore
    }
  }
}

export function persistApiUrl(url: string): void {
  if (typeof window === "undefined") return;
  if (getBuildTimeApiUrl()) return;
  localStorage.setItem("hospital_ai_api_url", url);
}
