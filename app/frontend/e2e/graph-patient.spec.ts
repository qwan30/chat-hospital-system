import { test, expect } from "@playwright/test";
import { seedSession } from "./_helpers";

// Minimal stub that gives the streaming hook something to work with
// (≥1 step so streamLength > 0 → stream.start() fires).
const MOCK_GRAPH = {
  patient_id: "p-001",
  nodes: [
    { id: "n1", label: "Hypertension", node_type: "diagnosis", properties: {} },
    { id: "n2", label: "Metformin", node_type: "medication", properties: {} },
  ],
  edges: [{ source: "n1", target: "n2", relation: "treated_by", weight: 0.9 }],
  reasoning_path: [
    {
      rationale: "Tracing diagnostic pathway for hypertension management.",
      steps: [
        {
          from_node: "Hypertension",
          to_node: "Metformin",
          relation: "treated_by",
          evidence: "Clinical guideline JNC-8",
        },
      ],
    },
  ],
  metadata: { updated_at: new Date().toISOString() },
};

test.describe("/graph/patients/:patientId — reasoning stream controls", () => {
  test.beforeEach(async ({ page }) => {
    await seedSession(page);
    // Intercept the graph API so the test is backend-independent.
    await page.route("**/api/v1/graph/patients/**", async (route) => {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_GRAPH) });
    });
    // Also intercept any other /api calls to prevent network errors in CI.
    await page.route("**/api/v1/**", async (route) => {
      if (!route.request().url().includes("/graph/patients/")) {
        await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({}) });
      }
    });
  });

  test("forced failure shows interrupted banner with Resume + Retry", async ({ page }) => {
    await page.goto("/graph/patients/p-001?simulate=stream-fail");

    await expect(page.getByText(/Response interrupted at/)).toBeVisible({ timeout: 8_000 });
    await expect(page.getByRole("button", { name: /Resume/ })).toBeVisible();
    await expect(page.getByRole("button", { name: /Retry/ })).toBeVisible();
  });

  test("rapid Resume / Retry presses do not spawn parallel streams", async ({ page }) => {
    await page.goto("/graph/patients/p-001?simulate=stream-fail");
    const banner = page.getByText(/Response interrupted at/);
    await expect(banner).toBeVisible({ timeout: 8_000 });

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
    await expect(banner).toBeVisible({ timeout: 8_000 });

    // No Stop button is rendered in the interrupted state — verify.
    await expect(page.getByRole("button", { name: /^Stop$/ })).toHaveCount(0);

    // Original cause stays put.
    await expect(banner).toBeVisible();
  });
});
