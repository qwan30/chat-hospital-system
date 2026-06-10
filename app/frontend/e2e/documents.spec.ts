import { test, expect } from "@playwright/test";
import { setupContext, gotoAuthenticated } from "./helpers/auth";

test.beforeEach(async ({ context }) => { await setupContext(context); });

test.describe("Documents Dashboard", () => {
  test("heading", async ({ page }) => {
    await gotoAuthenticated(page, "/documents");
    await expect(page.getByRole("heading", { name: "Documents" })).toBeVisible({ timeout: 15000 });
  });
  test("upload dropzone", async ({ page }) => {
    await gotoAuthenticated(page, "/documents");
    await expect(page.getByText(/Drop files here/i)).toBeVisible({ timeout: 15000 });
  });
  test("upload button", async ({ page }) => {
    await gotoAuthenticated(page, "/documents");
    await expect(page.getByRole("button", { name: "Upload" })).toBeVisible({ timeout: 15000 });
  });
});
test.describe("Documents Upload", () => {
  test("upload page", async ({ page }) => {
    await gotoAuthenticated(page, "/documents/upload");
    await expect(page.getByRole("heading", { name: /Upload Documents/i })).toBeVisible({ timeout: 15000 });
  });
});
test.describe("Document Detail", () => {
  test("preview page", async ({ page }) => {
    await gotoAuthenticated(page, "/documents/doc-001");
    await expect(page.getByRole("heading", { name: /Admission Note/i })).toBeVisible({ timeout: 15000 });
  });
});
test.describe("OCR Review", () => {
  test("review page", async ({ page }) => {
    await gotoAuthenticated(page, "/documents/doc-001/review");
    await expect(page.getByRole("heading", { name: /OCR Review/i })).toBeVisible({ timeout: 15000 });
  });
});