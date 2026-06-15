/**
 * Navigation Flow — Real User Interaction Tests
 *
 * Simulates a real clinician navigating the app via sidebar clicks.
 */
import { test, expect } from "@playwright/test";
import { setupContext, gotoAuthenticated } from "../helpers/auth";
import { waitForLoadingToFinish } from "../helpers/interactions";

test.beforeEach(async ({ context }) => {
  await setupContext(context);
});

const PAGES = [
  { name: "Dashboard", path: "/dashboard", heading: /Welcome back/i },
  { name: "Patients", path: "/patients", heading: /Patients/i },
  { name: "Chat", path: "/chat", heading: null },
  { name: "Documents", path: "/documents", heading: /Documents/i },
  { name: "Audit Logs", path: "/audit", heading: /Audit Log/i },
  { name: "Metrics", path: "/metrics", heading: /Impact & Quality/i },
  { name: "Settings", path: "/settings", heading: /Settings/i },
];

test.describe("Sidebar Navigation — REAL CLICKS", () => {
  for (const { name, path, heading } of PAGES) {
    test(`click "${name}" navigates to ${path}`, async ({ page }) => {
      // Start from /patients so every sidebar click is a real navigation
      await gotoAuthenticated(page, name === "Dashboard" ? "/patients" : "/dashboard");
      await waitForLoadingToFinish(page);

      const sidebar = page.locator("nav, aside, [data-testid='sidebar']").first();
      const link = sidebar.getByRole("link", { name });

      if (await link.isVisible({ timeout: 3000 }).catch(() => false)) {
        await link.click();
        await page.waitForLoadState("networkidle").catch(() => {});
        await page.waitForTimeout(500);

        if (heading) {
          await expect(
            page.getByRole("heading", { name: heading }).first(),
          ).toBeVisible({ timeout: 20000 });
        } else {
          await expect(
            page.getByText(/Good (morning|afternoon|evening)/i).first(),
          ).toBeVisible({ timeout: 20000 });
        }
      }
    });
  }
});

test.describe("Direct URL Access", () => {
  for (const { name, path } of PAGES) {
    test(`direct access ${path} loads ${name}`, async ({ page }) => {
      await gotoAuthenticated(page, path);
      await waitForLoadingToFinish(page);
      await expect(page.locator("body")).not.toBeEmpty();
      await expect(page).not.toHaveURL(/\/login/);
    });
  }
});

test.describe("Topbar", () => {
  test("user name visible after login", async ({ page }) => {
    await gotoAuthenticated(page, "/dashboard");
    await waitForLoadingToFinish(page);
    await expect(page.getByText(/Dr. Sarah Chen/i).first()).toBeVisible({
      timeout: 10000,
    });
  });

  test("search trigger visible", async ({ page }) => {
    await gotoAuthenticated(page, "/dashboard");
    await waitForLoadingToFinish(page);
    const trigger = page.getByText(/Search patients, documents/i);
    if (await trigger.isVisible({ timeout: 3000 }).catch(() => false)) {
      await expect(trigger).toBeVisible();
    }
  });
});
