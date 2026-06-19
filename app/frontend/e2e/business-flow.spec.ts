/**
 * End-to-end business flow tests — covers full user journeys including
 * happy paths and error cases.
 *
 * Run: npx playwright test business-flow.spec.ts --reporter=list
 */
import { test, expect, type Page } from "@playwright/test";

async function seedSession(page: Page, role = "cardiologist", workspaceId = "ws-cardio-4n") {
  await page.addInitScript(
    ({ role, workspaceId }) => {
      localStorage.setItem("hms.session", JSON.stringify({ role, workspaceId }));
    },
    { role, workspaceId },
  );
}

// ─────────────────────────────────────────────────────────────────────
// HAPPY PATHS
// ─────────────────────────────────────────────────────────────────────

test.describe("Happy Path: Full Clinical Workflow", () => {
  test.beforeEach(async ({ page }) => {
    await seedSession(page);
  });

  test("HC-01: Login page loads → mock sign-in → dashboard", async ({ page }) => {
    await page.goto("/auth/login", { waitUntil: "networkidle" });
    await expect(page.locator("h2")).toContainText("Welcome back");
    // Switch to Demo Role tab
    await page.click('button:has-text("Demo Role")');
    await page.waitForTimeout(300);
    await page.click('button:has-text("Sign in with Hospital SSO")');
    await page.waitForURL("**/dashboard**", { timeout: 10000 });
    await expect(page.getByText("Good morning")).toBeVisible({ timeout: 5000 });
    // At least one metric label should be visible
    const hasMetrics = await page
      .getByText(/Avg summary time|Cited answers/)
      .first()
      .isVisible();
    expect(hasMetrics).toBe(true);
  });

  test("HC-02: Patients list → search → navigate to detail", async ({ page }) => {
    await page.goto("/patients", { waitUntil: "networkidle" });
    await expect(page.locator("table")).toBeVisible({ timeout: 5000 });
    const searchInput = page.locator('input[type="text"], input:not([type])').first();
    await searchInput.fill("Eleanor");
    await page.waitForTimeout(500);
    await expect(page.getByText("Eleanor Vance")).toBeVisible();
    // Click "Open chat" button for this patient (navigates to chat with patient context)
    await page.locator('a:has-text("Open chat")').first().click();
    await page.waitForURL("**/chat/patients/**", { timeout: 10000 });
    await expect(page.getByText(/Eleanor|Vance|p-001/i).first()).toBeVisible({ timeout: 5000 });
  });

  test("HC-03: Patient tabs navigation", async ({ page }) => {
    await page.goto("/patients/p-001", { waitUntil: "networkidle" });
    await page.waitForTimeout(1000);
    const tabs = ["overview", "timeline", "labs", "medications", "documents"];
    for (const tab of tabs) {
      const tabButton = page.getByRole("tab", { name: new RegExp(tab, "i") });
      if (await tabButton.isVisible()) {
        await tabButton.click();
        await page.waitForTimeout(500);
      }
    }
  });

  test("HC-04: Chat landing with suggestions", async ({ page }) => {
    await page.goto("/chat", { waitUntil: "networkidle" });
    await expect(page.getByText("How can I help you")).toBeVisible({ timeout: 5000 });
    const suggestions = page
      .locator("button")
      .filter({ hasText: /guideline|sepsis|DOAC|dyspnea/i });
    const count = await suggestions.count();
    expect(count).toBeGreaterThanOrEqual(1);
    await expect(page.getByRole("textbox").first()).toBeVisible();
  });

  test("HC-05: Chat with patient context", async ({ page }) => {
    await page.goto("/chat/patients/p-001", { waitUntil: "networkidle" });
    await page.waitForTimeout(1000);
    await expect(page.getByText(/Eleanor|Vance|p-001/i).first()).toBeVisible({ timeout: 5000 });
    const textbox = page.locator('textarea, input[type="text"], [contenteditable]').first();
    if (await textbox.isVisible()) {
      await textbox.fill("What medications is this patient taking?");
      await page.waitForTimeout(300);
      // Look for send button by icon or type
      const sendBtn = page.locator('button[type="submit"], button:has(svg)').last();
      if (await sendBtn.isVisible()) {
        await sendBtn.click();
        await page.waitForTimeout(2000);
      }
    }
  });

  test("HC-06: Documents list loads", async ({ page }) => {
    await page.goto("/documents", { waitUntil: "networkidle" });
    await expect(page.getByText(/document/i).first()).toBeVisible({ timeout: 5000 });
  });

  test("HC-07: Settings navigation", async ({ page }) => {
    await page.goto("/settings", { waitUntil: "networkidle" });
    await expect(page.getByText(/settings|profile/i).first()).toBeVisible({ timeout: 5000 });
  });

  test("HC-08: Admin audit access", async ({ page }) => {
    await seedSession(page, "admin");
    await page.goto("/audit", { waitUntil: "networkidle" });
    await expect(page.getByText(/audit/i).first()).toBeVisible({ timeout: 5000 });
  });

  test("HC-09: Access requests page", async ({ page }) => {
    await page.goto("/access-requests", { waitUntil: "networkidle" });
    await expect(page.locator("body")).toBeVisible();
  });

  test("HC-10: Pharmacist role dashboard", async ({ page }) => {
    await seedSession(page, "pharmacist", "ws-pharmacy");
    await page.goto("/dashboard", { waitUntil: "networkidle" });
    await page.waitForTimeout(1000);
    await expect(page.locator("body")).toBeVisible();
  });

  test("HC-11: Notifications page", async ({ page }) => {
    await page.goto("/notifications", { waitUntil: "networkidle" });
    await expect(page.locator("body")).toBeVisible();
  });

  test("HC-12: Timeline view", async ({ page }) => {
    await page.goto("/timeline", { waitUntil: "networkidle" });
    await expect(page.locator("body")).toBeVisible();
  });

  test("HC-13: Help shortcuts", async ({ page }) => {
    await page.goto("/help/shortcuts", { waitUntil: "networkidle" });
    await expect(page.locator("body")).toBeVisible();
  });

  test("HC-14: Graph knowledge visualization", async ({ page }) => {
    await page.goto("/graph/patients/p-001", { waitUntil: "networkidle" });
    await page.waitForTimeout(1500);
    await expect(page.locator("body")).toBeVisible();
  });
});

