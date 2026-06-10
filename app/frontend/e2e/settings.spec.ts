import { test, expect } from "@playwright/test";
import { setupContext, gotoAuthenticated } from "./helpers/auth";

test.beforeEach(async ({ context }) => { await setupContext(context); });

test.describe("Settings", () => {
  test("heading", async ({ page }) => {
    await gotoAuthenticated(page, "/settings");
    await expect(page.getByRole("heading", { name: "Settings" })).toBeVisible({ timeout: 15000 });
  });
  test("profile tab", async ({ page }) => {
    await gotoAuthenticated(page, "/settings");
    await expect(page.getByRole("tab", { name: "Profile" })).toBeVisible({ timeout: 15000 });
  });
  test("profile form", async ({ page }) => {
    await gotoAuthenticated(page, "/settings");
    await expect(page.getByRole("heading", { name: /Profile Information/i })).toBeVisible({ timeout: 15000 });
  });
  test("save button", async ({ page }) => {
    await gotoAuthenticated(page, "/settings");
    await expect(page.getByRole("button", { name: /Save Changes/i })).toBeVisible({ timeout: 15000 });
  });
});