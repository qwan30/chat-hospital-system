import { Page, expect } from "@playwright/test";

/**
 * Shared interaction utilities for real-user E2E tests.
 * These simulate how a real clinician would interact with the system:
 * clicking, typing, waiting for responses, and verifying behavior.
 *
 * Called by: login-flow.spec.ts, chat-flow.spec.ts, patient-flow.spec.ts,
 *            document-upload-flow.spec.ts, navigation-flow.spec.ts, and others.
 */

const DEFAULT_TIMEOUT = 15000;

/** Wait for all loading spinners and skeletons to disappear */
export async function waitForLoadingToFinish(page: Page, timeout = DEFAULT_TIMEOUT) {
  await page.waitForLoadState("networkidle", { timeout });
  const spinner = page.locator('[role="progressbar"], .MuiCircularProgress-root, .animate-spin');
  if (await spinner.count() > 0) {
    await spinner.first().waitFor({ state: "hidden", timeout }).catch(() => {});
  }
}

/** Assert a toast/snackbar notification is visible with given text */
export async function assertToast(page: Page, text: string | RegExp, timeout = DEFAULT_TIMEOUT) {
  const toast = page.locator('[role="alert"], .MuiSnackbar-root, .toast, [data-testid="toast"]');
  await expect(toast.filter({ hasText: text }).first()).toBeVisible({ timeout });
}

/** Assert an error message is visible */
export async function assertError(page: Page, text: string | RegExp, timeout = DEFAULT_TIMEOUT) {
  const error = page.locator('[role="alert"], .MuiAlert-standardError, .text-red-600, .text-destructive');
  await expect(error.filter({ hasText: text }).first()).toBeVisible({ timeout });
}

/** Click an element and wait for any resulting navigation or network idle */
export async function clickAndWait(page: Page, selector: string, timeout = DEFAULT_TIMEOUT) {
  await page.click(selector);
  await page.waitForLoadState("networkidle", { timeout }).catch(() => {});
}

/** Fill an input and press Enter (how real users often submit search) */
export async function typeAndSubmit(
  page: Page,
  placeholder: string | RegExp,
  text: string,
) {
  const input = page.getByPlaceholder(placeholder);
  await input.fill(text);
  await input.press("Enter");
  await page.waitForTimeout(500);
}

/** Fill a form field by its label */
export async function fillField(page: Page, label: string | RegExp, value: string) {
  const field = page.getByLabel(label);
  await field.fill(value);
}

/** Assert the current URL contains the given path */
export async function assertUrlContains(page: Page, path: string) {
  await expect(page).toHaveURL(new RegExp(path));
}

/** Assert a heading is visible */
export async function assertHeading(page: Page, text: string | RegExp, timeout = DEFAULT_TIMEOUT) {
  await expect(page.getByRole("heading", { name: text }).first()).toBeVisible({ timeout });
}

/** Assert a button is visible and enabled */
export async function assertButtonEnabled(page: Page, name: string | RegExp, timeout = DEFAULT_TIMEOUT) {
  const btn = page.getByRole("button", { name });
  await expect(btn).toBeVisible({ timeout });
  await expect(btn).toBeEnabled({ timeout });
}

/** Assert a button is visible but disabled */
export async function assertButtonDisabled(page: Page, name: string | RegExp, timeout = DEFAULT_TIMEOUT) {
  const btn = page.getByRole("button", { name });
  await expect(btn).toBeVisible({ timeout });
  await expect(btn).toBeDisabled({ timeout });
}

/** Navigate via sidebar link — exactly like a user clicking the sidebar */
export async function navigateViaSidebar(page: Page, linkName: string, timeout = DEFAULT_TIMEOUT) {
  const sidebar = page.locator("nav, aside, [data-testid='sidebar']").first();
  const link = sidebar.getByRole("link", { name: linkName });
  await link.click();
  await page.waitForLoadState("networkidle", { timeout }).catch(() => {});
  await page.waitForTimeout(500);
}

/** Wait for a chat/AI response to appear (streaming may take several seconds) */
export async function waitForAiResponse(page: Page, timeout = 30000) {
  await page.waitForTimeout(2000);
  const response = page.locator('[data-role="assistant"], .assistant-message, .ai-response').first();
  await expect(response).toBeVisible({ timeout });
}
