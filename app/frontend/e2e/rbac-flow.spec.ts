/**
 * Role-based access control E2E tests — covers all 6 roles with allowed
 * and blocked routes. Uses a table-driven approach so each role + route
 * combination is verified independently.
 *
 * Run: npx playwright test rbac-flow.spec.ts --reporter=list
 */
import { expect, test } from "@playwright/test";
import { seedSession } from "./_helpers";

type RbacCase = {
  role: string;
  workspaceId: string;
  allowed: string[];
  blocked: string[];
};

const RBAC_CASES: RbacCase[] = [
  {
    role: "cardiologist",
    workspaceId: "ws-cardio-4n",
    allowed: ["/dashboard", "/patients", "/chat", "/graph/patients/p-001"],
    blocked: ["/admin/roles"],
  },
  {
    role: "hospitalist",
    workspaceId: "ws-medicine",
    allowed: ["/dashboard", "/patients"],
    blocked: ["/admin", "/pharmacy"],
  },
  {
    role: "rn",
    workspaceId: "ws-icu-2w",
    allowed: ["/patients"],
    blocked: ["/admin/roles", "/pharmacy", "/graph/patients/p-001"],
  },
  {
    role: "pharmacist",
    workspaceId: "ws-pharmacy",
    allowed: ["/dashboard", "/patients"],
    blocked: ["/admin"],
  },
  {
    role: "front_desk",
    workspaceId: "ws-er-front",
    allowed: ["/patients"],
    blocked: ["/admin/roles", "/chat", "/graph"],
  },
  {
    role: "admin",
    workspaceId: "ws-hospital",
    allowed: ["/admin/roles", "/audit", "/access-policy", "/patients"],
    blocked: [],
  },
];

for (const { role, workspaceId, allowed, blocked } of RBAC_CASES) {
  test.describe(`RBAC: ${role}`, () => {
    test.beforeEach(async ({ page }) => {
      await seedSession(page, role, workspaceId);
    });

    for (const route of allowed) {
      test(`can access ${route}`, async ({ page }) => {
        await page.goto(route, { waitUntil: "networkidle" });
        await expect(page.locator("body")).toBeVisible();
        // Should not be redirected to login, forbidden, or error pages
        const currentUrl = page.url();
        const isBlocked =
          currentUrl.includes("/auth/login") ||
          currentUrl.includes("/error/") ||
          currentUrl.includes("/forbidden");
        expect(isBlocked).toBe(false);
      });
    }

    for (const route of blocked) {
      test(`blocked from ${route}`, async ({ page }) => {
        await page.goto(route, { waitUntil: "networkidle" });
        await page.waitForTimeout(1000);
        const currentUrl = page.url();
        const isBlocked =
          currentUrl.includes("forbidden") ||
          currentUrl.includes("error") ||
          currentUrl.includes("login");
        expect(isBlocked).toBe(true);
      });
    }
  });
}
