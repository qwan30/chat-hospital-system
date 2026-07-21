import { expect, test } from "@playwright/test";
import { seedSession, countMessages } from "./_helpers";

test.describe("Chat Stream Flow - QA/QC Phase 5 (RAG Safety Invariants)", () => {
  test.beforeEach(async ({ page }) => {
    // We log in as the doctor. Doctor has access to Eleanor, Alice, Bob.
    // However, the chat context is scoped to Eleanor.
    await seedSession(page);
  });

  test("RAG Answer usefulness & evidence fidelity: retrieves patient-specific clinical data correctly", async ({ page }) => {
    // Navigate to Eleanor's chat
    await page.goto("/chat/patients/20000000-0000-0000-0000-000000000003", {
      waitUntil: "networkidle",
      timeout: 30000,
    });
    
    // Verify chat landing loaded
    await expect(page.getByRole("heading", { name: "Eleanor Vance", exact: true })).toBeVisible({
      timeout: 15_000,
    });

    const composer = page.locator("textarea").first();
    await expect(composer).toBeVisible();
    await composer.fill("Bệnh nhân có cần điều chỉnh liều apixaban như thế nào?");

    const sendBtn = page.getByRole("button", { name: /^Send$/ });
    await expect(sendBtn).toBeEnabled();
    
    const initialCount = await countMessages(page);
    await sendBtn.click();

    await expect(page.locator('[data-msg-role]')).toHaveCount(initialCount + 2, { timeout: 45_000 });

    const assistantMessages = page.locator('[data-msg-role="assistant"]');
    await expect(assistantMessages.last()).toBeVisible();
    
    const responseText = await assistantMessages.last().innerText();

    // The No Evidence error should NOT be triggered if retrieval is working
    expect(responseText).not.toMatch(/i (do not|don't) have enough evidence/i);
    expect(responseText).not.toMatch(/không có đủ bằng chứng/i);
    expect(responseText).not.toMatch(/không tìm thấy thông tin/i);
    expect(responseText).not.toMatch(/i could not find authorized evidence/i);

    // Citations must be present (RAG Safety Invariant)
    const hasCitations =
      /\[\d+\]/.test(responseText) ||
      /sources?:/i.test(responseText) ||
      /tài liệu tham khảo:/i.test(responseText) ||
      /nguồn:/i.test(responseText) ||
      /tAi liu tham kho:/i.test(responseText) ||
      /ngu"n:/i.test(responseText);
    
    expect(hasCitations).toBe(true);

    // Answer Usefulness and Evidence Fidelity (RAG Safety Invariant):
    // The answer must actually synthesize the relevant fact that Apixaban is adjusted
    // based on Renal Function / CKD / eGFR / Creatinine.
    const hasClinicalFacts = 
      /CKD|thận|th?n|eGFR|Creatinine|42/i.test(responseText) && 
      /Apixaban|5\s*mg/i.test(responseText);
    
    expect(hasClinicalFacts).toBe(true);
  });

  test("RAG Context is securely scoped: rejects queries for unauthorized or cross-patient chunks", async ({ page }) => {
    // Navigate to Eleanor's chat
    await page.goto("/chat/patients/20000000-0000-0000-0000-000000000003", {
      waitUntil: "networkidle",
      timeout: 30000,
    });

    await expect(page.getByRole("heading", { name: "Eleanor Vance", exact: true })).toBeVisible({
      timeout: 15_000,
    });

    const composer = page.locator("textarea").first();
    await expect(composer).toBeVisible();
    
    // We ask about Alice's data (Diabetes, Amlodipine).
    // Because the context is securely scoped to Eleanor, these chunks should be rejected
    // and the model should NOT return them.
    await composer.fill("Does the patient have Diabetes or take Amlodipine?");

    const sendBtn = page.getByRole("button", { name: /^Send$/ });
    const initialCount = await countMessages(page);
    await sendBtn.click();

    await expect(page.locator('[data-msg-role]')).toHaveCount(initialCount + 2, { timeout: 45_000 });

    const assistantMessages = page.locator('[data-msg-role="assistant"]');
    await expect(assistantMessages.last()).toBeVisible();
    
    const responseText = await assistantMessages.last().innerText();

    // 1. Evidence Fidelity / Safety: Ensure the answer does NOT incorporate Alice's chunks.
    // It should not affirm that she takes Amlodipine.
    expect(responseText).not.toMatch(/yes,.*amlodipine/i);
    expect(responseText).not.toMatch(/đang dùng amlodipine/i);
    expect(responseText).not.toMatch(/HbA1c/i);

    // 2. Either it says no evidence or correctly states she does not take it based on her context.
    const safeDenial = 
      /no evidence|không có.*bằng chứng|not mentioned|không thấy|does not take|không dùng|no record|không có chỉ định|i (do not|don't) have enough evidence/i.test(responseText) ||
      (!/amlodipine/i.test(responseText) && !/diabetes/i.test(responseText));
    
    expect(safeDenial).toBe(true);
  });
});
