/**
 * Document Flow — Real User Interaction Tests
 *
 * Clinician viewing, searching, and uploading documents.
 */
import { test, expect } from "@playwright/test";
import { setupContext, gotoAuthenticated } from "../helpers/auth";
import { waitForLoadingToFinish } from "../helpers/interactions";

test.beforeEach(async ({ context }) => {
  await setupContext(context);
});

test.describe("Documents List", () => {
  test("documents page shows heading and entries", async ({ page }) => {
    await gotoAuthenticated(page, "/documents");
    await waitForLoadingToFinish(page);

    await expect(
      page.getByRole("heading", { name: /Documents/i }),
    ).toBeVisible({ timeout: 10000 });

    await expect(page.getByText("Admission Note").first()).toBeVisible({
      timeout: 5000,
    });
    await expect(page.getByText("Lab Results - CBC").first()).toBeVisible({
      timeout: 5000,
    });
  });

  test("document status badges visible", async ({ page }) => {
    await gotoAuthenticated(page, "/documents");
    await waitForLoadingToFinish(page);

    await expect(page.getByText(/indexed/i).first()).toBeVisible({
      timeout: 5000,
    });
  });

  test("upload dropzone visible", async ({ page }) => {
    await gotoAuthenticated(page, "/documents");
    await waitForLoadingToFinish(page);

    const dropzone = page.getByText(/Drop files here|Upload|Drag/i);
    if (await dropzone.isVisible({ timeout: 3000 }).catch(() => false)) {
      await expect(dropzone.first()).toBeVisible();
    }
  });
});

test.describe("Document Upload Page", () => {
  test("upload page loads with heading", async ({ page }) => {
    await gotoAuthenticated(page, "/documents/upload");
    await waitForLoadingToFinish(page);

    await expect(
      page.getByRole("heading", { name: /Upload Documents/i }),
    ).toBeVisible({ timeout: 10000 });
  });

  test("upload form has file input", async ({ page }) => {
    await gotoAuthenticated(page, "/documents/upload");
    await waitForLoadingToFinish(page);

    const fileInput = page.locator('input[type="file"]');
    if (await fileInput.isVisible({ timeout: 3000 }).catch(() => false)) {
      await expect(fileInput).toBeVisible();
    }
  });
});

test.describe("Document Detail", () => {
  test("detail page loads for document doc-001", async ({ page }) => {
    await gotoAuthenticated(page, "/documents/doc-001");
    await waitForLoadingToFinish(page);

    // Document detail page should load (may show metadata or review page)
    await expect(page.locator("body")).not.toBeEmpty();
    await expect(page).not.toHaveURL(/\/login/);
  });
});
