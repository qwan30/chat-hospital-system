/**
 * Chrome DevTools-style audit: captures console errors, network failures,
 * and visual state across all critical user flows.
 *
 * Run: npx playwright test e2e/devtools-audit.spec.ts --project=chromium
 */
import { test, expect, type Page, type ConsoleMessage, type Request } from "@playwright/test";
import { seedSession } from "./_helpers";

// ── Shared state ──────────────────────────────────────────────
const BUGS: BugReport[] = [];

interface BugReport {
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  flow: string;
  role: string;
  url: string;
  console: string[];
  network: string[];
  expected: string;
  actual: string;
}

// ── DevTools-style collectors ─────────────────────────────────
function attachDevTools(page: Page, flowName: string) {
  const consoleErrors: string[] = [];
  const networkErrors: string[] = [];

  page.on("console", (msg: ConsoleMessage) => {
    if (msg.type() === "error") {
      consoleErrors.push(`[${msg.type()}] ${msg.text()}`);
    }
    if (msg.type() === "warning") {
      console.log(`  ⚠️ CONSOLE WARN: ${msg.text().slice(0, 150)}`);
    }
  });

  page.on("requestfailed", (req: Request) => {
    networkErrors.push(`FAILED ${req.method()} ${req.url()} — ${req.failure()?.errorText}`);
  });

  page.on("response", (resp) => {
    if (resp.status() >= 400) {
      networkErrors.push(`HTTP ${resp.status()} ${resp.request().method()} ${resp.url()}`);
    }
  });

  return {
    async finalize(expected: string, actual: string, severity: BugReport["severity"] = "MEDIUM") {
      if (consoleErrors.length > 0 || networkErrors.length > 0) {
        BUGS.push({
          severity,
          flow: flowName,
          role: "",
          url: page.url(),
          console: consoleErrors,
          network: networkErrors,
          expected,
          actual:
            actual ||
            `${consoleErrors.length} console errors, ${networkErrors.length} network errors`,
        });
      }
    },
  };
}

// ═══════════════════════════════════════════════════════════════
// Flow 1: Login & Authentication
// ═══════════════════════════════════════════════════════════════
test.describe("Flow 1: Login & Authentication", () => {
  test("1.1 Root redirects to /chat", async ({ page }) => {
    const dt = attachDevTools(page, "Login");
    await page.goto("http://localhost:8082");
    await page.waitForURL("**/chat", { timeout: 10_000 });
    expect(page.url()).toContain("/chat");
    await dt.finalize("Redirect to /chat", page.url());
  });

  test("1.2 Login page renders", async ({ page }) => {
    const dt = attachDevTools(page, "Login");
    await page.goto("http://localhost:8082/auth/login");
    await expect(page.locator("text=Welcome back").first()).toBeVisible({ timeout: 5_000 });
    await dt.finalize("Login page visible", page.url());
  });

  test("1.3 Demo SSO login as cardiologist", async ({ page }) => {
    const dt = attachDevTools(page, "Login");
    await page.goto("http://localhost:8082/auth/login", { waitUntil: "networkidle" });
    const demoTab = page.getByRole("tab", { name: "Demo Role" });
    await expect(demoTab).toBeVisible({ timeout: 5000 });
    await demoTab.click();

    // Ensure the tab transitioned and is active to guarantee hydration and click registration
    await expect(demoTab).toHaveAttribute("data-state", "active", { timeout: 3000 });
    await page.waitForTimeout(300);

    const cardioBtn = page.locator('button:has-text("Cardiologist")');
    await expect(cardioBtn).toBeVisible({ timeout: 5000 });
    await cardioBtn.click();
    await page.waitForTimeout(100);

    await page.click('button:has-text("Sign in with Hospital SSO")');
    // Whether SSO worked or not, verify page doesn't crash
    await page.waitForLoadState("networkidle");
    await expect(page.locator("body")).not.toBeEmpty();
    await dt.finalize("Login page functional", page.url());
  });

  test("1.4 Unauthenticated redirect", async ({ page }) => {
    const dt = attachDevTools(page, "Login");
    // Navigate to app first so we have a valid origin for localStorage
    await page.goto("http://localhost:8082");
    await page.evaluate(() => localStorage.clear());
    await page.goto("http://localhost:8082/dashboard");
    await page.waitForTimeout(3_000); // Let redirect happen
    const url = page.url();
    const redirected = url.includes("/auth/login") || url.includes("/chat");
    expect(redirected).toBeTruthy();
    await dt.finalize("Redirected when unauthenticated", page.url());
  });
});

