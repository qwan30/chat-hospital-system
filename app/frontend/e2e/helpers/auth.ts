import { Page, BrowserContext } from "@playwright/test";

const API_URL = "http://localhost:8000/api/v1";

export async function setupContext(context: BrowserContext) {
  await context.addInitScript((apiUrl: string) => {
    localStorage.setItem("hospital_ai_api_url", apiUrl);
    localStorage.setItem("e2e_auth_token", "e2e-test-token");
  }, API_URL);

  await context.route("**/auth/me", (route) => {
    route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({
        id: "dr-chen", full_name: "Dr. Sarah Chen",
        email: "sarah.chen@hospital.com", role: "physician", department: "Cardiology",
      }),
    });
  });

  await context.route("**/api/v1/dashboard/summary", (route) => {
    route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({
        recent_patients: [{ id: "1", full_name: "John Doe", mrn: "MRN-001" }],
        document_stats: { indexed: 10, processing: 2, failed: 1 },
        metrics: { hours_saved: 120, cost_saved_usd: 15000 },
        systems_health: { hms_api: "ok", ollama_inference: "ok" },
      }),
    });
  });

  await context.route("**/api/v1/patients/search**", (route) => {
    route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({
        items: [
          { id: "PT-0847", full_name: "Jonathan Blake", mrn: "MRN-2025-0847", department: "Cardiology", status: "active" },
          { id: "PT-1203", full_name: "Maria Garcia", mrn: "MRN-2025-1203", department: "Neurology", status: "admitted" },
        ], total: 2,
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
        sections: [{ title: "Chief Complaint", content: "Acute chest pain.", citations: [1] }],
        citations: [{ id: 1, document_title: "Admission Note", page: 2, content_snippet: "...", confidence: 0.94 }],
        confidence: "high", generated_at: "2025-05-15T09:00:00Z",
      }),
    });
  });

  await context.route("**/api/v1/patients/*/medication-review", (route) => {
    route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({
        patient_id: "PT-0847",
        medications: [{ id: "med-1", name: "Lisinopril", dosage: "10mg", frequency: "Once daily", route: "PO", indication: "Hypertension", start_date: "Apr 2025", status: "active", citation_id: 1 }],
        allergies: [{ id: "all-1", allergen: "Penicillin", severity: "high", reaction: "Anaphylaxis", recorded_date: "Jan 2019" }],
        recommendations: ["Consider dose adjustment."],
        citations: [{ id: 1, document_title: "Medication List", page: 1, content_snippet: "...", confidence: 0.95 }],
        confidence: "high",
      }),
    });
  });

  await context.route("**/api/v1/audit/events**", (route) => {
    route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({
        items: [
          { id: "evt-001", actor_user_id: "dr.chen", action: "patient.read", object_type: "PatientRecord", patient_id: "PT-0847", outcome: "allowed", trace_id: "tr-001", created_at: "2025-05-15T08:32:00Z" },
        ],
      }),
    });
  });

  await context.route("**/api/v1/metrics/summary", (route) => {
    route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({
        total_queries: 1247, avg_latency_ms: 142, total_cost_saved: 47250, helpful_rate: 94, no_evidence_rate: 3, audit_deny_count: 23,
      }),
    });
  });

  await context.route("**/api/v1/documents**", (route) => {
    route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({
        items: [{ id: "doc-001", title: "Admission Note", patient_id: "PT-0847", document_type: "Clinical Note", status: "indexed", ocr_confidence: 0.94, page_count: 3, created_at: "2025-05-12T08:00:00Z" }],
        total: 1,
      }),
    });
  });

  // GET chat-threads (list) + POST (create)
  await context.route("**/api/v1/chat-threads", (route) => {
    if (route.request().method() === "POST") {
      route.fulfill({
        status: 200, contentType: "application/json",
        body: JSON.stringify({ id: "thread-e2e", title: "E2E Thread", created_at: new Date().toISOString() }),
      });
    } else {
      route.fulfill({
        status: 200, contentType: "application/json",
        body: JSON.stringify({ items: [], total: 0 }),
      });
    }
  });
  // POST /api/v1/chat (send message)
  await context.route("**/api/v1/chat", (route) => {
    if (route.request().method() === "POST") {
      route.fulfill({
        status: 200, contentType: "application/json",
        body: JSON.stringify({ id: "msg-e2e", role: "assistant", content: "Based on the available evidence, the patient shows normal values.", confidence: "high", citations: [] }),
      });
    } else {
      route.continue();
    }
  });
}

export async function gotoAuthenticated(page: Page, path: string) {
  await page.goto(path);
  await page.waitForTimeout(2000);
}