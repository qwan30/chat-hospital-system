import { test, expect } from "@playwright/test";
import { seedSession } from "./_helpers";

test.describe("/chat/patients/:patientId — duplicate submits + rapid presses", () => {
  test.beforeEach(async ({ page }) => {
    await seedSession(page);
  });

  test("rapid Enter does not create duplicate messages or React key warnings", async ({ page }) => {
    const warnings: string[] = [];
    page.on("console", (msg) => {
      const t = msg.text();
      if (msg.type() === "error" && /unique "key" prop|Each child in a list/i.test(t)) {
        warnings.push(t);
      }
    });

    await page.goto("/chat/patients/p-001");
    const composer = page.locator("textarea").first();
    await expect(composer).toBeVisible({ timeout: 30000 });
    await composer.fill("Quick question about anticoagulation?");

    const before = await page.locator('[data-msg-role="user"]').count();

    // Hammer Enter — only the first should land because the composer disables
    // the moment streamingId is set.
    for (let i = 0; i < 8; i++) await composer.press("Enter", { delay: 5 });

    // Exactly one new user message appended.
    await expect(page.locator('[data-msg-role="user"]')).toHaveCount(before + 1);
    expect(warnings, warnings.join("\n")).toEqual([]);

    // The in-flight disabled state is covered by the next test; this case only
    // verifies duplicate-submit protection and React key safety.
  });

  test("Send button is blocked while a reply is in flight", async ({ page }) => {
    await page.route("**/api/v1/chat/stream", async (route) => {
      await new Promise((r) => setTimeout(r, 500));
      await route.continue();
    });
    await page.goto("/chat/patients/p-001");
    const composer = page.locator("textarea").first();
    await expect(composer).toBeVisible({ timeout: 30000 });
    const send = page.getByRole("button", { name: /^Send$/ });

    await composer.fill("First question");
    await send.click();

    // Composer empties and disables immediately.
    await expect(composer).toHaveValue("");
    await expect(composer).toBeDisabled();
    await expect(send).toBeDisabled();

    const userCount = await page.locator('[data-msg-role="user"]').count();

    // Rapid extra clicks via JS shouldn't enqueue another message.
    await send.click({ force: true }).catch(() => {});
    await send.click({ force: true }).catch(() => {});
    await expect(page.locator('[data-msg-role="user"]')).toHaveCount(userCount);
  });

  test("simulate=stream-fail surfaces Resume + Retry and rapid presses are idempotent", async ({
    page,
  }) => {
    await page.goto("/chat/patients/p-001?simulate=stream-fail");
    const composer = page.locator("textarea").first();
    await expect(composer).toBeVisible({ timeout: 30000 });
    await composer.fill("Trigger forced failure");
    await page.getByRole("button", { name: /^Send$/ }).click();

    // Interruption banner appears.
    const banner = page.getByText(/Response interrupted at/);
    await expect(banner).toBeVisible({ timeout: 5_000 });

    const retry = page.getByRole("button", { name: /Retry/ });
    // Mash Retry — at most one banner / one streaming controls row should be visible at any time.
    await Promise.all(
      Array.from({ length: 6 }, () => retry.click({ force: true }).catch(() => {})),
    );
    await expect(page.getByRole("alert")).toHaveCount(1, { timeout: 5_000 });
  });
});
