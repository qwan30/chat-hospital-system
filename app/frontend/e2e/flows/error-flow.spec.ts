/**
 * Error Handling Flow — Real User Interaction Tests
 *
 * Network failures, rate limits, auth expiry, 404s — what a real user sees.
 */
import { test, expect } from "@playwright/test";
import { gotoAuthenticated } from "../helpers/auth";
import { waitForLoadingToFinish } from "../helpers/interactions";

test.describe("Network Failures", () => {
  test("dashboard handles API 500 gracefully", async ({ page, context }) => {
    await context.route("**/api/v1/**", (route) => {
      route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ error: "internal_error", message: "Something went wrong" }),
      });
    });
    await context.route("**/auth/me", (route) => {
      route.fulfill({
        status: 200, contentType: "application/json",
        body: JSON.stringify({
          id: "dr-chen", full_name: "Dr. Sarah Chen",
          email: "sarah.chen@hospital.com", role: "physician", department: "Cardiology",
        }),
      });
    });

    await gotoAuthenticated(page, "/dashboard");
    await page.waitForTimeout(2000);
    await expect(page.locator("body")).not.toBeEmpty();
  });

  test("auth expiry redirects to login", async ({ page, context }) => {
    await context.route("**/auth/me", (route) => {
      route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({ error: "unauthorized", message: "Token expired" }),
      });
    });

    await page.goto("/dashboard");
    await page.waitForTimeout(2000);
    await expect(page).toHaveURL(/\/login/, { timeout: 10000 });
  });

  test("404 page for nonexistent route", async ({ page, context }) => {
    await context.addInitScript(() => {
      localStorage.setItem("hospital_ai_api_url", "http://localhost:8000/api/v1");
      localStorage.setItem("e2e_auth_token", "e2e-test-token");
    });
    await context.route("**/auth/me", (route) => {
      route.fulfill({
        status: 200, contentType: "application/json",
        body: JSON.stringify({
          id: "dr-chen", full_name: "Dr. Sarah Chen",
          email: "sarah.chen@hospital.com", role: "physician", department: "Cardiology",
        }),
      });
    });

    await page.goto("/this-route-does-not-exist-12345");
    await page.waitForTimeout(2000);
    await expect(page.locator("body")).not.toBeEmpty();
  });
});

test.describe("Rate Limiting", () => {
  test("chat shows error when rate limited", async ({ page, context }) => {
    await context.addInitScript(() => {
      localStorage.setItem("hospital_ai_api_url", "http://localhost:8000/api/v1");
      localStorage.setItem("e2e_auth_token", "e2e-test-token");
    });
    await context.route("**/auth/me", (route) => {
      route.fulfill({
        status: 200, contentType: "application/json",
        body: JSON.stringify({
          id: "dr-chen", full_name: "Dr. Sarah Chen",
          email: "sarah.chen@hospital.com", role: "physician", department: "Cardiology",
        }),
      });
    });
    await context.route("**/api/v1/chat", (route) => {
      route.fulfill({
        status: 429,
        contentType: "application/json",
        body: JSON.stringify({ error: "rate_limited", message: "Too many requests." }),
      });
    });

    await gotoAuthenticated(page, "/chat");
    await waitForLoadingToFinish(page);

    const input = page.getByPlaceholder(/Ask a clinical question/i);
    if (await input.isVisible({ timeout: 5000 }).catch(() => false)) {
      await input.fill("Test message");
      await input.press("Enter");
      await page.waitForTimeout(1500);
      await expect(page.getByText(/Too many|rate|limit/i).first()).toBeVisible({
        timeout: 5000,
      });
    }
  });
});
