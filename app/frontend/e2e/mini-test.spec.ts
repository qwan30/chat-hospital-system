import { test, expect } from "@playwright/test";
import { setupContext } from "./helpers/auth";
test.beforeEach(async ({ context }) => { await setupContext(context); });
test("dashboard loads", async ({ page }) => {
  await page.goto("/dashboard");
  await page.waitForTimeout(3000);
  console.log("URL:", page.url());
  console.log("Title:", await page.title());
  const html = await page.content();
  console.log("Has Dashboard:", html.includes("Dashboard"));
  console.log("Has Hours Saved:", html.includes("Hours Saved"));
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible({ timeout: 5000 });
});
