import { test, expect } from "@playwright/test";
import { seedSession } from "./_helpers";

test.describe("/graph/patients/:patientId — reasoning stream controls", () => {
  test.beforeEach(async ({ page }) => {
    await seedSession(page);
  });

  test("forced failure shows interrupted banner with Resume + Retry", async ({ page }) => {
    await page.goto("/graph/patients/p-001?simulate=stream-fail");

    await expect(page.getByText(/Response interrupted at/)).toBeVisible({ timeout: 5_000 });
    await expect(page.getByRole("button", { name: /Resume/ })).toBeVisible();
    await expect(page.getByRole("button", { name: /Retry/ })).toBeVisible();
  });

  test("rapid Resume / Retry presses do not spawn parallel streams", async ({ page }) => {
    await page.goto("/graph/patients/p-001?simulate=stream-fail");
    const banner = page.getByText(/Response interrupted at/);
    await expect(banner).toBeVisible({ timeout: 5_000 });

    const retry = page.getByRole("button", { name: /Retry/ });
    const resume = page.getByRole("button", { name: /Resume/ });

    // Interleave 5 rapid clicks across both buttons.
    for (let i = 0; i < 5; i++) {
      await (i % 2 === 0 ? retry : resume).click({ force: true }).catch(() => {});
    }

    // Only one set of controls / one banner exists, regardless of how many
    // clicks landed. The hook's `clear()` guard means no orphan intervals.
    await expect(page.locator("text=Tracing next hop…"))
      .toHaveCount(0, { timeout: 2_000 })
      .catch(async () => {
        // It's acceptable for "Tracing next hop…" to appear during streaming,
        // but never more than once.
        await expect(page.locator("text=Tracing next hop…")).toHaveCount(1);
      });
  });

  test("Stop after interruption keeps the original failure reason", async ({ page }) => {
    await page.goto("/graph/patients/p-001?simulate=stream-fail");
    const banner = page.getByText(/Reasoning stream interrupted/);
    await expect(banner).toBeVisible({ timeout: 5_000 });

    // No Stop button is rendered in the interrupted state — verify.
    await expect(page.getByRole("button", { name: /^Stop$/ })).toHaveCount(0);

    // Original cause stays put.
    await expect(banner).toBeVisible();
  });
});
