import { test, expect } from "@playwright/test";
import { setupContext, gotoAuthenticated } from "./helpers/auth";

test.beforeEach(async ({ context }) => { await setupContext(context); });

test.describe("Dashboard", () => {
  test("heading after login", async ({ page }) => {
    await gotoAuthenticated(page, "/dashboard");
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible({ timeout: 15000 });
  });
  test("KPI metric cards", async ({ page }) => {
    await gotoAuthenticated(page, "/dashboard");
    await expect(page.getByText("Hours Saved").first()).toBeVisible({ timeout: 15000 });
  });
  test("system health badge", async ({ page }) => {
    await gotoAuthenticated(page, "/dashboard");
    await expect(page.getByText(/All systems operational/i)).toBeVisible({ timeout: 15000 });
  });
});