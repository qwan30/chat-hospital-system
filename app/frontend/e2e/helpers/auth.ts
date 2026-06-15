import { Page, BrowserContext, expect } from "@playwright/test";

const API_URL = "http://localhost:8000/api/v1";

// ── Auth helpers that simulate REAL USER interactions ──────────────

/**
 * Login by clicking the SSO button — the simplest real-user flow.
 * The LoginCard.handleSSOLogin() calls login(apiUrl, "dev-admin") which
 * hits GET /auth/me with Bearer "dev-admin".
 */
export async function loginViaSSO(page: Page): Promise<void> {
  await page.goto("/login");
  await page.waitForLoadState("networkidle");

  // Real user sees the SSO button and clicks it
  const ssoButton = page.getByRole("button", { name: /Sign in with Hospital SSO/i });
  await expect(ssoButton).toBeVisible({ timeout: 10000 });
  await ssoButton.click();

  // After successful login, redirect to dashboard
  await page.waitForURL(/\/dashboard/, { timeout: 15000 });
  await page.waitForLoadState("networkidle");
}

/**
 * Login by typing email + password — the full form flow.
 * handleEmailLogin() calls login(apiUrl, password.trim()) which
 * uses the password value as the Bearer token for GET /auth/me.
 */
export async function loginViaEmailForm(
  page: Page,
  credentials: { email: string; password: string },
): Promise<void> {
  await page.goto("/login");
  await page.waitForLoadState("networkidle");

  // Real user: type email into the email field
  await page.getByPlaceholder("Enter your email").fill(credentials.email);

  // Real user: type password into the password field
  await page.getByPlaceholder("Enter your password").fill(credentials.password);

  // Real user: click the submit button
  await page.getByRole("button", { name: "Sign in with email" }).click();

  // After successful login, redirect to MFA page then dashboard
  // (handleEmailLogin pushes to /login/mfa on success)
  await page.waitForURL(/\/login\/mfa/, { timeout: 15000 }).catch(() => {});
  await page.waitForLoadState("networkidle");
}

/**
 * Attempt login with invalid credentials — should show error, stay on login page.
 */
export async function loginWithInvalidCredentials(
  page: Page,
  credentials: { email: string; password: string },
): Promise<void> {
  await page.goto("/login");
  await page.waitForLoadState("networkidle");

  await page.getByPlaceholder("Enter your email").fill(credentials.email);
  await page.getByPlaceholder("Enter your password").fill(credentials.password);
  await page.getByRole("button", { name: "Sign in with email" }).click();

  // Should stay on login page — error message appears
  await page.waitForTimeout(1500);
}

/**
 * Attempt login with empty fields — should show validation error.
 */
export async function loginWithEmptyFields(page: Page): Promise<void> {
  await page.goto("/login");
  await page.waitForLoadState("networkidle");

  // Don't fill anything — just click submit
  await page.getByRole("button", { name: "Sign in with email" }).click();

  // Validation error should appear
  await page.waitForTimeout(1000);
}

// ── Context setup (API mocking) ────────────────────────────────────

/**
 * Standard setup for authenticated E2E tests.
 * Auto-injects token into localStorage so AuthProvider auto-logs in.
 * Use this for tests that start AFTER login (dashboard, patients, chat, etc.)
 */
export async function setupContext(context: BrowserContext) {
  await context.addInitScript((apiUrl: string) => {
    localStorage.setItem("hospital_ai_api_url", apiUrl);
    localStorage.setItem("e2e_auth_token", "e2e-test-token");
  }, API_URL);

  await mockAllApiRoutes(context);
}

/**
 * Setup for interactive login tests — does NOT auto-inject token,
 * so the user sees and interacts with the real login form.
 */
export async function setupContextForLogin(context: BrowserContext) {
  await context.addInitScript((apiUrl: string) => {
    localStorage.setItem("hospital_ai_api_url", apiUrl);
    // NO e2e_auth_token — user must interact with login form
  }, API_URL);

  // mockAllApiRoutes handles /auth/me with token-based logic
  await mockAllApiRoutes(context);
}