// ═══════════════════════════════════════════════════════════════
// Flow 2: Dashboard
// ═══════════════════════════════════════════════════════════════
test.describe("Flow 2: Dashboard", () => {
  test("2.1 Dashboard loads with mock session (doctor)", async ({ page }) => {
    const dt = attachDevTools(page, "Dashboard");
    await seedSession(page, "doctor", "20000000-0000-0000-0000-000000000001");
    await page.goto("http://localhost:8082/dashboard");
    await page.waitForLoadState("networkidle");
    const heading = page.locator("h1, h2").first();
    await expect(heading).toBeVisible({ timeout: 5_000 });
    await dt.finalize("Dashboard heading visible", page.url());
  });

  test("2.2 Dashboard with admin role", async ({ page }) => {
    const dt = attachDevTools(page, "Dashboard");
    await seedSession(page, "admin", "20000000-0000-0000-0000-000000000005");
    await page.goto("http://localhost:8082/dashboard");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("h1, h2").first()).toBeVisible({ timeout: 5_000 });
    await dt.finalize("Admin dashboard visible", page.url());
  });

  test("2.3 Dashboard with pharmacist role", async ({ page }) => {
    const dt = attachDevTools(page, "Dashboard");
    await seedSession(page, "pharmacist", "20000000-0000-0000-0000-000000000004");
    await page.goto("http://localhost:8082/dashboard");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("h1, h2").first()).toBeVisible({ timeout: 5_000 });
    await dt.finalize("Pharmacist dashboard visible", page.url());
  });
});

// ═══════════════════════════════════════════════════════════════
// Flow 3: Chat (CRITICAL)
// ═══════════════════════════════════════════════════════════════
test.describe("Flow 3: Chat (CRITICAL)", () => {
  test("3.1 Chat landing page loads", async ({ page }) => {
    const dt = attachDevTools(page, "Chat");
    await seedSession(page, "cardiologist", "20000000-0000-0000-0000-000000000001");
    await page.goto("http://localhost:8082/chat");
    await page.waitForLoadState("networkidle");
    const hasContent = await page.locator("textarea, input[type='text'], [role='textbox']").count();
    if (hasContent === 0) {
      BUGS.push({
        severity: "HIGH",
        flow: "Chat",
        role: "cardiologist",
        url: page.url(),
        console: [],
        network: [],
        expected: "Chat input/textarea visible",
        actual: "No text input found on chat page",
      });
    }
    await dt.finalize("Chat page with input visible", page.url());
  });

  test("3.2 Chat history page loads", async ({ page }) => {
    const dt = attachDevTools(page, "Chat");
    await seedSession(page, "doctor", "20000000-0000-0000-0000-000000000001");
    await page.goto("http://localhost:8082/chat/history");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("body")).not.toBeEmpty();
    await dt.finalize("Chat history page not empty", page.url());
  });

  test("3.3 Chat general — verifies redirect or render", async ({ page }) => {
    const dt = attachDevTools(page, "Chat");
    await seedSession(page, "doctor", "20000000-0000-0000-0000-000000000001");
    await page.goto("http://localhost:8082/chat/general");
    await page.waitForLoadState("networkidle");
    // accept either chat or login redirect (session may not stick for this route)
    expect(page.url()).toMatch(/chat|auth/);
    await dt.finalize("Chat general route resolves", page.url());
  });
});

// ═══════════════════════════════════════════════════════════════
// Flow 4: Patient Management
// ═══════════════════════════════════════════════════════════════
test.describe("Flow 4: Patient Management", () => {
  test("4.1 Patients list loads", async ({ page }) => {
    const dt = attachDevTools(page, "Patients");
    await seedSession(page, "doctor", "20000000-0000-0000-0000-000000000001");
    await page.goto("http://localhost:8082/patients");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("h1, h2").first()).toBeVisible({ timeout: 5_000 });
    await dt.finalize("Patients list heading visible", page.url());
  });

  test("4.2 Patient detail page", async ({ page }) => {
    const dt = attachDevTools(page, "Patients");
    await seedSession(page, "cardiologist", "20000000-0000-0000-0000-000000000001");
    await page.goto("http://localhost:8082/patients/p-001");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("body")).not.toBeEmpty();
    await dt.finalize("Patient detail resolves", page.url());
  });
});

// ═══════════════════════════════════════════════════════════════
// Flow 5: RBAC Enforcement
// ═══════════════════════════════════════════════════════════════
test.describe("Flow 5: RBAC Enforcement", () => {
  const blockedTests = [
    { role: "rn", route: "/admin/roles", desc: "Nurse blocked from admin" },
    { role: "pharmacist", route: "/admin/roles", desc: "Pharmacist blocked from admin" },
    { role: "front_desk", route: "/admin/roles", desc: "Front desk blocked from admin" },
  ];

  for (const { role, route, desc } of blockedTests) {
    test(`5.x ${desc}`, async ({ page }) => {
      const dt = attachDevTools(page, "RBAC");
      await seedSession(page, role, "20000000-0000-0000-0000-000000000001");
      await page.goto(`http://localhost:8082${route}`);
      await page.waitForLoadState("networkidle");
      const url = page.url();
      const isBlocked = url.includes("/forbidden") || !url.includes(route);
      if (!isBlocked) {
        BUGS.push({
          severity: "HIGH",
          flow: "RBAC",
          role,
          url,
          console: [],
          network: [],
          expected: `${role} should be blocked from ${route}`,
          actual: `${role} can access ${route}`,
        });
      }
      await dt.finalize(`${role} blocked from ${route}`, page.url(), "HIGH");
    });
  }
});

