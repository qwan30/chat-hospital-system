import { expect, test } from "@playwright/test";
import { seedSession } from "./_helpers";

test.describe("Chat Stream Flow - QA/QC Phase 5", () => {
  test.beforeEach(async ({ page }) => {
    await seedSession(page);
  });

  test("Vietnamese query returns citations and bypasses No Evidence block", async ({ page }) => {
    // Navigate to patient chat
    await page.goto("/chat/patients/20000000-0000-0000-0000-000000000003", {
      waitUntil: "networkidle",
      timeout: 30000,
    });
    await page.waitForTimeout(1000);

    // Verify chat landing loaded
    await expect(page.getByRole("heading", { name: "Eleanor Vance" })).toBeVisible({
      timeout: 15_000,
    });

    // Type the Vietnamese question in the composer
    const composer = page.locator("textarea").first();
    await expect(composer).toBeVisible();
    await composer.fill("Bệnh nhân cần điều chỉnh liều apixaban như thế nào?");

    // Send the message
    const sendBtn = page.getByRole("button", { name: /^Send$/ });
    await expect(sendBtn).toBeEnabled();
    await sendBtn.click();

    // Wait for the stream to start and complete (composer will be re-enabled when streaming finishes)
    await expect(composer).toBeEnabled({ timeout: 45_000 });

    // Verify the response contains substantial content
    const assistantMessages = page.locator('[data-msg-role="assistant"]');
    await expect(assistantMessages.last()).toBeVisible();

    const responseText = await assistantMessages.last().innerText();

    // 1. Assert that the No Evidence error is NO LONGER triggered
    expect(responseText).not.toContain("No Evidence");
    expect(responseText).not.toMatch(/i (do not|don't) have enough evidence/i);
    expect(responseText).not.toMatch(/không có đủ bằng chứng/i);
    expect(responseText).not.toMatch(/không tìm thấy thông tin/i);
    expect(responseText).not.toMatch(/i could not find authorized evidence/i);

    // 2. Assert that the LLM returns standard Citations
    // Check for inline citations like [1], [2], or a Sources list
    const hasCitations =
      /\[\d+\]/.test(responseText) ||
      /sources?:/i.test(responseText) ||
      /tài liệu tham khảo:/i.test(responseText) ||
      /nguồn:/i.test(responseText);

    console.log("RESPONSE TEXT:\n", responseText);

    expect(hasCitations).toBe(true);
  });
});