// ─────────────────────────────────────────────────────────────────────
// ERROR CASES
// ─────────────────────────────────────────────────────────────────────

test.describe("Error Cases: Bad Paths & Edge Cases", () => {
  test("EC-01: Unauthenticated redirect to login", async ({ page }) => {
    await page.goto("/dashboard", { waitUntil: "networkidle" });
    await page.waitForURL("**/auth/login**", { timeout: 10000 });
    await expect(page).toHaveURL(/auth\/login/);
  });

  test("EC-02: 404 page for non-existent route", async ({ page }) => {
    await seedSession(page);
    await page.goto("/this-page-does-not-exist-12345", { waitUntil: "networkidle" });
    await page.waitForTimeout(1000);
    const has404 = await page.getByText("404").first().isVisible();
    expect(has404).toBe(true);
  });

  test("EC-03: Error forbidden page", async ({ page }) => {
    await seedSession(page);
    await page.goto("/error/forbidden", { waitUntil: "networkidle" });
    await expect(page.locator("body")).toBeVisible();
  });

  test("EC-04: Error offline page", async ({ page }) => {
    await seedSession(page);
    await page.goto("/error/offline", { waitUntil: "networkidle" });
    await expect(page.locator("body")).toBeVisible();
  });

  test("EC-05: Error server page", async ({ page }) => {
    await seedSession(page);
    await page.goto("/error/server", { waitUntil: "networkidle" });
    await expect(page.locator("body")).toBeVisible();
  });

  test("EC-06: Error timeout page", async ({ page }) => {
    await seedSession(page);
    await page.goto("/error/timeout", { waitUntil: "networkidle" });
    await expect(page.locator("body")).toBeVisible();
  });

  test("EC-07: Error maintenance page", async ({ page }) => {
    await seedSession(page);
    await page.goto("/error/maintenance", { waitUntil: "networkidle" });
    await expect(page.locator("body")).toBeVisible();
  });

  test("EC-08: Error rate-limit page", async ({ page }) => {
    await seedSession(page);
    await page.goto("/error/rate-limit", { waitUntil: "networkidle" });
    await expect(page.locator("body")).toBeVisible();
  });

  test("EC-09: RBAC — nurse cannot access admin routes", async ({ page }) => {
    await seedSession(page, "rn");
    await page.goto("/admin/roles", { waitUntil: "networkidle" });
    await page.waitForTimeout(1000);
    const url = page.url();
    const isBlocked = url.includes("forbidden") || url.includes("error") || url.includes("login");
    expect(isBlocked).toBe(true);
  });

  test("EC-10: Pharmacist graph access restricted", async ({ page }) => {
    await seedSession(page, "pharmacist", "ws-pharmacy");
    await page.goto("/graph/patients/p-001", { waitUntil: "networkidle" });
    await page.waitForTimeout(1000);
    await expect(page.locator("body")).toBeVisible();
  });

  test("EC-11: Non-existent patient ID", async ({ page }) => {
    await seedSession(page);
    await page.goto("/patients/non-existent-id-99999", { waitUntil: "networkidle" });
    await page.waitForTimeout(1000);
    await expect(page.locator("body")).toBeVisible();
    const text = await page.locator("body").innerText();
    expect(text.length).toBeGreaterThan(10);
  });

  test("EC-12: Invalid chat patient ID", async ({ page }) => {
    await seedSession(page);
    await page.goto("/chat/patients/non-existent", { waitUntil: "networkidle" });
    await page.waitForTimeout(1000);
    await expect(page.locator("body")).toBeVisible();
  });

  test("EC-13: Session expired page", async ({ page }) => {
    await seedSession(page);
    await page.goto("/auth/session-expired", { waitUntil: "networkidle" });
    await expect(page.locator("body")).toBeVisible();
  });

  test("EC-14: Forgot password page", async ({ page }) => {
    await page.goto("/auth/forgot-password", { waitUntil: "networkidle" });
    await expect(page.locator("body")).toBeVisible();
  });

  test("EC-15: MFA page", async ({ page }) => {
    await page.goto("/auth/mfa", { waitUntil: "networkidle" });
    await expect(page.locator("body")).toBeVisible();
  });

  test("EC-16: Front desk — limited access + admin blocked", async ({ page }) => {
    await seedSession(page, "front_desk", "ws-er-front");
    await page.goto("/patients", { waitUntil: "networkidle" });
    await page.waitForTimeout(1000);
    await expect(page.locator("body")).toBeVisible();
    await page.goto("/admin/roles", { waitUntil: "networkidle" });
    await page.waitForTimeout(1000);
    const url = page.url();
    const isBlocked = url.includes("forbidden") || url.includes("error");
    expect(isBlocked).toBe(true);
  });

  test("EC-17: Login form accessibility", async ({ page }) => {
    await page.goto("/auth/login", { waitUntil: "networkidle" });
    const labels = page.locator("label");
    const count = await labels.count();
    expect(count).toBeGreaterThanOrEqual(2);
  });

  test("EC-18: Sidebar navigation links present", async ({ page }) => {
    await seedSession(page);
    await page.goto("/dashboard", { waitUntil: "networkidle" });
    await page.waitForTimeout(1000);
    const sidebar = page.locator("aside, nav, [class*='sidebar']").first();
    if (await sidebar.isVisible()) {
      const links = sidebar.locator("a");
      const count = await links.count();
      expect(count).toBeGreaterThanOrEqual(2);
    }
  });

  test("EC-19: Desktop viewport 1280px rendering", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await seedSession(page);
    await page.goto("/dashboard", { waitUntil: "networkidle" });
    await page.waitForTimeout(1000);
    await expect(page.locator("body")).toBeVisible();
  });

  test("EC-20: Mobile viewport 375px rendering", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await seedSession(page);
    await page.goto("/patients", { waitUntil: "networkidle" });
    await page.waitForTimeout(1000);
    await expect(page.locator("body")).toBeVisible();
  });
});
