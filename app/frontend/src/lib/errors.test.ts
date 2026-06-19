import { describe, expect, it } from "vitest";
import { ERRORS, getError, isChunkLoadError, type AppErrorCode } from "./errors";

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
