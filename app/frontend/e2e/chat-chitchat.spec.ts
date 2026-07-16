import { test, expect } from "@playwright/test";
import { seedSession } from "./_helpers";

test.describe("Chat functionality - greetings and valid question mapping", () => {
  test.beforeEach(async ({ page }) => {
    // login user 
    await seedSession(page);
  });

  test("Should correctly map patient id p-001 and answer normal clinical question", async ({ page }) => {
    await page.goto("/chat/patients/p-001");
    const composer = page.locator("textarea").first();
    await expect(composer).toBeVisible({ timeout: 30000 });
    const send = page.getByRole("button", { name: /^Send$/ });

    await composer.fill("What is the recent diagnosis for this patient?");
    await send.click();
    
    // Expect AI response bubble
    await expect(page.locator('[data-msg-role="assistant"]')).toHaveCount(1, { timeout: 20000 });
  });

  test("Should handle 'hello' chitchat on general chat", async ({ page }) => {
    await page.goto("/chat/general");
    const composer = page.locator("textarea").first();
    await expect(composer).toBeVisible({ timeout: 30000 });
    const send = page.getByRole("button", { name: /^Send$/ });

    await composer.fill("hello");
    await send.click();

    // The StubLLM should return a friendly greeting instead of "no evidence"
    const assistantBubble = page.locator('[data-msg-role="assistant"]').last();
    await expect(assistantBubble).toContainText(/Xin chào|Copilot/i, { timeout: 20000 });
  });

  test("Should handle 'cảm ơn' chitchat on patient chat", async ({ page }) => {
    await page.goto("/chat/patients/p-001");
    const composer = page.locator("textarea").first();
    await expect(composer).toBeVisible({ timeout: 30000 });
    const send = page.getByRole("button", { name: /^Send$/ });

    await composer.fill("cảm ơn");
    await send.click();

    const assistantBubble = page.locator('[data-msg-role="assistant"]').last();
    await expect(assistantBubble).toContainText(/Không có gì/i, { timeout: 20000 });
  });
});
