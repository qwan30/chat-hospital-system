import { test, expect } from "@playwright/test";

test.describe("CDSS Autonomous Agent Workflow", () => {
  test.beforeEach(async ({ page }) => {
    // Seed session for doctor
    await page.addInitScript(() => {
      localStorage.setItem("hms.session", JSON.stringify({ role: "cardiologist", workspaceId: "ws-cardio-4n", token: "dev-doctor" }));
    });
  });

  test("should display CDSS High Risk Clinical Alert in notifications", async ({ page }) => {
    // Go to notifications page
    await page.goto("/notifications", { waitUntil: "networkidle" });
    await page.waitForTimeout(1000);
    
    // Verify Page Header
    await expect(page.locator("body")).toBeVisible();
    await expect(page.getByText("Notifications").first()).toBeVisible({ timeout: 10000 });
    
    // Verify that the new CDSS alert is present
    await expect(page.getByText("High Risk Clinical Alert").first()).toBeVisible();
    await expect(page.getByText(/severe Bleeding Risk/i).first()).toBeVisible();
    
    // Verify unread filter behavior
    await page.getByRole("button", { name: "Unread" }).click();
    await page.waitForTimeout(500);
    await expect(page.getByText("High Risk Clinical Alert").first()).toBeVisible();
    
    // Click the open link
    const openLink = page.locator('a[href="/patients/p-001"]').first();
    await openLink.click();
    
    // Wait for the patient profile to load
    await page.waitForURL("**/patients/p-001**", { timeout: 10000 });
    await expect(page.locator("body")).toBeVisible();
  });
});
