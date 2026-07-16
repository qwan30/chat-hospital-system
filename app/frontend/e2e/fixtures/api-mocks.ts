/**
 * e2e/fixtures/api-mocks.ts
 *
 * Shared Playwright route interceptors for tests that run without a backend.
 * Import `withApiMocks` in any spec's `test.use()` or `beforeEach` to get a
 * set of minimal-valid API responses that keep the app from hanging on
 * fetch errors.
 *
 * Tests that need REAL backend behaviour (LLM streaming, actual CDSS alerts)
 * should use `test.skip(!!process.env.CI, "requires live backend")` instead.
 */
import type { Page } from "@playwright/test";

// ── Minimal stub payloads ─────────────────────────────────────────────────────

export const MOCK_PATIENTS = {
  items: [
    {
      id: "p-001",
      mrn: "MRN-001",
      first_name: "Alice",
      last_name: "Synthetic",
      date_of_birth: "1960-04-12",
      gender: "Female",
      primary_diagnosis: "Hypertension",
      attending_physician: "Dr. Nguyen",
      ward: "Cardiology",
    },
    {
      id: "p-003",
      mrn: "MRN-003",
      first_name: "Eleanor",
      last_name: "Vance",
      date_of_birth: "1975-08-21",
      gender: "Female",
      primary_diagnosis: "Atrial Fibrillation",
      attending_physician: "Dr. Tran",
      ward: "Cardiology",
    },
  ],
  total: 2,
  page: 1,
  page_size: 20,
};

export const MOCK_PATIENT_DETAIL = {
  id: "p-001",
  mrn: "MRN-001",
  first_name: "Alice",
  last_name: "Synthetic",
  date_of_birth: "1960-04-12",
  gender: "Female",
  primary_diagnosis: "Hypertension",
  attending_physician: "Dr. Nguyen",
  ward: "Cardiology",
  allergies: [],
  active_medications: [
    { name: "Metformin", dose: "500mg", frequency: "BID", route: "oral" },
  ],
};

export const MOCK_PATIENT_GRAPH = {
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

export const MOCK_DASHBOARD_METRICS = {
  avg_summary_seconds: 4.2,
  cited_answers_pct: 87,
  active_patients: 23,
  pending_alerts: 2,
  recent_queries: [],
};

export const MOCK_DOCUMENTS = {
  items: [],
  total: 0,
  page: 1,
  page_size: 20,
};

export const MOCK_AUDIT_LOGS = {
  items: [],
  total: 0,
  page: 1,
  page_size: 20,
};

export const MOCK_NOTIFICATIONS = {
  items: [],
  total: 0,
  unread_count: 0,
};

// ── Route interceptor ─────────────────────────────────────────────────────────

/**
 * Mount all API mocks onto `page`. Call this in `beforeEach` or `test.use()`.
 * Routes are matched in registration order; more-specific routes must come first.
 */
export async function mountApiMocks(page: Page): Promise<void> {
  // Graph patient API
  await page.route("**/api/v1/graph/patients/**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(MOCK_PATIENT_GRAPH),
    });
  });

  // Patient detail
  await page.route("**/api/v1/patients/p-*", async (route) => {
    const method = route.request().method();
    if (method === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(MOCK_PATIENT_DETAIL),
      });
    } else {
      await route.continue();
    }
  });

  // Patients list
  await page.route("**/api/v1/patients*", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(MOCK_PATIENTS),
    });
  });

  // Dashboard / metrics
  await page.route("**/api/v1/dashboard**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(MOCK_DASHBOARD_METRICS),
    });
  });

  // Documents
  await page.route("**/api/v1/documents**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(MOCK_DOCUMENTS),
    });
  });

  // Audit logs
  await page.route("**/api/v1/audit**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(MOCK_AUDIT_LOGS),
    });
  });

  // Notifications — empty list so CDSS alert tests still have a reference
  await page.route("**/api/v1/notifications**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(MOCK_NOTIFICATIONS),
    });
  });

  // Catch-all for any remaining /api/v1/ calls (threads, chat, etc.)
  await page.route("**/api/v1/**", async (route) => {
    // Don't intercept streaming/SSE — let those fail naturally.
    const url = route.request().url();
    if (url.includes("/stream") || url.includes("/chat/send")) {
      await route.abort("connectionrefused");
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({}),
    });
  });
}
