import { test, expect } from "@playwright/test";
import { seedSession } from "./_helpers";

test.describe("/chat/general — stop / retry / resume", () => {
  test.beforeEach(async ({ page }) => {
    await seedSession(page);
  });

  test("composer is disabled while initial assistant reply streams", async ({ page }) => {
    await page.goto("/chat/general");

    // The seed sets streamingId to "g2", so the Stop button is visible up-front.
    const stop = page.getByRole("button", { name: /^Stop$/ });
    await expect(stop).toBeVisible();

    const send = page.getByRole("button", { name: /^Send$/ });
    await expect(send).toBeDisabled();

    const textarea = page.getByRole("textbox");
    await expect(textarea).toBeDisabled();

    // Stop the stream and confirm the composer re-enables.
    await stop.click();
    await expect(stop).toHaveCount(0);
    await expect(textarea).toBeEnabled();
  });

  test("rapid stop clicks do not corrupt state or duplicate banners", async ({ page }) => {
    await page.goto("/chat/general");
    const stop = page.getByRole("button", { name: /^Stop$/ });
    await expect(stop).toBeVisible();

    // Fire 5 quick clicks before React can re-render.
    await Promise.all(Array.from({ length: 5 }, () => stop.click({ force: true }).catch(() => {})));

    // Exactly one interrupted banner.
    await expect(page.getByRole("alert")).toHaveCount(1);
    await expect(page.getByText(/Response interrupted at/)).toHaveCount(1);

    // Resume + Retry both rendered, exactly once each.
    await expect(page.getByRole("button", { name: /Resume/ })).toHaveCount(1);
    await expect(page.getByRole("button", { name: /Retry/ })).toHaveCount(1);
  });
});
