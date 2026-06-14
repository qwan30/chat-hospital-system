/**
 * Centralized API client with auth header injection.
 * All frontend data access goes through this module — never call fetch() directly.
 */

export interface ApiClientOptions {
  apiUrl: string;
  token: string;
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
  options: ApiClientOptions & RequestInit
): Promise<T> {
  const { apiUrl, token, ...init } = options;
  const url = `${apiUrl.replace(/\/+$/, "")}${path}`;

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
    let errorData: { error?: string; message?: string } = {};
    try {
      errorData = await response.json();
    } catch {
      // ignore parse error
    }
    throw new ApiError(
      response.status,
      errorData.error || "UNKNOWN",
      errorData.message || response.statusText
    );
  }

  if (response.status === 204) return undefined as unknown as T;
  return response.json();
}

// ── Typed API Contracts ───────────────────────────────────────────

export interface ListEnvelope<T> {
  items: T[];
  total?: number;
}

export interface Patient {
  id: string;
  mrn: string;
  full_name: string;
  dob?: string;
  gender?: string;
  department?: string;
  status?: string;
}

export interface PatientOverview {
  patient_id: string;
  full_name: string;
  mrn: string;
  dob?: string;
  gender?: string;
  blood_type?: string;
  department?: string;
  attending_physician?: string;
  admission_status?: string;
  admitted_date?: string;
  room?: string;
  allergy_count: number;
  medication_count: number;
  lab_count: number;
  ai_summary?: string;
  last_updated?: string;
}

export interface ChatThread {
  id: string;
  title: string;
  patient_id?: string;
  created_at: string;
  updated_at?: string;
  message_count?: number;
}

export interface ChatMessage {
  id: string;
  thread_id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  confidence?: string;
  created_at: string;
}

export interface Citation {
  evidence_id: string;
  document_id: string;
  document_title: string;
  page: number;
  chunk_id: string;
  score: number;
  content?: string;
}

export interface DocumentItem {
  id: string;
  patient_id?: string;
  title: string;
  document_type: string;
  status: string;
  ocr_confidence?: number;
  page_count?: number;
  created_at: string;
}

export interface AuditEvent {
  id: string;
  actor_user_id: string;
  action: string;
  object_type: string;
  object_id?: string;
  patient_id?: string;
  outcome: string;
  trace_id: string;
  created_at: string;
}

export interface DashboardSummary {
  recent_patients: Patient[];
  document_stats: { indexed: number; processing: number; failed: number };
  metrics: { hours_saved: number; cost_saved_usd: number };
  systems_health: { hms_api: string; ollama_inference: string };
}

export interface MetricsSummary {
  total_queries: number;
  avg_latency_ms: number;
  total_time_saved_sec: number;
  total_cost_saved: number;
  helpful_rate: number;
  no_evidence_rate: number;
  audit_deny_count: number;
}

export interface GlobalSearchResult {
  patients: { id: string; full_name: string; mrn: string }[];
  documents: { id: string; title: string; document_type: string }[];
  threads: { id: string; title?: string; patient_id?: string }[];
}

// ── API Functions ─────────────────────────────────────────────────

export function getDashboardSummary(opts: ApiClientOptions): Promise<DashboardSummary> {
  return apiFetch<DashboardSummary>("/dashboard/summary", { ...opts, method: "GET" });
}

export function listPatients(opts: ApiClientOptions): Promise<Patient[]> {
  return apiFetch<ListEnvelope<Patient>>("/patients/search", { ...opts, method: "GET" })
    .then((d) => d.items);
}

export function getPatientOverview(
  opts: ApiClientOptions,
  patientId: string
): Promise<PatientOverview> {
  return apiFetch<PatientOverview>(`/patients/${patientId}/overview`, { ...opts, method: "GET" });
}

export function listThreads(opts: ApiClientOptions): Promise<ChatThread[]> {
  return apiFetch<ListEnvelope<ChatThread>>("/chat-threads", { ...opts, method: "GET" })
    .then((d) => d.items);
}

export function createThread(
  opts: ApiClientOptions,
  body: { title: string; patient_id?: string }
): Promise<ChatThread> {
  return apiFetch<ChatThread>("/chat-threads", {
    ...opts,
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function sendChatMessage(
  opts: ApiClientOptions,
  body: { question: string; patient_id?: string; thread_id?: string }
): Promise<ChatMessage> {
  return apiFetch<ChatMessage>("/chat", {
    ...opts,
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function listDocuments(
  opts: ApiClientOptions,
  params?: Record<string, string>
): Promise<DocumentItem[]> {
  const qs = params ? "?" + new URLSearchParams(params).toString() : "";
  return apiFetch<ListEnvelope<DocumentItem>>(`/documents${qs}`, { ...opts, method: "GET" })
    .then((d) => d.items);
}

export function listAuditEvents(
  opts: ApiClientOptions,
  params?: Record<string, string>
): Promise<AuditEvent[]> {
  const qs = params ? "?" + new URLSearchParams(params).toString() : "";
  return apiFetch<ListEnvelope<AuditEvent>>(`/audit/events${qs}`, { ...opts, method: "GET" })
    .then((d) => d.items);
}

export function getMetricsSummary(opts: ApiClientOptions): Promise<MetricsSummary> {
  return apiFetch<MetricsSummary>("/metrics/summary", { ...opts, method: "GET" });
}

export function globalSearch(
  opts: ApiClientOptions,
  query: string
): Promise<GlobalSearchResult> {
  const params = new URLSearchParams({ q: query }).toString();
  return apiFetch<GlobalSearchResult>(`/search/global?${params}`, { ...opts, method: "GET" });
}

export function createAccessRequest(
  opts: ApiClientOptions,
  body: {
    patient_id: string;
    resource: string;
    duration: string;
    urgency: string;
    relationship: string;
    purpose: string;
    justification: string;
  }
): Promise<{ message: string; patient_id: string; expires_at: string }> {
  return apiFetch("/access-requests", {
    ...opts,
    method: "POST",
    body: JSON.stringify(body),
  });
}
