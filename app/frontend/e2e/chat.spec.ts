import { test, expect } from "@playwright/test";
import { setupContext, gotoAuthenticated } from "./helpers/auth";

test.beforeEach(async ({ context }) => { await setupContext(context); });

test.describe("Chat Landing", () => {
  test("greeting", async ({ page }) => {
    await gotoAuthenticated(page, "/chat");
    await expect(page.getByText(/Good morning/i).first()).toBeVisible({ timeout: 15000 });
  });
  test("suggestion cards", async ({ page }) => {
    await gotoAuthenticated(page, "/chat");
    await expect(page.getByText(/Summarize recent labs/i)).toBeVisible({ timeout: 15000 });
  });
  test("composer input", async ({ page }) => {
    await gotoAuthenticated(page, "/chat");
    await expect(page.getByPlaceholder(/Ask a clinical question/i)).toBeVisible({ timeout: 15000 });
  });
});
test.describe("Chat New Thread", () => {
  test("new conversation heading", async ({ page }) => {
    await gotoAuthenticated(page, "/chat/new");
    await expect(page.getByRole("heading", { name: /New Conversation/i })).toBeVisible({ timeout: 15000 });
  });
});
test.describe("Chat Thread", () => {
  test("thread messages", async ({ page }) => {
    await gotoAuthenticated(page, "/chat/thread-001");
    await expect(page.getByRole("heading", { name: /Cardiac Workup/i })).toBeVisible({ timeout: 15000 });
  });
});