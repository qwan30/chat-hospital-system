import { test, expect } from "@playwright/test";
import { setupContext, gotoAuthenticated } from "../helpers/auth";

interface ClickResult {
  label: string;
  tag: string;
  visible: boolean;
  clickable: boolean;
  error?: string;
}

interface RouteReport {
  route: string;
  url: string;
  status: "pass" | "fail" | "partial";
  totalElements: number;
  clickedElements: number;
  failedClicks: number;
  consoleErrors: string[];
  pageErrors: string[];
  results: ClickResult[];
}

async function clickAllInteractive(page: any): Promise<{
  results: ClickResult[];
  consoleErrors: string[];
  pageErrors: string[];
}> {
  const results: ClickResult[] = [];
  const consoleErrors: string[] = [];
  const pageErrors: string[] = [];

  page.on("console", (msg: any) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });
  page.on("pageerror", (err: Error) => pageErrors.push(err.message));

  const selectors = [
    "button:visible",
    "a:visible[href]",
    '[role="button"]:visible',
    '[role="tab"]:visible',
    "input:visible[type='text']",
    "input:visible[type='email']",
    "input:visible[type='search']",
  ];

  for (const sel of selectors) {
    const elements = page.locator(sel);
    const count = await elements.count();
    for (let i = 0; i < count; i++) {
      const el = elements.nth(i);
      const tag =
        (await el.evaluate((e: HTMLElement) => e.tagName.toLowerCase()).catch(() => "unknown")) || "unknown";
      const label =
        (await el.textContent()?.catch(() => ""))?.trim().slice(0, 60) ||
        (await el.getAttribute("aria-label").catch(() => null)) ||
        (await el.getAttribute("title").catch(() => null)) ||
        (await el.getAttribute("placeholder").catch(() => null)) ||
        `${tag}-${i}`;
      const visible = await el.isVisible().catch(() => false);

      let clickable = true;
      let error: string | undefined;
      try {
        await el.click({ timeout: 2000, noWaitAfter: true });
        await page.waitForTimeout(200);
      } catch (e: any) {
        clickable = false;
        error = e.message?.slice(0, 100);
      }

      results.push({ label, tag, visible, clickable, error });
    }
  }

  page.removeAllListeners?.("console");
  page.removeAllListeners?.("pageerror");

  return { results, consoleErrors, pageErrors };
}

// ── PUBLIC ROUTES ──

test.describe("Click-through: Login", () => {
  test("login page", async ({ page }) => {
    await page.goto("/login");
    await page.waitForTimeout(1000);
    await page.screenshot({ path: "test-results/click-through/login.png", fullPage: true });

    const { results, consoleErrors, pageErrors } = await clickAllInteractive(page);
    const failed = results.filter((r) => !r.clickable);

    const report: RouteReport = {
      route: "/login", url: page.url(),
      status: failed.length === 0 ? "pass" : failed.length < 3 ? "partial" : "fail",
      totalElements: results.length,
      clickedElements: results.filter((r) => r.clickable).length,
      failedClicks: failed.length, consoleErrors, pageErrors, results,
    };
    console.log(JSON.stringify(report, null, 2));
    if (failed.length > 0) console.warn(`FAILED: /login`, failed.map((f) => f.label));
    expect(failed.length).toBeLessThanOrEqual(2);
  });

  test("mfa page", async ({ page }) => {
    await page.goto("/login/mfa");
    await page.waitForTimeout(1000);
    await page.screenshot({ path: "test-results/click-through/login-mfa.png", fullPage: true });

    const { results, consoleErrors, pageErrors } = await clickAllInteractive(page);
    const failed = results.filter((r) => !r.clickable);
    if (failed.length > 0) console.warn(`FAILED: /login/mfa`, failed.map((f) => f.label));
  });
});

// ── AUTHENTICATED ROUTES ──

const AUTH_ROUTES = [
  "/dashboard", "/patients", "/chat", "/chat/new",
  "/documents", "/documents/upload",
  "/audit", "/metrics", "/settings", "/timeline",
];

AUTH_ROUTES.forEach((path) => {
  const name = path.replace(/\//g, "-").replace(/^-/, "");
  test.describe(`Click-through: ${name}`, () => {
    test.beforeEach(async ({ context }) => { await setupContext(context); });

    test(name, async ({ page }) => {
      await gotoAuthenticated(page, path);
      await page.screenshot({ path: `test-results/click-through/${name}.png`, fullPage: true });

      const { results, consoleErrors, pageErrors } = await clickAllInteractive(page);
      const failed = results.filter((r) => !r.clickable);

      const report: RouteReport = {
        route: path, url: page.url(),
        status: failed.length === 0 ? "pass" : failed.length < 3 ? "partial" : "fail",
        totalElements: results.length,
        clickedElements: results.filter((r) => r.clickable).length,
        failedClicks: failed.length, consoleErrors, pageErrors, results,
      };
      console.log(JSON.stringify(report, null, 2));

      if (failed.length > 0) {
        console.warn(`\n=== FAILED on ${path} ===`);
        failed.forEach((f) => console.warn(`  "${f.label}" (${f.tag}): ${f.error || "unknown"}`));
      }
      if (consoleErrors.length > 0) {
        console.warn(`\n=== CONSOLE ERRORS on ${path} ===`);
        consoleErrors.forEach((e) => console.warn(`  ${e}`));
      }

      expect(failed.length).toBeLessThanOrEqual(3);
      expect(consoleErrors.length).toBe(0);
    });
  });
});

// ── DYNAMIC ROUTES ──

test.describe("Click-through: Dynamic Routes", () => {
  test.beforeEach(async ({ context }) => { await setupContext(context); });

  test("patient detail", async ({ page }) => {
    await gotoAuthenticated(page, "/patients/PT-0847");
    await page.screenshot({ path: "test-results/click-through/patient-detail.png", fullPage: true });
    const { results, consoleErrors } = await clickAllInteractive(page);
    const failed = results.filter((r) => !r.clickable);

    for (const tab of ["medications", "encounters"]) {
      try { await page.getByRole("tab", { name: new RegExp(tab, "i") }).click({ timeout: 2000 }); await page.waitForTimeout(500); } catch {}
    }
    if (failed.length > 0) console.warn(`FAILED: patient detail`, failed.map((f) => f.label));
    expect(consoleErrors.length).toBe(0);
  });

  test("patient denied", async ({ page }) => {
    await gotoAuthenticated(page, "/patients/PT-0847/denied");
    await page.screenshot({ path: "test-results/click-through/patient-denied.png", fullPage: true });
    const { results, consoleErrors } = await clickAllInteractive(page);
    const failed = results.filter((r) => !r.clickable);
    if (failed.length > 0) console.warn(`FAILED: denied`, failed.map((f) => f.label));
    expect(consoleErrors.length).toBe(0);
  });

  test("document detail", async ({ page }) => {
    await gotoAuthenticated(page, "/documents/doc-001");
    await page.screenshot({ path: "test-results/click-through/document-detail.png", fullPage: true });
    const { results } = await clickAllInteractive(page);
    const failed = results.filter((r) => !r.clickable);
    if (failed.length > 0) console.warn(`FAILED: document`, failed.map((f) => f.label));
  });

  test("chat thread", async ({ page }) => {
    await gotoAuthenticated(page, "/chat/test-thread");
    await page.screenshot({ path: "test-results/click-through/chat-thread.png", fullPage: true });
    const { results } = await clickAllInteractive(page);
    const failed = results.filter((r) => !r.clickable);
    if (failed.length > 0) console.warn(`FAILED: chat`, failed.map((f) => f.label));
  });
});
