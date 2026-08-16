export type ErrorTone = "info" | "warning" | "critical";

export type AppErrorCode =
  | "unauthenticated"
  | "session-expired"
  | "mfa-required"
  | "forbidden"
  | "workspace-scope"
  | "break-glass-required"
  | "patient-not-found"
  | "document-not-found"
  | "route-not-found"
  | "gone"
  | "invalid-input"
  | "insufficient-evidence"
  | "ocr-failed"
  | "conflict"
  | "rate-limit"
  | "quota-exceeded"
  | "unknown"
  | "llm-offline"
  | "hms-unreachable"
  | "timeout"
  | "partial-degraded"
  | "offline"
  | "chunk-load-failure"
  | "clock-skew"
  | "maintenance";

export interface AppErrorMeta {
  code: AppErrorCode;
  http: number;
  title: string;
  description: string;
  tone: ErrorTone;
  cta?: { label: string; to: string };
  auditEvent: string;
}

export const ERRORS: Record<AppErrorCode, AppErrorMeta> = {
  unauthenticated: {
    code: "unauthenticated",
    http: 401,
    tone: "info",
    title: "Authentication required",
    description:
      "Your session is missing or invalid. Sign in again to continue — your draft is preserved.",
    cta: { label: "Sign in", to: "/auth/login" },
    auditEvent: "auth.unauthenticated",
  },
  "session-expired": {
    code: "session-expired",
    http: 401,
    tone: "info",
    title: "Session expired",
    description:
      "You were signed out after a period of inactivity to protect PHI. Sign in to resume.",
    cta: { label: "Sign in", to: "/auth/login" },
    auditEvent: "auth.session_expired",
  },
  "mfa-required": {
    code: "mfa-required",
    http: 401,
    tone: "info",
    title: "Multi-factor verification required",
    description:
      "This action is gated by step-up MFA. Verify with your authenticator app to continue.",
    cta: { label: "Verify MFA", to: "/auth/mfa" },
    auditEvent: "auth.mfa_required",
  },
  forbidden: {
    code: "forbidden",
    http: 403,
    tone: "warning",
    title: "You don't have permission for this resource",
    description:
      "Your current role can't access this page. Switch role from the avatar menu or request access.",
    cta: { label: "Request access", to: "/access-requests" },
    auditEvent: "rbac.forbidden",
  },
  "workspace-scope": {
    code: "workspace-scope",
    http: 403,
    tone: "warning",
    title: "Out of workspace scope",
    description:
      "This patient or resource belongs to another workspace. Switch workspace to continue.",
    cta: { label: "Switch workspace", to: "/settings/workspaces" },
    auditEvent: "rbac.workspace_scope",
  },
  "break-glass-required": {
    code: "break-glass-required",
    http: 403,
    tone: "critical",
    title: "Break-glass access required",
    description:
      "Emergency access is needed to view this record. All access will be audited and reviewed.",
    auditEvent: "rbac.break_glass_required",
  },
  "patient-not-found": {
    code: "patient-not-found",
    http: 404,
    tone: "info",
    title: "Patient not found",
    description:
      "This MRN is missing from cache or no longer in your scope. Try a sync or search again.",
    cta: { label: "Back to patients", to: "/patients" },
    auditEvent: "resource.patient_not_found",
  },
  "document-not-found": {
    code: "document-not-found",
    http: 404,
    tone: "info",
    title: "Document not found",
    description: "This document was removed, archived, or is outside your access scope.",
    cta: { label: "Back to documents", to: "/documents" },
    auditEvent: "resource.document_not_found",
  },
  "route-not-found": {
    code: "route-not-found",
    http: 404,
    tone: "info",
    title: "Page not found",
    description: "The page you're looking for doesn't exist or has been moved.",
    cta: { label: "Back to dashboard", to: "/dashboard" },
    auditEvent: "resource.route_not_found",
  },
  gone: {
    code: "gone",
    http: 410,
    tone: "warning",
    title: "This resource is no longer available",
    description: "It has been permanently removed in accordance with retention policy.",
    cta: { label: "Back to dashboard", to: "/dashboard" },
    auditEvent: "resource.gone",
  },
  "invalid-input": {
    code: "invalid-input",
    http: 400,
    tone: "warning",
    title: "Invalid input",
    description:
      "Some required fields are missing or malformed. Review the highlighted fields and try again.",
    auditEvent: "validation.invalid_input",
  },
  "insufficient-evidence": {
    code: "insufficient-evidence",
    http: 422,
    tone: "warning",
    title: "Insufficient evidence to answer",
    description: "Retrieval could not surface citations of high enough relevance to answer safely.",
    cta: { label: "Upload document", to: "/documents/upload" },
    auditEvent: "ai.insufficient_evidence",
  },
  "ocr-failed": {
    code: "ocr-failed",
    http: 422,
    tone: "warning",
    title: "OCR processing failed",
    description: "The scan is too low contrast or rotated to extract structured fields.",
    cta: { label: "Open OCR queue", to: "/documents/ocr-queue" },
    auditEvent: "doc.ocr_failed",
  },
  conflict: {
    code: "conflict",
    http: 409,
    tone: "warning",
    title: "This record has changed",
    description:
      "Someone else updated this record while you were editing. Reload to see the latest version.",
    cta: { label: "Reload latest", to: "" },
    auditEvent: "data.conflict",
  },
  "rate-limit": {
    code: "rate-limit",
    http: 429,
    tone: "warning",
    title: "Too many queries",
    description:
      "You've exceeded the per-user query rate limit (60/min). Slow down or batch your queries.",
    auditEvent: "quota.rate_limit",
  },
  "quota-exceeded": {
    code: "quota-exceeded",
    http: 429,
    tone: "warning",
    title: "Daily quota reached",
    description: "Your workspace AI quota has been exhausted for today. Quota resets at 00:00 UTC.",
    auditEvent: "quota.exceeded",
  },
  unknown: {
    code: "unknown",
    http: 500,
    tone: "critical",
    title: "Something went wrong",
    description: "An unexpected error occurred. The incident has been logged for review.",
    cta: { label: "Back to dashboard", to: "/dashboard" },
    auditEvent: "runtime.unknown",
  },
  "llm-offline": {
    code: "llm-offline",
    http: 503,
    tone: "critical",
    title: "LLM runtime is unavailable",
    description:
      "The local Ollama runtime is restarting after a model swap. Your drafts are preserved.",
    cta: { label: "View LLM health", to: "/integrations/llm" },
    auditEvent: "runtime.llm_offline",
  },
  "hms-unreachable": {
    code: "hms-unreachable",
    http: 503,
    tone: "critical",
    title: "HMS integration unreachable",
    description: "We can't reach the hospital management system. Synced data may be stale.",
    cta: { label: "View HMS health", to: "/integrations/hms" },
    auditEvent: "runtime.hms_unreachable",
  },
  timeout: {
    code: "timeout",
    http: 504,
    tone: "warning",
    title: "Request timed out",
    description:
      "The operation took too long to complete. Retry, or open the trace to inspect what happened.",
    cta: { label: "Back to dashboard", to: "/dashboard" },
    auditEvent: "runtime.timeout",
  },
  "partial-degraded": {
    code: "partial-degraded",
    http: 200,
    tone: "warning",
    title: "Running in degraded mode",
    description: "One or more subsystems are slow. We're showing cached data where possible.",
    auditEvent: "runtime.degraded",
  },
  offline: {
    code: "offline",
    http: 0,
    tone: "warning",
    title: "You're offline",
    description:
      "We can't reach the network. Your draft is preserved locally — actions will resume when you're back online.",
    auditEvent: "client.offline",
  },
  "chunk-load-failure": {
    code: "chunk-load-failure",
    http: 0,
    tone: "warning",
    title: "A newer version is available",
    description:
      "Part of the app failed to load because it was updated. Reload to get the latest version.",
    auditEvent: "client.chunk_load_failure",
  },
  "clock-skew": {
    code: "clock-skew",
    http: 0,
    tone: "info",
    title: "System clock is out of sync",
    description:
      "Your device clock differs from the server by more than 2 minutes. Some audit timestamps may be off.",
    auditEvent: "client.clock_skew",
  },
  maintenance: {
    code: "maintenance",
    http: 503,
    tone: "info",
    title: "Scheduled maintenance in progress",
    description:
      "We're performing planned maintenance. Read-only mode is available. Estimated restore: 30 min.",
    auditEvent: "runtime.maintenance",
  },
};

