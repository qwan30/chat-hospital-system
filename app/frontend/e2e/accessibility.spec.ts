import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { seedSession } from "./_helpers";

test.describe("Accessibility Audit", () => {
  test("Main chat interface should not have any automatically detectable accessibility issues", async ({
    page,
  }) => {
    // Seed the local storage so we are "logged in"
    await seedSession(page);

    // Go to the main dashboard/chat view
    await page.goto("/");

    // Give the app a moment to render the UI
    await page.waitForLoadState("networkidle");

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .disableRules(["color-contrast"])
      .analyze();

    // Attach violations to the test report if any exist
    if (accessibilityScanResults.violations.length > 0) {
      console.log(JSON.stringify(accessibilityScanResults.violations, null, 2));
    }

    expect(accessibilityScanResults.violations).toEqual([]);
  });
});
