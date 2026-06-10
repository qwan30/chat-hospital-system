import { test, expect } from "@playwright/test";
import { setupContext, gotoAuthenticated } from "./helpers/auth";

test.beforeEach(async ({ context }) => { await setupContext(context); });

test.describe("Metrics", () => {
  test("heading", async ({ page }) => {
    await gotoAuthenticated(page, "/metrics");
    await expect(page.getByRole("heading", { name: /Impact & Quality/i })).toBeVisible({ timeout: 15000 });
  });
  test("KPI cards", async ({ page }) => {
    await gotoAuthenticated(page, "/metrics");
    await expect(page.getByText("Total Queries").first()).toBeVisible({ timeout: 15000 });
  });
  test("workflow impact table", async ({ page }) => {
    await gotoAuthenticated(page, "/metrics");
    await expect(page.getByRole("heading", { name: /Workflow Impact/i })).toBeVisible({ timeout: 15000 });
  });
});