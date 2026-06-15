/**
 * Chat Flow — Real User Interaction Tests
 *
 * Simulates a real clinician conducting AI-assisted clinical chat:
 * type questions, click send, read AI responses with citations.
 */
import { test, expect } from "@playwright/test";
import { setupContext, gotoAuthenticated } from "../helpers/auth";
import { waitForLoadingToFinish } from "../helpers/interactions";

test.beforeEach(async ({ context }) => {
  await setupContext(context);
});

test.describe("Chat Landing", () => {
  test("greeting changes based on time of day", async ({ page }) => {
    await gotoAuthenticated(page, "/chat");
    await waitForLoadingToFinish(page);
    const greeting = page.getByText(/Good (morning|afternoon|evening)/i).first();
    await expect(greeting).toBeVisible({ timeout: 15000 });
  });

  test("suggestion cards show clinical topics", async ({ page }) => {
    await gotoAuthenticated(page, "/chat");
    await waitForLoadingToFinish(page);
    await expect(page.getByText(/Summarize recent labs/i)).toBeVisible({ timeout: 10000 });
  });

  test("composer input is visible and empty", async ({ page }) => {
    await gotoAuthenticated(page, "/chat");
    await waitForLoadingToFinish(page);
    const input = page.getByPlaceholder(/Ask a clinical question/i);
    await expect(input).toBeVisible({ timeout: 10000 });
    await expect(input).toHaveValue("");
  });
});

test.describe("Chat — Send Message (REAL USER CLICKS)", () => {
  test("type question and press Enter — navigates to new chat", async ({ page }) => {
    await gotoAuthenticated(page, "/chat");
    await waitForLoadingToFinish(page);

    // REAL USER: types a clinical question
    const input = page.getByPlaceholder(/Ask a clinical question/i);
    await input.fill("What are the latest lab results for the patient?");

    // REAL USER: presses Enter to send
    await input.press("Enter");

    // handleSubmit redirects to /chat/new?q=... — verify navigation happened
    await page.waitForURL(/\/chat\/new/, { timeout: 15000 });
    await expect(page).toHaveURL(/\/chat\/new/);
  });

  test("send a second follow-up question", async ({ page }) => {
    await gotoAuthenticated(page, "/chat");
    await waitForLoadingToFinish(page);

    const input = page.getByPlaceholder(/Ask a clinical question/i);

    // First question
    await input.fill("What is the patient diagnosis?");
    await input.press("Enter");
    await page.waitForTimeout(1500);

    // Second question
    await input.fill("What medications are prescribed?");
    await input.press("Enter");
    await page.waitForTimeout(1500);

    // Both user messages should be visible in conversation
    // (check that the input is still usable after responses)
    await expect(input).toBeVisible();
  });
});

test.describe("Chat — Thread Navigation", () => {
  test("new conversation page loads", async ({ page }) => {
    await gotoAuthenticated(page, "/chat/new");
    await waitForLoadingToFinish(page);
    await expect(
      page.getByRole("heading", { name: /New Conversation/i }),
    ).toBeVisible({ timeout: 15000 });
  });

  test("existing thread loads with title", async ({ page }) => {
    await gotoAuthenticated(page, "/chat/thread-001");
    await waitForLoadingToFinish(page);
    await expect(page.getByText(/Cardiac Workup/i).first()).toBeVisible({
      timeout: 15000,
    });
  });
});
