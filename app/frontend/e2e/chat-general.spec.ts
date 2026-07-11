import { expect, test } from "@playwright/test";
import { seedSession } from "./_helpers";

test.describe("/chat/general stream lifecycle", () => {
  test.beforeEach(async ({ page }) => {
    await seedSession(page);
  });

  test("composer re-enables after a sent reply completes", async ({ page }) => {
    await page.route("**/api/v1/chat/stream", async (route) => {
      await new Promise((r) => setTimeout(r, 500));
      await route.continue();
    });
    await page.goto("/chat/general");
    await expect(page.getByRole("heading", { name: "General clinical chat" })).toBeVisible({
      timeout: 15_000,
    });

    const send = page.getByRole("button", { name: /^Send$/ });
    const textarea = page.locator("textarea").first();
    await expect(textarea).toBeEnabled({ timeout: 15_000 });

    const before = await page.locator('[data-msg-role="user"]').count();
    await textarea.fill("Summarize high level heart failure medication monitoring.");
    await send.click();

    await expect(page.locator('[data-msg-role="user"]')).toHaveCount(before + 1);
    await expect(textarea).toBeDisabled();
    await expect(textarea).toBeEnabled({ timeout: 10_000 });
  });

  test("forced interruption renders one retry/resume alert", async ({ page }) => {
    // Intercept the stream and mock a failure halfway through
    await page.route("**/api/v1/chat/stream", async (route) => {
      const headers = { "Content-Type": "text/event-stream" };
      const response = await route.fetch();

      route.fulfill({
        headers,
        status: 200,
        body: 'data: {"type":"token","content":"This is a "}\n\ndata: {"type":"token","content":"simulated "}\n\ndata: {"type":"error","message":"Simulated stream failure"}\n\n',
      });
    });

    await page.goto("/chat/general");
    await expect(page.getByRole("heading", { name: "General clinical chat" })).toBeVisible({
      timeout: 15_000,
    });

    const composer = page.locator("textarea").first();
    await composer.fill("Trigger forced failure");
    await page.getByRole("button", { name: /^Send$/ }).click();

    await expect(page.getByRole("alert")).toHaveCount(1, { timeout: 20_000 });
    await expect(page.getByText(/Response interrupted at/)).toHaveCount(1);
    await expect(page.getByRole("button", { name: /Resume/ })).toHaveCount(1);
    await expect(page.getByRole("button", { name: /Retry/ })).toHaveCount(1);
  });
});
