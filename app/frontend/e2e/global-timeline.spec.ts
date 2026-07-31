import { test, expect } from "@playwright/test";
import { seedSession } from "./_helpers";

test.describe("Global Timeline Page", () => {
  test.beforeEach(async ({ page }) => {
    await seedSession(page);
  });

  test("loads timeline events correctly", async ({ page }) => {
    // We will intercept the API call to mock a successful response
    await page.route("**/api/v1/timeline*", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          events: [
            {
              event_id: "evt_001",
              timestamp: new Date().toISOString(),
              type: "chat",
              title: "AI Chat Created",
              body: "Doctor chatted with AI about patient.",
              patient_id: "pat_123",
              metadata: {},
            },
            {
              event_id: "evt_002",
              timestamp: new Date().toISOString(),
              type: "document",
              title: "Document Uploaded",
              body: "Lab results uploaded.",
              metadata: {},
            },
          ],
          total_count: 2,
        }),
      });
    });

    await page.goto("/timeline", { waitUntil: "networkidle" });

    // Verify page header
    await expect(page.locator("h1")).toContainText("Timeline");

    // Verify events are rendered
    await expect(page.getByText("AI Chat Created")).toBeVisible();
    await expect(page.getByText("Doctor chatted with AI about patient.")).toBeVisible();
    await expect(page.getByText("Document Uploaded")).toBeVisible();

    // Test expanding an event
    await page.getByText("AI Chat Created").click();
    await expect(page.getByText("evt_001")).toBeVisible();
    await expect(page.getByText("View Patient →")).toBeVisible();
  });

  test("handles empty state", async ({ page }) => {
    // Intercept to mock empty response
    await page.route("**/api/v1/timeline*", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          events: [],
          total_count: 0,
        }),
      });
    });

    await page.goto("/timeline", { waitUntil: "networkidle" });

    // Verify empty state message
    await expect(page.getByText("No events found.")).toBeVisible();
  });

  test("handles error state", async ({ page }) => {
    // Intercept to mock error response
    await page.route("**/api/v1/timeline*", async (route) => {
      await route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ error: "Internal Server Error" }),
      });
    });

    await page.goto("/timeline", { waitUntil: "networkidle" });

    // Verify error message
    await expect(page.getByText("Failed to load timeline events.")).toBeVisible({ timeout: 15000 });
  });
});
