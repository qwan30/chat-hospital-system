/**
 * Authentication flow E2E tests — covers login page rendering, sign-in flow,
 * session persistence, auth-related pages, and unauthenticated redirect.
 *
 * Run: npx playwright test auth-flow.spec.ts --reporter=list
 */
import { expect, test } from "@playwright/test";
import { seedSession } from "./_helpers";

test.describe("Auth flow lifecycle", () => {
  test("Login page renders correctly", async ({ page }) => {
    await page.goto("/auth/login", { waitUntil: "networkidle" });
    await expect(page.locator("h2")).toContainText("Welcome back");
    await expect(page.getByRole("tab", { name: /Demo Role/i })).toBeVisible();
    const labels = page.locator("label");
    await expect(labels).toHaveCount(2);
  });

  test("Demo Role sign-in flow", async ({ page }) => {
    await page.goto("/auth/login", { waitUntil: "networkidle" });
    await page.click('button:has-text("Demo Role")');
    await page.click('button:has-text("Sign in with Hospital SSO")');
    await page.waitForURL("**/dashboard**", { timeout: 10000 });
    await expect(page.getByText("Good morning")).toBeVisible({ timeout: 5000 });
  });

  test("Session persists across navigation", async ({ page }) => {
    await seedSession(page);
    await page.goto("/patients", { waitUntil: "networkidle" });
    await expect(page.locator("table")).toBeVisible({ timeout: 5000 });
    await page.goto("/dashboard", { waitUntil: "networkidle" });
    await expect(page.getByText("Good morning")).toBeVisible({ timeout: 5000 });
  });

  test("Session expired page", async ({ page }) => {
    await seedSession(page);
    await page.goto("/auth/session-expired", { waitUntil: "networkidle" });
    await expect(page.locator("body")).toBeVisible();
  });

  test("Forgot password page", async ({ page }) => {
    await page.goto("/auth/forgot-password", { waitUntil: "networkidle" });
    await expect(page.locator("body")).toBeVisible();
  });

  test("MFA page", async ({ page }) => {
    await page.goto("/auth/mfa", { waitUntil: "networkidle" });
    await expect(page.locator("body")).toBeVisible();
  });

  test("SSO callback page", async ({ page }) => {
    await page.goto("/auth/sso/callback", { waitUntil: "networkidle" });
    await expect(page.locator("body")).toBeVisible();
  });

  test("Unauthenticated redirect", async ({ page }) => {
    await page.goto("/dashboard", { waitUntil: "networkidle" });
    await page.waitForURL("**/auth/login**", { timeout: 10000 });
    await expect(page).toHaveURL(/auth\/login/);
  });
});
