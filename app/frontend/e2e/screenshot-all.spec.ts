/**
 * Screenshot capture script — navigates to all major pages in the HMS AI Copilot
 * and saves full-page screenshots to the screen-demo directory.
 *
 * Run: npx playwright test screenshot-all.spec.ts --reporter=list
 */
import { test, type Page } from "@playwright/test";
import path from "path";

const SCREENSHOT_DIR = "D:/projects/chatbot-hospital-system/screen-demo";
const BASE_URL = "http://localhost:8082";

async function seedSession(page: Page, role = "cardiologist", workspaceId = "ws-cardio-4n") {
  await page.addInitScript(
    ({ role, workspaceId }) => {
      localStorage.setItem("hms.session", JSON.stringify({ role, workspaceId }));
    },
    { role, workspaceId },
  );
}

async function screenshot(page: Page, name: string, url: string) {
  await page.goto(`${BASE_URL}${url}`, { waitUntil: "networkidle", timeout: 30000 });
  await page.waitForTimeout(1000);
  await page.screenshot({
    path: path.join(SCREENSHOT_DIR, `${name}.png`),
    fullPage: true,
  });
}

test.describe("Screenshot all HMS pages", () => {
  test.beforeEach(async ({ page }) => {
    await seedSession(page);
  });

  test("01-login-page", async ({ page }) => {
    await page.goto(`${BASE_URL}/auth/login`, { waitUntil: "networkidle" });
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "01-login.png"), fullPage: true });
  });

  test("02-dashboard", async ({ page }) => {
    await screenshot(page, "02-dashboard", "/dashboard");
  });

  test("03-dashboard-activity", async ({ page }) => {
    await screenshot(page, "03-dashboard-activity", "/dashboard/activity");
  });

  test("04-dashboard-customize", async ({ page }) => {
    await screenshot(page, "04-dashboard-customize", "/dashboard/customize");
  });

  test("05-patients-list", async ({ page }) => {
    await screenshot(page, "05-patients-list", "/patients");
  });

  test("06-patient-overview", async ({ page }) => {
    await page.goto(`${BASE_URL}/patients/p-001`, { waitUntil: "networkidle" });
    await page.waitForTimeout(1000);
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, "06-patient-overview.png"),
      fullPage: true,
    });
  });

  test("07-patient-timeline", async ({ page }) => {
    await screenshot(page, "07-patient-timeline", "/patients/p-001/timeline");
  });

  test("08-patient-medications", async ({ page }) => {
    await screenshot(page, "08-patient-medications", "/patients/p-001/medications");
  });

  test("09-patient-labs", async ({ page }) => {
    await screenshot(page, "09-patient-labs", "/patients/p-001/labs");
  });

  test("10-patient-documents", async ({ page }) => {
    await screenshot(page, "10-patient-documents", "/patients/p-001/documents");
  });

  test("11-patient-access-history", async ({ page }) => {
    await screenshot(page, "11-patient-access-history", "/patients/p-001/access-history");
  });

  test("12-chat-landing", async ({ page }) => {
    await screenshot(page, "12-chat-landing", "/chat");
  });

  test("13-chat-patient", async ({ page }) => {
    await screenshot(page, "13-chat-patient", "/chat/patients/p-001");
  });

  test("14-chat-general", async ({ page }) => {
    await screenshot(page, "14-chat-general", "/chat/general");
  });

  test("15-chat-history", async ({ page }) => {
    await screenshot(page, "15-chat-history", "/chat/history");
  });

  test("16-chat-templates", async ({ page }) => {
    await screenshot(page, "16-chat-templates", "/chat/templates");
  });

  test("17-documents-list", async ({ page }) => {
    await screenshot(page, "17-documents-list", "/documents");
  });

  test("18-documents-upload", async ({ page }) => {
    await screenshot(page, "18-documents-upload", "/documents/upload");
  });

  test("19-documents-search", async ({ page }) => {
    await screenshot(page, "19-documents-search", "/documents/search");
  });

  test("20-documents-ocr-queue", async ({ page }) => {
    await screenshot(page, "20-documents-ocr-queue", "/documents/ocr-queue");
  });

  test("21-audit-log", async ({ page }) => {
    await screenshot(page, "21-audit-log", "/audit");
  });

  test("22-audit-denied", async ({ page }) => {
    await screenshot(page, "22-audit-denied", "/audit/denied");
  });

  test("23-settings", async ({ page }) => {
    await screenshot(page, "23-settings", "/settings");
  });

  test("24-settings-security", async ({ page }) => {
    await screenshot(page, "24-settings-security", "/settings/security");
  });

  test("25-settings-ai", async ({ page }) => {
    await screenshot(page, "25-settings-ai", "/settings/ai");
  });

  test("26-settings-workspaces", async ({ page }) => {
    await screenshot(page, "26-settings-workspaces", "/settings/workspaces");
  });

  test("27-citations-compare", async ({ page }) => {
    await screenshot(page, "27-citations-compare", "/citations/compare");
  });

  test("28-timeline", async ({ page }) => {
    await screenshot(page, "28-timeline", "/timeline");
  });

  test("29-access-requests", async ({ page }) => {
    await screenshot(page, "29-access-requests", "/access-requests");
  });

  test("30-notifications", async ({ page }) => {
    await screenshot(page, "30-notifications", "/notifications");
  });

  test("31-help-shortcuts", async ({ page }) => {
    await screenshot(page, "31-help-shortcuts", "/help/shortcuts");
  });

  test("32-error-not-found", async ({ page }) => {
    await page.goto(`${BASE_URL}/error/not-found`, { waitUntil: "networkidle" });
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, "32-error-not-found.png"),
      fullPage: true,
    });
  });

  test("33-error-forbidden", async ({ page }) => {
    await page.goto(`${BASE_URL}/error/forbidden`, { waitUntil: "networkidle" });
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, "33-error-forbidden.png"),
      fullPage: true,
    });
  });

  test("34-error-offline", async ({ page }) => {
    await page.goto(`${BASE_URL}/error/offline`, { waitUntil: "networkidle" });
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, "34-error-offline.png"),
      fullPage: true,
    });
  });

  test("35-error-server", async ({ page }) => {
    await page.goto(`${BASE_URL}/error/server`, { waitUntil: "networkidle" });
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, "35-error-server.png"),
      fullPage: true,
    });
  });

  test("36-graph-patient", async ({ page }) => {
    await screenshot(page, "36-graph-patient", "/graph/patients/p-001");
  });

  test("37-screens-overview", async ({ page }) => {
    await screenshot(page, "37-screens-overview", "/screens");
  });
});
