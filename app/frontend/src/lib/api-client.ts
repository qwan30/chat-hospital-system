/**
 * Centralized API client with auth header injection.
 */

interface ApiClientOptions {
  apiUrl: string;
  token: string;
}

class ApiError extends Error {
  status: number;
  code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

async function apiFetch<T>(
  path: string,
  options: ApiClientOptions & RequestInit
): Promise<T> {
  const { apiUrl, token, ...init } = options;
  const url = `${apiUrl.replace(/\/+$/, "")}${path}`;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string>),
  };

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

// ── Chat API ──────────────────────────────────────────────────────

export interface ChatRequest {
  question: string;
  patient_id?: string;
  thread_id?: string;
}

export interface ChatEvidence {
  evidence_id: string;
  document_id: string;
  document_title: string;
  page: number;
  chunk_id: string;
  score: number;
  content?: string;
  metadata: Record<string, unknown>;
}

export interface ChatResponse {
  answer: string;
  citations: ChatEvidence[];
  confidence: string;
  disclaimer: string;
  thread_id?: string;
  pipeline?: string;
}

export function sendChat(opts: ApiClientOptions, body: ChatRequest): Promise<ChatResponse> {
  return apiFetch<ChatResponse>("/chat", { ...opts, method: "POST", body: JSON.stringify(body) });
}

// ── Thread API ────────────────────────────────────────────────────

export interface Thread {
  id: string;
  title: string;
  patient_id?: string;
  created_at: string;
  updated_at?: string;
  message_count?: number;
}

export interface ThreadMessage {
  id: string;
  thread_id: string;
  role: string;
  content: string;
  evidence?: ChatEvidence[];
  created_at: string;
}

export function listThreads(opts: ApiClientOptions): Promise<Thread[]> {
  return apiFetch<Thread[]>("/chat-threads", { ...opts, method: "GET" });
}

export function getThread(opts: ApiClientOptions, threadId: string): Promise<Thread> {
  return apiFetch<Thread>(`/chat-threads/${threadId}`, { ...opts, method: "GET" });
}

export function createThread(
  opts: ApiClientOptions,
  body: { title: string; patient_id?: string }
): Promise<Thread> {
  return apiFetch<Thread>("/chat-threads", { ...opts, method: "POST", body: JSON.stringify(body) });
}

export function getThreadMessages(opts: ApiClientOptions, threadId: string): Promise<ThreadMessage[]> {
  return apiFetch<ThreadMessage[]>(`/chat-threads/${threadId}/messages`, { ...opts, method: "GET" });
}

// ── Patient API ───────────────────────────────────────────────────

export interface Patient {
  id: string;
  mrn: string;
  full_name: string;
  dob: string;
  department: string;
}

interface ListEnvelope<T> {
  items: T[];
}

export function listPatients(opts: ApiClientOptions): Promise<Patient[]> {
  return apiFetch<ListEnvelope<Patient>>("/patients/search", { ...opts, method: "GET" }).then(
    (data) => data.items
  );
}

// ── Document API ──────────────────────────────────────────────────

export interface DocumentItem {
  id: string;
  patient_id: string;
  uploaded_by: string;
  title: string;
  document_type: string;
  storage_uri: string;
  mime_type: string;
  status: string;
  page_count?: number;
  ocr_error?: string;
  created_at: string;
}

export function listDocuments(opts: ApiClientOptions, patientId?: string): Promise<DocumentItem[]> {
  const params = patientId ? `?patient_id=${patientId}` : "";
  return apiFetch<ListEnvelope<DocumentItem>>(`/documents${params}`, { ...opts, method: "GET" }).then(
    (data) => data.items
  );
}

export function getDocument(opts: ApiClientOptions, documentId: string): Promise<DocumentItem> {
  return apiFetch<DocumentItem>(`/documents/${documentId}`, { ...opts, method: "GET" });
}

export function uploadDocument(
  opts: ApiClientOptions,
  body: { patient_id: string; file: File; title: string; document_type?: string }
): Promise<DocumentItem> {
  const { apiUrl, token } = opts;
  const url = `${apiUrl.replace(/\/+$/, "")}/documents`;

  const formData = new FormData();
  formData.append("patient_id", body.patient_id);
  formData.append("title", body.title);
  formData.append("document_type", body.document_type || "clinical_note");
  formData.append("file", body.file);

  return fetch(url, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  }).then((res) => {
    if (!res.ok) throw new ApiError(res.status, "UPLOAD_ERROR", "Upload failed");
    return res.json();
  });
}

// ── HMS Sync API ──────────────────────────────────────────────────

export interface HmsSyncResult {
  patient_id: string;
  synced: Record<string, number>;
  message: string;
}

