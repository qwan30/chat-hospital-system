import { test, expect } from "@playwright/test";
import { setupContext, gotoAuthenticated } from "./helpers/auth";

test.beforeEach(async ({ context }) => { await setupContext(context); });

test.describe("Patients List", () => {
  test("heading", async ({ page }) => {
    await gotoAuthenticated(page, "/patients");
    await expect(page.getByRole("heading", { name: "Patients" })).toBeVisible({ timeout: 15000 });
  });
  test("search input", async ({ page }) => {
    await gotoAuthenticated(page, "/patients");
    await expect(page.getByPlaceholder(/Search by name/i)).toBeVisible({ timeout: 15000 });
  });
});
test.describe("Patient Overview", () => {
  test("detail with tabs", async ({ page }) => {
    await gotoAuthenticated(page, "/patients/PT-0847");
    await expect(page.getByRole("tab", { name: /AI Summary/i })).toBeVisible({ timeout: 15000 });
  });
});
test.describe("Patient AI Summary", () => {
  test("generate button", async ({ page }) => {
    await gotoAuthenticated(page, "/patients/PT-0847/summary");
    await expect(page.getByRole("button", { name: /Generate Summary/i })).toBeVisible({ timeout: 15000 });
  });
});
test.describe("Patient Meds", () => {
  test("start review button", async ({ page }) => {
    await gotoAuthenticated(page, "/patients/PT-0847/meds");
    await expect(page.getByRole("button", { name: /Start Medication Review/i })).toBeVisible({ timeout: 15000 });
  });
});
test.describe("Patient Access Denied", () => {
  test("access denied heading", async ({ page }) => {
    await gotoAuthenticated(page, "/patients/PT-0847/denied");
    await expect(page.getByRole("heading", { name: "Access Denied" })).toBeVisible({ timeout: 15000 });
  });
  test("request emergency access button", async ({ page }) => {
    await gotoAuthenticated(page, "/patients/PT-0847/denied");
    await expect(page.getByRole("button", { name: /Request Emergency Access/i })).toBeVisible({ timeout: 15000 });
  });
});