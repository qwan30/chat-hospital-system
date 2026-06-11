import { test, expect } from "@playwright/test";
import { setupContext, gotoAuthenticated } from "../helpers/auth";

const PUBLIC_ROUTES = ["/login", "/login/mfa"];
const AUTH_ROUTES = ["/dashboard", "/patients", "/chat", "/chat/new", "/documents", "/documents/upload", "/audit", "/metrics", "/settings", "/timeline"];
const DYNAMIC_ROUTES = ["/patients/PT-0847", "/patients/PT-0847/denied", "/patients/PT-0847/meds", "/patients/PT-0847/summary", "/chat/test-thread", "/documents/doc-001"];

test.describe("Visual Audit", () => {
  PUBLIC_ROUTES.forEach((route) => {
    const name = route.replace(/\//g, "-").replace(/^-/, "");
    test(`screenshot: ${name}`, async ({ page }) => {
      const errors: string[] = [];
      page.on("console", (msg: any) => { if (msg.type() === "error") errors.push(msg.text()); });
      await page.goto(route);
      await page.waitForTimeout(1000);
      await page.screenshot({ path: `test-results/visual-audit/${name}.png`, fullPage: true });
      const mainButtons = page.locator("main button:visible, main a:visible[href]");
      const count = await mainButtons.count();
      let clickable = 0;
      for (let i = 0; i < Math.min(count, 5); i++) {
        try { await mainButtons.nth(i).click({ timeout: 1500, noWaitAfter: true }); clickable++; await page.waitForTimeout(150); } catch {}
      }
      console.log(`[${name}] ${clickable}/${Math.min(count, 5)} buttons clickable, ${errors.length} console errors`);
      if (errors.length > 0) console.warn(`ERRORS:`, errors.slice(0, 3));
      expect(errors.length).toBe(0);
    });
  });

  AUTH_ROUTES.forEach((route) => {
    const name = route.replace(/\//g, "-").replace(/^-/, "");
    test(`screenshot: ${name}`, async ({ context, page }) => {
      await setupContext(context);
      const errors: string[] = [];
      page.on("console", (msg: any) => { if (msg.type() === "error") errors.push(msg.text()); });
      await gotoAuthenticated(page, route);
      await page.screenshot({ path: `test-results/visual-audit/${name}.png`, fullPage: true });
      const mainButtons = page.locator("main button:visible, main a:visible[href]");
      const count = await mainButtons.count();
      let clickable = 0;
      for (let i = 0; i < Math.min(count, 5); i++) {
        try { await mainButtons.nth(i).click({ timeout: 1500, noWaitAfter: true }); clickable++; await page.waitForTimeout(150); } catch {}
      }
      console.log(`[${name}] ${clickable}/${Math.min(count, 5)} buttons clickable, ${errors.length} console errors`);
      if (errors.length > 0) console.warn(`ERRORS:`, errors.slice(0, 3));
      expect(errors.length).toBe(0);
    });
  });

  DYNAMIC_ROUTES.forEach((route) => {
    const name = route.replace(/\//g, "-").replace(/^-/, "").replace(/patients-/, "pat-").replace(/documents-/, "doc-").replace(/chat-/, "chat-");
    test(`screenshot: ${name}`, async ({ context, page }) => {
      await setupContext(context);
      const errors: string[] = [];
      page.on("console", (msg: any) => { if (msg.type() === "error") errors.push(msg.text()); });
      await gotoAuthenticated(page, route);
      await page.screenshot({ path: `test-results/visual-audit/${name}.png`, fullPage: true });
      if (errors.length > 0) console.warn(`[${name}] ERRORS:`, errors.slice(0, 3));
      expect(errors.length).toBe(0);
    });
  });
});