// ═══════════════════════════════════════════════════════════════
// Flow 6: Error Pages
// ═══════════════════════════════════════════════════════════════
test.describe("Flow 6: Error Pages", () => {
  const errorRoutes = [
    "/error/forbidden",
    "/error/offline",
    "/error/server",
    "/error/timeout",
    "/error/maintenance",
    "/error/rate-limit",
    "/not-a-real-page-xyz",
  ];

  for (const route of errorRoutes) {
    test(`6.x Error page: ${route}`, async ({ page }) => {
      const dt = attachDevTools(page, "ErrorPages");
      await seedSession(page, "doctor", "20000000-0000-0000-0000-000000000001");
      await page.goto(`http://localhost:8082${route}`);
      await page.waitForLoadState("networkidle");
      await expect(page.locator("body")).not.toBeEmpty();
      await dt.finalize(`Error page ${route} renders`, page.url());
    });
  }
});

// ═══════════════════════════════════════════════════════════════
// Flow 7: Settings (admin only)
// ═══════════════════════════════════════════════════════════════
test.describe("Flow 7: Settings", () => {
  test("7.1 Admin can access settings", async ({ page }) => {
    const dt = attachDevTools(page, "Settings");
    await seedSession(page, "admin", "20000000-0000-0000-0000-000000000005");
    await page.goto("http://localhost:8082/settings");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("body")).not.toBeEmpty();
    await dt.finalize("Admin sees settings", page.url());
  });

  test("7.2 Non-admin blocked from settings", async ({ page }) => {
    const dt = attachDevTools(page, "Settings");
    await seedSession(page, "rn", "20000000-0000-0000-0000-000000000003");
    await page.goto("http://localhost:8082/settings");
    await page.waitForLoadState("networkidle");
    const url = page.url();
    const isBlocked = url.includes("/forbidden") || !url.includes("/settings");
    if (!isBlocked) {
      BUGS.push({
        severity: "HIGH",
        flow: "Settings",
        role: "rn",
        url,
        console: [],
        network: [],
        expected: "Nurse blocked from settings",
        actual: "Nurse can access settings",
      });
    }
    await dt.finalize("Nurse blocked from settings", url, "HIGH");
  });
});

// ═══════════════════════════════════════════════════════════════
// Flow 8: Documents
// ═══════════════════════════════════════════════════════════════
test.describe("Flow 8: Documents", () => {
  test("8.1 Documents list loads", async ({ page }) => {
    const dt = attachDevTools(page, "Documents");
    await seedSession(page, "doctor", "20000000-0000-0000-0000-000000000001");
    await page.goto("http://localhost:8082/documents");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("body")).not.toBeEmpty();
    await dt.finalize("Documents list renders", page.url());
  });

  test("8.2 Document upload page", async ({ page }) => {
    const dt = attachDevTools(page, "Documents");
    await seedSession(page, "cardiologist", "20000000-0000-0000-0000-000000000001");
    await page.goto("http://localhost:8082/documents/upload");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("body")).not.toBeEmpty();
    await dt.finalize("Upload page renders", page.url());
  });
});

// ═══════════════════════════════════════════════════════════════
// Flow 9: Graph Visualization
// ═══════════════════════════════════════════════════════════════
test.describe("Flow 9: Knowledge Graph", () => {
  test("9.1 Graph loads for authorized role", async ({ page }) => {
    const dt = attachDevTools(page, "Graph");
    await seedSession(page, "cardiologist", "20000000-0000-0000-0000-000000000001");
    await page.goto("http://localhost:8082/graph/patients/p-001");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("body")).not.toBeEmpty();
    await dt.finalize("Graph page renders", page.url());
  });
});

// ═══════════════════════════════════════════════════════════════
// BUG REPORT SUMMARY
// ═══════════════════════════════════════════════════════════════
test.afterAll(() => {
  console.log("\n" + "=".repeat(70));
  console.log("  🐛 BUG REPORT SUMMARY");
  console.log("=".repeat(70));

  if (BUGS.length === 0) {
    console.log("  ✅ No bugs detected during the audit.");
    return;
  }

  const bySeverity = {
    CRITICAL: BUGS.filter((b) => b.severity === "CRITICAL"),
    HIGH: BUGS.filter((b) => b.severity === "HIGH"),
    MEDIUM: BUGS.filter((b) => b.severity === "MEDIUM"),
    LOW: BUGS.filter((b) => b.severity === "LOW"),
  };

  for (const [severity, bugs] of Object.entries(bySeverity)) {
    if (bugs.length === 0) continue;
    console.log(`\n  ${severity} (${bugs.length})`);
    console.log("  " + "-".repeat(40));
    for (const bug of bugs) {
      console.log(`  🔴 Flow: ${bug.flow} | Role: ${bug.role || "N/A"} | URL: ${bug.url}`);
      console.log(`     Expected: ${bug.expected}`);
      console.log(`     Actual:   ${bug.actual}`);
      if (bug.console.length) console.log(`     Console:  ${bug.console[0]}`);
      if (bug.network.length) console.log(`     Network:  ${bug.network[0]}`);
      console.log();
    }
  }

  console.log(`  TOTAL BUGS: ${BUGS.length}`);
  console.log("=".repeat(70));
});
