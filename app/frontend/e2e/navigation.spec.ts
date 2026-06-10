import { test, expect } from "@playwright/test";
import { setupContext, gotoAuthenticated } from "./helpers/auth";

test.beforeEach(async ({ context }) => { await setupContext(context); });

test.describe("App Shell", () => {
  test("sidebar nav items", async ({ page }) => {
    await gotoAuthenticated(page, "/dashboard");
    for (const item of ["Patients", "Chat", "Documents", "Audit", "Metrics", "Settings"]) {
      await expect(page.getByRole("link", { name: item })).toBeVisible({ timeout: 15000 });
    }
  });
  test("topbar search trigger", async ({ page }) => {
    await gotoAuthenticated(page, "/dashboard");
    await expect(page.getByText(/Search patients, documents/i)).toBeVisible({ timeout: 15000 });
  });
  test("topbar environment badge", async ({ page }) => {
    await gotoAuthenticated(page, "/dashboard");
    await expect(page.getByText(/Synthetic Data/i).first()).toBeVisible({ timeout: 15000 });
  });
});