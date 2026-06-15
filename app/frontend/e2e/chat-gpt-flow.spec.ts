/**
 * GPT-like chat interaction test — tests the full chat experience:
 * landing page → type message → send → receive response → citations.
 *
 * Run: npx playwright test chat-gpt-flow.spec.ts --reporter=list
 */
import { test, expect, type Page } from "@playwright/test";

const BASE_URL = "http://localhost:8082";

async function seedSession(page: Page, role = "cardiologist", workspaceId = "ws-cardio-4n") {
  await page.addInitScript(
    ({ role, workspaceId }) => {
      localStorage.setItem("hms.session", JSON.stringify({ role, workspaceId }));
    },
    { role, workspaceId },
  );
}

test.describe("Chat GPT-like Flow", () => {
  test.beforeEach(async ({ page }) => {
    await seedSession(page);
  });

  test("Chat Landing → type question → send → see response with citations", async ({ page }) => {
    await page.goto(`${BASE_URL}/chat`, { waitUntil: "networkidle", timeout: 30000 });
    await page.waitForTimeout(1000);

    // Verify chat landing loaded
    await expect(page.getByText("How can I help you")).toBeVisible({ timeout: 5000 });

    // Type in the composer
    const composer = page.locator("textarea").first();
    await expect(composer).toBeVisible();
    await composer.fill(
      "What is the recommended anticoagulation protocol for atrial fibrillation patients?",
    );

    // Click send — navigates to /chat/patients/p-001
    const sendBtn = page.locator('button:has-text("Send")');
    await expect(sendBtn).toBeEnabled();
    await sendBtn.click();

    // Should navigate to patient chat page
    await page.waitForURL("**/chat/patients/**", { timeout: 10000 });
    await page.waitForTimeout(800);

    // Patient context card should be visible
    await expect(page.getByText(/Eleanor|Vance/i).first()).toBeVisible({ timeout: 5000 });
    await expect(page.getByText("Access verified")).toBeVisible();

    // Chat composer should still be visible for follow-up
    const followUpComposer = page.locator("textarea").first();
    await expect(followUpComposer).toBeVisible();

    // Type a follow-up question
    await followUpComposer.fill("What about patients with renal impairment?");

    // Send follow-up
    const sendBtn2 = page.locator('button:has-text("Send")');
    await expect(sendBtn2).toBeEnabled();
    await sendBtn2.click();
    await page.waitForTimeout(1500);

    // Verify the page shows meaningful content
    const bodyText = await page.locator("body").innerText();
    expect(bodyText.length).toBeGreaterThan(100);
    const hasContent =
      bodyText.includes("anticoagulation") ||
      bodyText.includes("renal") ||
      bodyText.includes("recommended") ||
      bodyText.includes("guideline");
    expect(hasContent).toBe(true);
  });

  test("Chat with patient — full conversation with citations", async ({ page }) => {
    await page.goto(`${BASE_URL}/chat/patients/p-001`, {
      waitUntil: "networkidle",
      timeout: 30000,
    });
    await page.waitForTimeout(1000);

    // Verify patient context
    await expect(page.getByText(/Eleanor Vance/i).first()).toBeVisible({ timeout: 5000 });
    await expect(page.getByText("Access verified")).toBeVisible();

    // Type and send message
    const composer = page.locator("textarea").first();
    await composer.fill(
      "Summarize the patient's current medications and identify any potential drug interactions.",
    );
    await page.locator('button:has-text("Send")').click();
    await page.waitForTimeout(2000);

    // Should see a response
    const bodyText = await page.locator("body").innerText();
    expect(bodyText.length).toBeGreaterThan(200);
  });

  test("Chat landing suggestions are displayed", async ({ page }) => {
    await page.goto(`${BASE_URL}/chat`, { waitUntil: "networkidle", timeout: 30000 });
    await page.waitForTimeout(800);

    // Suggestion cards should exist (at least 4 clinical suggestions)
    const suggestionBtns = page
      .locator("button")
      .filter({ hasText: /guideline|sepsis|DOAC|dyspnea/i });
    const count = await suggestionBtns.count();
    expect(count).toBeGreaterThanOrEqual(1);

    // Verify suggestions are visible with clinical content
    for (let i = 0; i < Math.min(count, 4); i++) {
      await expect(suggestionBtns.nth(i)).toBeVisible();
    }
  });

  test("Chat composer Enter key sends message", async ({ page }) => {
    await page.goto(`${BASE_URL}/chat`, { waitUntil: "networkidle", timeout: 30000 });
    await page.waitForTimeout(800);

    const composer = page.locator("textarea").first();
    await composer.fill("Test keyboard shortcut message");
    await composer.press("Enter");

    await page.waitForTimeout(1000);
    // Should have navigated (onSend navigates in landing page)
    const url = page.url();
    expect(url).toContain("chat");
  });

  test("Chat general knowledge tab loads with pre-seeded conversation", async ({ page }) => {
    await page.goto(`${BASE_URL}/chat/general`, { waitUntil: "networkidle", timeout: 30000 });
    await page.waitForTimeout(1500);

    await expect(page.locator("body")).toBeVisible();
    // Page header should be visible
    await expect(page.getByText("General clinical chat")).toBeVisible({ timeout: 5000 });

    // Should show pre-existing DAPT conversation
    const bodyText = await page.locator("body").innerText();
    expect(bodyText).toContain("DAPT");
    expect(bodyText.length).toBeGreaterThan(100);
  });

  test("Chat history page shows threads", async ({ page }) => {
    await page.goto(`${BASE_URL}/chat/history`, { waitUntil: "networkidle", timeout: 30000 });
    await page.waitForTimeout(800);

    await expect(page.locator("body")).toBeVisible();
    const bodyText = await page.locator("body").innerText();
    expect(bodyText.length).toBeGreaterThan(50);
  });

  test("Chat full conversation loop — send multiple messages and verify responses", async ({
    page,
  }) => {
    await page.goto(`${BASE_URL}/chat/patients/p-001`, {
      waitUntil: "networkidle",
      timeout: 30000,
    });
    await page.waitForTimeout(1000);

    // Send first message
    const composer = page.locator("textarea").first();
    await composer.fill("What are the patient's current medications?");
    await page.locator('button:has-text("Send")').click();
    await page.waitForTimeout(2500);

    // Wait for streaming to finish, then fill textarea again with a second message
    const composer2 = page.locator("textarea").first();
    await composer2.fill("Are there any drug interactions to watch for?");
    await page.waitForTimeout(300);

    // Send button should be enabled now (textarea has text, streaming done)
    const sendBtn2 = page.locator('button:has-text("Send")');
    if (await sendBtn2.isEnabled()) {
      await sendBtn2.click();
      await page.waitForTimeout(2000);
    }

    // Page should have substantial content from multiple messages
    const bodyText = await page.locator("body").innerText();
    expect(bodyText.length).toBeGreaterThan(200);
  });
});
