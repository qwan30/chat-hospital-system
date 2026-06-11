import { test, expect } from "@playwright/test";
import { setupContext } from "./helpers/auth";

test.beforeEach(async ({ context }) => { await setupContext(context); });

// === Dashboard ===
test("Dashboard heading after login", async ({ page }) => {
  await page.goto("/dashboard");
  await page.waitForTimeout(2000);
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible({ timeout: 15000 });
});
test("Dashboard KPI cards", async ({ page }) => {
  await page.goto("/dashboard");
  await page.waitForTimeout(2000);
  await expect(page.getByText("Hours Saved").first()).toBeVisible({ timeout: 15000 });
});

// === Patients ===
test("Patients heading", async ({ page }) => {
  await page.goto("/patients");
  await page.waitForTimeout(2000);
  await expect(page.getByRole("heading", { name: "Patients" })).toBeVisible({ timeout: 15000 });
});
test("Patients search input", async ({ page }) => {
  await page.goto("/patients");
  await page.waitForTimeout(2000);
  await expect(page.getByPlaceholder(/Search by name/i)).toBeVisible({ timeout: 15000 });
});
test("Patient overview tabs", async ({ page }) => {
  await page.goto("/patients/PT-0847");
  await page.waitForTimeout(2000);
  await expect(page.getByRole("tab", { name: /AI Summary/i })).toBeVisible({ timeout: 15000 });
});
test("Patient AI summary generate button", async ({ page }) => {
  await page.goto("/patients/PT-0847/summary");
  await page.waitForTimeout(2000);
  await expect(page.getByRole("button", { name: /Generate Summary/i })).toBeVisible({ timeout: 15000 });
});
test("Patient meds start review button", async ({ page }) => {
  await page.goto("/patients/PT-0847/meds");
  await page.waitForTimeout(2000);
  await expect(page.getByRole("button", { name: /Start Medication Review/i })).toBeVisible({ timeout: 15000 });
});
test("Access denied heading", async ({ page }) => {
  await page.goto("/patients/PT-0847/denied");
  await page.waitForTimeout(2000);
  await expect(page.getByRole("heading", { name: "Access Denied" })).toBeVisible({ timeout: 15000 });
});

// === Chat ===
test("Chat greeting", async ({ page }) => {
  await page.goto("/chat");
  await page.waitForTimeout(2000);
  await expect(page.getByText(/Good (morning|afternoon|evening)/i).first()).toBeVisible({ timeout: 15000 });
});
test("Chat suggestion cards", async ({ page }) => {
  await page.goto("/chat");
  await page.waitForTimeout(2000);
  await expect(page.getByText(/Summarize recent labs/i)).toBeVisible({ timeout: 15000 });
});

// === Documents ===
test("Documents heading", async ({ page }) => {
  await page.goto("/documents");
  await page.waitForTimeout(2000);
  await expect(page.getByRole("heading", { name: "Documents" })).toBeVisible({ timeout: 15000 });
});
test("Documents upload dropzone", async ({ page }) => {
  await page.goto("/documents");
  await page.waitForTimeout(2000);
  await expect(page.getByText(/Drop files here/i)).toBeVisible({ timeout: 15000 });
});
test("Documents upload page", async ({ page }) => {
  await page.goto("/documents/upload");
  await page.waitForTimeout(2000);
  await expect(page.getByRole("heading", { name: /Upload Documents/i })).toBeVisible({ timeout: 15000 });
});

// === Audit ===
test("Audit heading", async ({ page }) => {
  await page.goto("/audit");
  await page.waitForTimeout(2000);
  await expect(page.getByRole("heading", { name: "Audit Log" })).toBeVisible({ timeout: 15000 });
});
test("Audit KPI cards", async ({ page }) => {
  await page.goto("/audit");
  await page.waitForTimeout(2000);
  await expect(page.getByText("Total Events").first()).toBeVisible({ timeout: 15000 });
});

// === Metrics ===
test("Metrics heading", async ({ page }) => {
  await page.goto("/metrics");
  await page.waitForTimeout(2000);
  await expect(page.getByRole("heading", { name: /Impact & Quality/i })).toBeVisible({ timeout: 15000 });
});

// === Settings ===
test("Settings heading", async ({ page }) => {
  await page.goto("/settings");
  await page.waitForTimeout(2000);
  await expect(page.getByRole("heading", { name: "Settings" })).toBeVisible({ timeout: 15000 });
});
test("Settings profile tab", async ({ page }) => {
  await page.goto("/settings");
  await page.waitForTimeout(2000);
  await expect(page.getByRole("tab", { name: "Profile" })).toBeVisible({ timeout: 15000 });
});

// === Navigation ===
test("Sidebar nav items", async ({ page }) => {
  await page.goto("/dashboard");
  await page.waitForTimeout(2000);
  for (const item of ["Patients", "Chat", "Documents", "Audit", "Metrics", "Settings"]) {
    await expect(page.getByRole("link", { name: item })).toBeVisible({ timeout: 15000 });
  }
});
test("Topbar search trigger", async ({ page }) => {
  await page.goto("/dashboard");
  await page.waitForTimeout(2000);
  await expect(page.getByText(/Search patients, documents/i)).toBeVisible({ timeout: 15000 });
});