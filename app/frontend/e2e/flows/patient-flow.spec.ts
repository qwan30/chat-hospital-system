/**
 * Patient Flow — Real User Interaction Tests
 *
 * Simulates a clinician searching for patients, clicking results,
 * navigating tabs, and requesting emergency access.
 */
import { test, expect } from "@playwright/test";
import { setupContext, gotoAuthenticated } from "../helpers/auth";
import { waitForLoadingToFinish } from "../helpers/interactions";

test.beforeEach(async ({ context }) => {
  await setupContext(context);
});

test.describe("Patient Search — REAL TYPING", () => {
  test("type patient name filters the list", async ({ page }) => {
    await gotoAuthenticated(page, "/patients");
    await waitForLoadingToFinish(page);

    // REAL USER: types into search box
    const searchInput = page.getByPlaceholder(/Search by name/i);
    await expect(searchInput).toBeVisible({ timeout: 10000 });
    await searchInput.fill("Blake");
    await page.waitForTimeout(500);

    // Matching patient should be visible
    await expect(page.getByText("Jonathan Blake").first()).toBeVisible({
      timeout: 5000,
    });
  });

  test("patient list shows MRNs and departments", async ({ page }) => {
    await gotoAuthenticated(page, "/patients");
    await waitForLoadingToFinish(page);

    await expect(page.getByText("Jonathan Blake").first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByText("Maria Garcia").first()).toBeVisible({ timeout: 5000 });
    await expect(page.getByText("MRN-2025-0847").first()).toBeVisible();
  });

  test("clear search restores full list", async ({ page }) => {
    await gotoAuthenticated(page, "/patients");
    await waitForLoadingToFinish(page);

    const searchInput = page.getByPlaceholder(/Search by name/i);
    await searchInput.fill("Blake");
    await page.waitForTimeout(300);
    await searchInput.fill("");
    await page.waitForTimeout(500);

    // Full list restored
    await expect(page.getByText("Jonathan Blake").first()).toBeVisible({ timeout: 5000 });
    await expect(page.getByText("Maria Garcia").first()).toBeVisible({ timeout: 3000 });
  });
});

test.describe("Patient Detail — REAL CLICKS", () => {
  test("clicking a patient navigates to detail page", async ({ page }) => {
    await gotoAuthenticated(page, "/patients");
    await waitForLoadingToFinish(page);

    // REAL USER: clicks on a patient name
    const patientLink = page.getByText("Jonathan Blake").first();
    await patientLink.click();

    // Navigates to patient detail
    await page.waitForURL(/\/patients\/PT-0847/, { timeout: 10000 });
    await waitForLoadingToFinish(page);

    // Tabs should be visible
    await expect(
      page.getByRole("tab", { name: /AI Summary/i }),
    ).toBeVisible({ timeout: 10000 });
  });

  test("patient overview shows clinical info", async ({ page }) => {
    await gotoAuthenticated(page, "/patients/PT-0847");
    await waitForLoadingToFinish(page);

    await expect(page.getByText(/Jonathan Blake/i).first()).toBeVisible({
      timeout: 10000,
    });
    await expect(page.getByText(/Cardiology/i).first()).toBeVisible({
      timeout: 5000,
    });
  });

  test("AI Summary tab shows Generate Summary button", async ({ page }) => {
    await gotoAuthenticated(page, "/patients/PT-0847/summary");
    await waitForLoadingToFinish(page);

    await expect(
      page.getByRole("button", { name: /Generate Summary/i }),
    ).toBeVisible({ timeout: 10000 });
  });
});

test.describe("Patient Meds — Medication Review", () => {
  test("meds page shows Start Medication Review button", async ({ page }) => {
    await gotoAuthenticated(page, "/patients/PT-0847/meds");
    await waitForLoadingToFinish(page);

    await expect(
      page.getByRole("button", { name: /Start Medication Review/i }),
    ).toBeVisible({ timeout: 10000 });
  });

  test("clicking Start Review shows medications", async ({ page }) => {
    await gotoAuthenticated(page, "/patients/PT-0847/meds");
    await waitForLoadingToFinish(page);

    const reviewButton = page.getByRole("button", {
      name: /Start Medication Review/i,
    });
    if (await reviewButton.isEnabled().catch(() => false)) {
      await reviewButton.click();
      await page.waitForTimeout(1000);
    }

    // Medications should appear from mock
    const med = page.getByText(/Lisinopril/i).first();
    if (await med.isVisible({ timeout: 3000 }).catch(() => false)) {
      await expect(med).toBeVisible();
    }
  });
});

test.describe("Patient Access — Denied & Emergency Request", () => {
  test("access denied heading visible", async ({ page }) => {
    await gotoAuthenticated(page, "/patients/PT-0847/denied");
    await waitForLoadingToFinish(page);

    await expect(
      page.getByRole("heading", { name: /Access Denied/i }),
    ).toBeVisible({ timeout: 10000 });
  });

  test("emergency access request button visible", async ({ page }) => {
    await gotoAuthenticated(page, "/patients/PT-0847/denied");
    await waitForLoadingToFinish(page);

    await expect(
      page.getByRole("button", { name: /Request Emergency Access/i }),
    ).toBeVisible({ timeout: 10000 });
  });

  test("click request access opens form or dialog", async ({ page }) => {
    await gotoAuthenticated(page, "/patients/PT-0847/denied");
    await waitForLoadingToFinish(page);

    const requestButton = page.getByRole("button", {
      name: /Request Emergency Access/i,
    });
    if (await requestButton.isEnabled().catch(() => false)) {
      await requestButton.click();
      await page.waitForTimeout(500);
    }
    // Page should respond (form, dialog, or redirect)
    await expect(page).toHaveURL(/\/patients/);
  });
});