export function hmsSyncFull(opts: ApiClientOptions, patientId: string): Promise<HmsSyncResult> {
  return apiFetch<HmsSyncResult>("/hms/sync/full", {
    ...opts,
    method: "POST",
    body: JSON.stringify({ patient_id: patientId }),
  });
}

export function hmsHealthCheck(opts: ApiClientOptions): Promise<{ hms_reachable: boolean; hms_url: string }> {
  return apiFetch("/hms/health", { ...opts, method: "GET" });
}

// ── Audit API ─────────────────────────────────────────────────────

export interface AuditEntry {
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

export function listAuditLogs(opts: ApiClientOptions, params?: Record<string, string>): Promise<AuditEntry[]> {
  const qs = params ? "?" + new URLSearchParams(params).toString() : "";
  return apiFetch<ListEnvelope<AuditEntry>>(`/audit/logs${qs}`, { ...opts, method: "GET" }).then(
    (data) => data.items
  );
}

// ── Metrics API ───────────────────────────────────────────────────

export interface MetricsSummary {
  total_queries: number;
  avg_latency_ms: number;
  total_time_saved_sec: number;
  total_cost_saved: number;
  helpful_rate: number;
  no_evidence_rate: number;
  audit_deny_count: number;
}

export function getMetricsSummary(opts: ApiClientOptions): Promise<MetricsSummary> {
  return apiFetch<MetricsSummary>("/feedback/metrics/summary", { ...opts, method: "GET" });
}

// ── BFF Dashboard API ──────────────────────────────────────────────

export interface RecentPatient {
  id: string;
  full_name: string;
  mrn: string;
  last_accessed?: string;
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

export interface DashboardSummary {
  recent_patients: RecentPatient[];
  document_stats: DocumentStats;
  metrics: DashboardMetrics;
  systems_health: SystemsHealth;
}

export function getDashboardSummary(opts: ApiClientOptions): Promise<DashboardSummary> {
  return apiFetch<DashboardSummary>("/dashboard/summary", { ...opts, method: "GET" });
}

// ── BFF Patient API ────────────────────────────────────────────────

export interface PatientOverview {
  patient_id: string;
  full_name: string;
  mrn: string;
  dob?: string;
  gender?: string;
  cccd?: string;
  blood_type?: string;
  occupation?: string;
  allergy_count: number;
  medication_count: number;
  lab_count: number;
  appointment_count: number;
  ai_summary?: string;
  last_updated?: string;
}

export function getPatientOverview(
  opts: ApiClientOptions,
  patientId: string
): Promise<PatientOverview> {
  return apiFetch<PatientOverview>(`/patients/${patientId}/overview`, { ...opts, method: "GET" });
}

export interface PatientTimelineEvent {
  event_id: string;
  event_type: string;
  title: string;
  description?: string;
  timestamp: string;
}

export interface PatientTimeline {
  patient_id: string;
  events: PatientTimelineEvent[];
}

export function getPatientTimeline(
  opts: ApiClientOptions,
  patientId: string
): Promise<PatientTimeline> {
  return apiFetch<PatientTimeline>(`/patients/${patientId}/timeline`, { ...opts, method: "GET" });
}

export function hmsSyncPatient(
  opts: ApiClientOptions,
  patientId: string
): Promise<HmsSyncResult> {
  return apiFetch<HmsSyncResult>(`/hms/sync/patients/${patientId}`, { ...opts, method: "POST", body: "{}" });
}

// ── BFF Global Search API ──────────────────────────────────────────

export interface SearchPatient {
  id: string;
  full_name: string;
  mrn: string;
  dob?: string;
  department?: string;
  status: string;
}

export interface SearchDocument {
  id: string;
  title: string;
  document_type: string;
  patient_id: string;
}

export interface SearchThread {
  id: string;
  title?: string;
  patient_id: string;
}

export interface GlobalSearchResult {
  patients: SearchPatient[];
  documents: SearchDocument[];
  threads: SearchThread[];
}

export function globalSearch(
  opts: ApiClientOptions,
  query: string
): Promise<GlobalSearchResult> {
  const params = new URLSearchParams({ q: query }).toString();
  return apiFetch<GlobalSearchResult>(`/search/global?${params}`, { ...opts, method: "GET" });
}

export interface AccessRequestResponse {
  message: string;
  patient_id: string;
  expires_at: string;
}

export function createAccessRequest(
  opts: ApiClientOptions,
  patientId: string,
  justification: string
): Promise<AccessRequestResponse> {
  return apiFetch<AccessRequestResponse>("/access-requests", {
    ...opts,
    method: "POST",
    body: JSON.stringify({ patient_id: patientId, justification }),
  });
}

export { ApiError };