export function getError(code: AppErrorCode): AppErrorMeta {
  return ERRORS[code] ?? ERRORS["unknown"];
}

/** Detect dynamic-chunk load failures (post-deploy) by message heuristics. */
export function isChunkLoadError(err: unknown): boolean {
  if (!err) return false;
  const msg = (err as Error)?.message ?? String(err);
  return /chunk|Loading\s+(?:chunk|CSS)|dynamically imported module/i.test(msg);
}

/**
 * Safely extracts a human-readable message from an unknown error object.
 * Prevents raw JSON, HTML, or backend stack traces from leaking to the UI.
 */
export function sanitizeError(error: unknown, fallback = "An unexpected error occurred."): string {
  if (!error) return fallback;

  let rawMessage = "";
  if (error instanceof Error) {
    rawMessage = error.message;
  } else if (typeof error === "string") {
    rawMessage = error;
  } else {
    return fallback;
  }

  // Check for JSON
  try {
    JSON.parse(rawMessage);
    return fallback;
  } catch {
    // Not valid JSON, which is good
  }

  // Check for HTML tags or stack trace hints
  if (
    rawMessage.includes("<html") ||
    rawMessage.includes("</") ||
    rawMessage.includes("at Object.") ||
    rawMessage.includes("    at ") ||
    rawMessage.includes("processTicksAndRejections")
  ) {
    return fallback;
  }

  return rawMessage;
}
