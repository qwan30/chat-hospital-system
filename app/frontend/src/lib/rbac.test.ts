import { describe, expect, it } from "vitest";
import type { Role } from "./rbac";
import {
  canAccess,
  canAccessPatientTab,
  firstAllowedPatientTab,
  forbiddenReason,
  landingFor,
  PATIENT_TABS,
} from "./rbac";

describe("canAccess", () => {
  it("returns false for null or undefined role", () => {
    expect(canAccess(null, "/dashboard")).toBe(false);
    expect(canAccess(undefined, "/dashboard")).toBe(false);
  });

  it("returns true for all paths when role is admin", () => {
    const paths = [
      "/admin",
      "/dashboard",
      "/patients/42",
      "/graph",
      "/pharmacy/review-queue",
      "/settings",
      "/audit",
    ];
    for (const path of paths) {
      expect(canAccess("admin", path)).toBe(true);
    }
  });

  it("returns false for nurse (rn) trying to access admin routes", () => {
    const adminPaths = [
      "/admin",
      "/admin/users",
      "/access-policy",
      "/integrations",
      "/metrics",
      "/screens",
      "/audit/compliance-summary",
      "/audit/export",
      "/audit/denied",
    ];
    for (const path of adminPaths) {
      expect(canAccess("rn", path)).toBe(false);
    }
  });

  it("returns false for nurse trying to access graph routes (cardiologist/hospitalist only)", () => {
    expect(canAccess("rn", "/graph")).toBe(false);
    expect(canAccess("rn", "/graph/some-patient")).toBe(false);
  });

  it("returns true for public paths (/error/, /help/) regardless of role", () => {
    const roles: Role[] = [
      "cardiologist",
      "hospitalist",
      "rn",
      "pharmacist",
      "front_desk",
      "admin",
    ];
    for (const role of roles) {
      expect(canAccess(role, "/error/404")).toBe(true);
      expect(canAccess(role, "/help/faq")).toBe(true);
    }
  });

  it("returns true for pharmacist on /pharmacy/review-queue", () => {
    expect(canAccess("pharmacist", "/pharmacy/review-queue")).toBe(true);
  });
});

describe("landingFor", () => {
  it('returns "/pharmacy/review-queue" for pharmacist', () => {
    expect(landingFor("pharmacist")).toBe("/pharmacy/review-queue");
  });

  it('returns "/patients" for rn and front_desk', () => {
    expect(landingFor("rn")).toBe("/patients");
    expect(landingFor("front_desk")).toBe("/patients");
  });

  it('returns "/dashboard" for cardiologist, hospitalist, and admin', () => {
    expect(landingFor("cardiologist")).toBe("/dashboard");
    expect(landingFor("hospitalist")).toBe("/dashboard");
    expect(landingFor("admin")).toBe("/dashboard");
  });
});

describe("firstAllowedPatientTab", () => {
  it('returns "overview" for cardiologist', () => {
    expect(firstAllowedPatientTab("cardiologist")).toBe("overview");
  });

  it('returns "overview" for pharmacist', () => {
    expect(firstAllowedPatientTab("pharmacist")).toBe("overview");
  });
});

describe("canAccessPatientTab", () => {
  it("returns true for tabs included in the role's PATIENT_TABS", () => {
    expect(canAccessPatientTab("cardiologist", "overview")).toBe(true);
    expect(canAccessPatientTab("cardiologist", "timeline")).toBe(true);
    expect(canAccessPatientTab("pharmacist", "medication-review")).toBe(true);
  });

  it("returns false for tabs not included in the role's PATIENT_TABS", () => {
    expect(canAccessPatientTab("front_desk", "medications")).toBe(false);
    expect(canAccessPatientTab("rn", "labs")).toBe(false);
  });
});

describe("forbiddenReason", () => {
  it('returns "workspace-scope" for /patients/:id paths', () => {
    expect(forbiddenReason("rn", "/patients/42")).toBe("workspace-scope");
    expect(forbiddenReason("rn", "/patients/abc-123")).toBe("workspace-scope");
  });

  it('returns "role" for other paths', () => {
    expect(forbiddenReason("rn", "/admin")).toBe("role");
    expect(forbiddenReason("rn", "/graph")).toBe("role");
  });
});

describe("PATIENT_TABS", () => {
  it("cardiologist includes all 7 tabs", () => {
    expect(PATIENT_TABS.cardiologist).toEqual([
      "overview",
      "timeline",
      "labs",
      "medications",
      "documents",
      "access-history",
      "medication-review",
    ]);
  });

  it("admin also includes all 7 tabs", () => {
    expect(PATIENT_TABS.admin).toEqual([
      "overview",
      "timeline",
      "labs",
      "medications",
      "documents",
      "access-history",
      "medication-review",
    ]);
  });

  it("front_desk only has overview", () => {
    expect(PATIENT_TABS.front_desk).toEqual(["overview"]);
  });
});
