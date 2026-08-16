import { describe, expect, it } from "vitest";
import { ERRORS, getError, isChunkLoadError, sanitizeError, type AppErrorCode } from "./errors";

// ---------------------------------------------------------------------------
// getError
// ---------------------------------------------------------------------------
describe("getError", () => {
  it("returns the correct AppErrorMeta for a known error code", () => {
    const meta = getError("forbidden");

    expect(meta.code).toBe("forbidden");
    expect(meta.http).toBe(403);
    expect(meta.tone).toBe("warning");
    expect(meta.title).toBe("You don't have permission for this resource");
    expect(meta.description).toBeTruthy();
    expect(meta.auditEvent).toBe("rbac.forbidden");
    expect(meta.cta).toBeDefined();
    expect(meta.cta!.label).toBe("Request access");
    expect(meta.cta!.to).toBe("/access-requests");
  });

  it("falls back to 'unknown' for an invalid error code", () => {
    const meta = getError("nonexistent" as AppErrorCode);

    expect(meta.code).toBe("unknown");
    expect(meta.http).toBe(500);
    expect(meta.tone).toBe("critical");
  });
});

// ---------------------------------------------------------------------------
// isChunkLoadError
// ---------------------------------------------------------------------------
describe("isChunkLoadError", () => {
  it("returns true for chunk loading error messages", () => {
    expect(isChunkLoadError(new Error("Loading chunk 123 failed"))).toBe(true);
    expect(isChunkLoadError(new Error("Loading CSS chunk styles.css"))).toBe(true);
    expect(isChunkLoadError(new Error("dynamically imported module"))).toBe(true);
    expect(isChunkLoadError("Loading chunk failed")).toBe(true);
  });

  it("returns false for unrelated errors", () => {
    expect(isChunkLoadError(new Error("Network error"))).toBe(false);
    expect(isChunkLoadError("random string")).toBe(false);
    expect(isChunkLoadError(null)).toBe(false);
    expect(isChunkLoadError(undefined)).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// sanitizeError
// ---------------------------------------------------------------------------
describe("sanitizeError", () => {
  it("returns human readable error for simple strings and Errors", () => {
    expect(sanitizeError(new Error("Network offline"))).toBe("Network offline");
    expect(sanitizeError("Something bad happened")).toBe("Something bad happened");
  });

  it("returns fallback for raw JSON strings", () => {
    expect(sanitizeError('{"error": "bad request"}')).toBe("An unexpected error occurred.");
    expect(sanitizeError(new Error('{"error": "bad request"}'))).toBe(
      "An unexpected error occurred.",
    );
  });

  it("returns fallback for stack traces and HTML", () => {
    expect(sanitizeError("<html><body>Error</body></html>")).toBe("An unexpected error occurred.");
    expect(
      sanitizeError(
        "TypeError: Cannot read properties of null\n    at Object.<anonymous> (/app/index.js:10:15)",
      ),
    ).toBe("An unexpected error occurred.");
    expect(
      sanitizeError(
        new Error("Error at processTicksAndRejections (node:internal/process/task_queues:95:5)"),
      ),
    ).toBe("An unexpected error occurred.");
  });

  it("returns fallback for falsy or unexpected types", () => {
    expect(sanitizeError(null)).toBe("An unexpected error occurred.");
    expect(sanitizeError(undefined)).toBe("An unexpected error occurred.");
    expect(sanitizeError(123)).toBe("An unexpected error occurred.");
    expect(sanitizeError({ code: 500 })).toBe("An unexpected error occurred.");
  });
});

// ---------------------------------------------------------------------------
// Data integrity — all error codes
// ---------------------------------------------------------------------------
describe("ERRORS data integrity", () => {
  it("all entries have a valid AppErrorMeta shape", () => {
    const entries = Object.entries(ERRORS);

    for (const [code, meta] of entries) {
      expect(meta.code).toBe(code);
      expect(typeof meta.http).toBe("number");
      expect(meta.http).toBeGreaterThanOrEqual(0);
      expect(["info", "warning", "critical"]).toContain(meta.tone);
      expect(meta.title).toBeTruthy();
      expect(meta.description).toBeTruthy();
      expect(meta.auditEvent).toBeTruthy();
    }
  });

  it("all audit events are unique", () => {
    const entries = Object.entries(ERRORS);
    const auditEvents = entries.map(([, meta]) => meta.auditEvent);
    const unique = new Set(auditEvents);

    expect(unique.size).toBe(entries.length);
  });

  it("every error code with a CTA has a valid path", () => {
    const entries = Object.entries(ERRORS);

    for (const [, meta] of entries) {
      if (meta.cta) {
        // Path must start with "/" or be empty (reload-latest)
        expect(meta.cta.to.startsWith("/") || meta.cta.to === "").toBe(true);
        expect(meta.cta.label).toBeTruthy();
      }
    }
  });
});
