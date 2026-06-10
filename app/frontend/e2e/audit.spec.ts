import { test, expect } from "@playwright/test";
import { setupContext, gotoAuthenticated } from "./helpers/auth";

test.beforeEach(async ({ context }) => { await setupContext(context); });

test.describe("Audit", () => {
  test("heading", async ({ page }) => {
    await gotoAuthenticated(page, "/audit");
    await expect(page.getByRole("heading", { name: "Audit Log" })).toBeVisible({ timeout: 15000 });
  });
  test("KPI cards", async ({ page }) => {
    await gotoAuthenticated(page, "/audit");
    await expect(page.getByText("Total Events").first()).toBeVisible({ timeout: 15000 });
    await expect(page.getByText("Access Granted").first()).toBeVisible();
  });
  test("event log table", async ({ page }) => {
    await gotoAuthenticated(page, "/audit");
    await expect(page.getByRole("heading", { name: /Event Log/i })).toBeVisible({ timeout: 15000 });
  });
});