/** Shared API route mocks used by all E2E tests */
async function mockAllApiRoutes(context: BrowserContext) {
  // ── Auth (for authenticated tests — always returns doctor) ──
  await context.route("**/auth/me", (route) => {
    const authHeader = route.request().headers()["authorization"] || "";
    // If there's an auth header, it came from a real login action
    // Match known dev tokens to return appropriate user
    if (authHeader.includes("dev-admin")) {
      route.fulfill({
        status: 200, contentType: "application/json",
        body: JSON.stringify({
          id: "admin-001", full_name: "Alex Admin",
          email: "admin@example.test", role: "admin", department: "IT",
        }),
      });
    } else if (authHeader.includes("dev-doctor")) {
      route.fulfill({
        status: 200, contentType: "application/json",
        body: JSON.stringify({
          id: "dr-chen", full_name: "Dr. Sarah Chen",
          email: "sarah.chen@hospital.com", role: "physician", department: "Cardiology",
        }),
      });
    } else if (authHeader.includes("e2e-test-token")) {
      // E2E auto-login token (injected via localStorage by setupContext)
      route.fulfill({
        status: 200, contentType: "application/json",
        body: JSON.stringify({
          id: "dr-chen", full_name: "Dr. Sarah Chen",
          email: "sarah.chen@hospital.com", role: "physician", department: "Cardiology",
        }),
      });
    } else if (authHeader) {
      // Unknown token → 401 for error testing
      route.fulfill({
        status: 401, contentType: "application/json",
        body: JSON.stringify({ error: "unauthorized", message: "Invalid credentials" }),
      });
    } else {
      // No auth header — auto-login token from localStorage
      route.fulfill({
        status: 200, contentType: "application/json",
        body: JSON.stringify({
          id: "dr-chen", full_name: "Dr. Sarah Chen",
          email: "sarah.chen@hospital.com", role: "physician", department: "Cardiology",
        }),
      });
    }
  });

  // ── Dashboard ──
  await context.route("**/api/v1/dashboard/summary", (route) => {
    route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({
        recent_patients: [
          { id: "PT-0847", full_name: "Jonathan Blake", mrn: "MRN-2025-0847" },
          { id: "PT-1203", full_name: "Maria Garcia", mrn: "MRN-2025-1203" },
        ],
        document_stats: { indexed: 10, processing: 2, failed: 1 },
        metrics: { hours_saved: 120, cost_saved_usd: 15000 },
        systems_health: { hms_api: "ok", ollama_inference: "ok" },
      }),
    });
  });

  // ── Patients ──
  await context.route("**/api/v1/patients/search**", (route) => {
    route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({
        items: [
          { id: "PT-0847", full_name: "Jonathan Blake", mrn: "MRN-2025-0847", department: "Cardiology", status: "active" },
          { id: "PT-1203", full_name: "Maria Garcia", mrn: "MRN-2025-1203", department: "Neurology", status: "admitted" },
          { id: "PT-5591", full_name: "Alice Synthetic", mrn: "MRN-0001", department: "Internal Medicine", status: "active" },
        ], total: 3,
      }),
    });
  });

  await context.route("**/api/v1/patients/*/overview", (route) => {
    route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({
        patient_id: "PT-0847", full_name: "Jonathan Blake", mrn: "MRN-2025-0847",
        dob: "1962-03-15", gender: "Male", blood_type: "O+", department: "Cardiology",
        attending_physician: "Dr. Sarah Chen", admission_status: "active",
        admitted_date: "2025-05-12", room: "304-B",
        allergy_count: 3, medication_count: 5, lab_count: 12,
        last_updated: "2025-05-15T08:30:00Z",
      }),
    });
  });

  await context.route("**/api/v1/patients/*/ai-summary/generate", (route) => {
    route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({
        patient_id: "PT-0847",
        sections: [
          { title: "Chief Complaint", content: "Acute chest pain radiating to left arm. Onset 2 hours prior to admission.", citations: [1] },
          { title: "Assessment", content: "ST-elevation noted in anterior leads. Troponin elevated.", citations: [2] },
        ],
        citations: [
          { id: 1, document_title: "Admission Note", page: 2, content_snippet: "Patient presents with...", confidence: 0.94 },
          { id: 2, document_title: "Lab Results", page: 1, content_snippet: "Troponin I: 0.8 ng/mL", confidence: 0.97 },
        ],
        confidence: "high", generated_at: "2025-05-15T09:00:00Z",
      }),
    });
  });

  await context.route("**/api/v1/patients/*/medication-review", (route) => {
    route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({
        patient_id: "PT-0847",
        medications: [
          { id: "med-1", name: "Lisinopril", dosage: "10mg", frequency: "Once daily", route: "PO", indication: "Hypertension", start_date: "Apr 2025", status: "active", citation_id: 1 },
          { id: "med-2", name: "Atorvastatin", dosage: "20mg", frequency: "Once daily at bedtime", route: "PO", indication: "Hyperlipidemia", start_date: "Mar 2025", status: "active", citation_id: 2 },
        ],
        allergies: [
          { id: "all-1", allergen: "Penicillin", severity: "high", reaction: "Anaphylaxis", recorded_date: "Jan 2019" },
          { id: "all-2", allergen: "Sulfa", severity: "medium", reaction: "Rash", recorded_date: "Mar 2020" },
        ],
        recommendations: ["No drug-drug interactions detected.", "Consider monitoring renal function with Lisinopril."],
        citations: [
          { id: 1, document_title: "Medication List", page: 1, content_snippet: "Lisinopril 10mg daily...", confidence: 0.95 },
          { id: 2, document_title: "Medication List", page: 1, content_snippet: "Atorvastatin 20mg...", confidence: 0.93 },
        ],
        confidence: "high",
      }),
    });
  });

  // ── Documents ──
  await context.route("**/api/v1/documents**", (route) => {
    if (route.request().method() === "POST") {
      route.fulfill({
        status: 201, contentType: "application/json",
        body: JSON.stringify({
          id: "doc-new", title: "Uploaded Document", patient_id: "PT-0847",
          document_type: "Clinical Note", status: "uploaded", page_count: 1,
          created_at: new Date().toISOString(),
        }),
      });
    } else {
      route.fulfill({
        status: 200, contentType: "application/json",
        body: JSON.stringify({
          items: [
            { id: "doc-001", title: "Admission Note", patient_id: "PT-0847", document_type: "Clinical Note", status: "indexed", ocr_confidence: 0.94, page_count: 3, created_at: "2025-05-12T08:00:00Z" },
            { id: "doc-002", title: "Lab Results - CBC", patient_id: "PT-0847", document_type: "Lab Report", status: "indexed", ocr_confidence: 0.98, page_count: 2, created_at: "2025-05-13T10:30:00Z" },
          ], total: 2,
        }),
      });
    }
  });

  // ── Chat ──
  await context.route("**/api/v1/chat-threads", (route) => {
    if (route.request().method() === "POST") {
      route.fulfill({
        status: 201, contentType: "application/json",
        body: JSON.stringify({ id: "thread-new", title: "New Thread", created_at: new Date().toISOString() }),
      });
    } else {
      route.fulfill({
        status: 200, contentType: "application/json",
        body: JSON.stringify({
          items: [
            { id: "thread-001", title: "Cardiac Workup - Jonathan Blake", patient_id: "PT-0847", last_message_at: "2025-05-15T08:30:00Z" },
          ], total: 1,
        }),
      });
    }
  });

  await context.route("**/api/v1/chat**", (route) => {
    if (route.request().method() === "POST") {
      // Simulate slight AI delay (real user waits for response)
      route.fulfill({
        status: 200, contentType: "application/json",
        body: JSON.stringify({
          id: "msg-" + Date.now(),
          role: "assistant",
          content: "Based on the available evidence, the patient shows normal vital signs. [E1] The blood work indicates values within expected ranges. [E2] No contraindications were found in the medication review.",
          confidence: "high",
          citations: [
            { evidence_id: "E1", document_title: "Vital Signs Chart", page: 1, content_snippet: "BP 120/80, HR 72...", score: 0.94 },
            { evidence_id: "E2", document_title: "Lab Results CBC", page: 2, content_snippet: "All values within range...", score: 0.91 },
          ],
        }),
      });
    }
  });

  // ── Audit ──
  await context.route("**/api/v1/audit/events**", (route) => {
    route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({
        items: [
          { id: "evt-001", actor_user_id: "dr-chen", action: "patient.read", object_type: "PatientRecord", patient_id: "PT-0847", outcome: "allowed", trace_id: "tr-001", created_at: "2025-05-15T08:32:00Z" },
          { id: "evt-002", actor_user_id: "dr-chen", action: "chat.query", object_type: "ChatMessage", patient_id: "PT-0847", outcome: "allowed", trace_id: "tr-002", created_at: "2025-05-15T08:35:00Z" },
        ],
      }),
    });
  });

  // ── Metrics ──
  await context.route("**/api/v1/metrics/summary", (route) => {
    route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({
        total_queries: 1247, avg_latency_ms: 142, total_cost_saved: 47250,
        helpful_rate: 94, no_evidence_rate: 3, audit_deny_count: 23,
      }),
    });
  });

  // ── Search ──
  await context.route("**/api/v1/search/global**", (route) => {
    route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({
        patients: [{ id: "PT-0847", full_name: "Jonathan Blake", mrn: "MRN-2025-0847" }],
        documents: [{ id: "doc-001", title: "Admission Note" }],
      }),
    });
  });

  // ── Access Requests ──
  await context.route("**/api/v1/access-requests", (route) => {
    route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({
        message: "Temporary clinical access scope granted for 1 hour.",
        patient_id: "PT-0847",
        expires_at: new Date(Date.now() + 3600000).toISOString(),
      }),
    });
  });

  // ── Settings ──
  await context.route("**/api/v1/settings/**", (route) => {
    route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({}),
    });
  });
}

// ── Navigation helper ──────────────────────────────────────────────

export async function gotoAuthenticated(page: Page, path: string) {
  await page.goto(path);
  await page.waitForTimeout(2000);
}
