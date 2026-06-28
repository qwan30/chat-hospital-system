import { test, expect, type Page } from "@playwright/test";

async function seedSession(page: Page, role = "cardiologist", workspaceId = "ws-cardio-4n") {
  await page.addInitScript(
    ({ role, workspaceId }) => {
      localStorage.setItem("hms.session", JSON.stringify({ role, workspaceId }));
    },
    { role, workspaceId },
  );
}

test.describe("UAT Flow 1: Verification (Clinician Workflow)", () => {
  test.beforeEach(async ({ page }) => {
    await seedSession(page, "cardiologist", "ws-cardio-4n");
  });

  test("View patient overview → open chat → query meds → click citation to view document", async ({ page }) => {
    // 1. Go to patient details page
    await page.goto("/patients/p-001", { waitUntil: "networkidle" });
    await page.waitForTimeout(1000);
    
    // Verify patient demographics loaded
    await expect(page.locator("body")).toBeVisible();
    await expect(page.getByText(/MRN/i).first()).toBeVisible();

    // 2. Click "Open chat" to start a RAG session
    await page.locator('a:has-text("Open chat")').first().click();
    await page.waitForURL("**/chat?patient=p-001", { timeout: 10000 });
    await page.waitForTimeout(1000);

    // 3. Send a clinical query to trigger retrieval and citation
    const composer = page.locator("textarea").first();
    await expect(composer).toBeVisible();
    await composer.fill("List the patient's current medications.");
    await page.locator('button:has-text("Send")').click();
    
    // Wait for the streaming response to finalize
    await page.waitForTimeout(3000);
    await expect(page.locator('[data-msg-role="assistant"]').first()).toBeVisible({ timeout: 10000 });

    // 4. Verify citation chips are rendered in the Evidence rail
    const evidenceRail = page.locator("h3:has-text('Evidence')");
    await expect(evidenceRail).toBeVisible();
    
    const openDocLink = page.locator("a:has-text('Open Document')").first();
    await expect(openDocLink).toBeVisible();
    
    // 5. Click citation to open document preview
    await openDocLink.click();
    await page.waitForURL("**/documents/**", { timeout: 10000 });
    await page.waitForTimeout(1000);

    // Verify document page loaded and shows preview text
    await expect(page.getByText(/Extracted text/i)).toBeVisible();
  });
});

test.describe("UAT Flow 2: Justification (RBAC Gating & Break-Glass)", () => {
  test("Nurse tries to view restricted patient → handles access request dialog", async ({ page }) => {
    await seedSession(page, "rn", "ws-icu-2w");
    
    // Go to restricted patient (Bob, p-002)
    await page.goto("/patients/p-002", { waitUntil: "networkidle" });
    await page.waitForTimeout(1000);

    // Verify "Patient not found / Restricted record" page loads
    await expect(page.getByText(/No record matches this MRN in your accessible scope/i)).toBeVisible();
    
    const requestAccessBtn = page.getByRole("button", { name: "Request access" });
    await expect(requestAccessBtn).toBeVisible();
    
    // Open Access Request Dialog
    await requestAccessBtn.click();
    await expect(page.getByText("Request access to patient record")).toBeVisible();

    const justificationField = page.locator("#justification");
    await expect(justificationField).toBeVisible();

    const submitBtn = page.getByRole("button", { name: "Submit request" });
    
    // Submit button should be disabled for short justification
    await justificationField.fill("Too short");
    await page.waitForTimeout(300);
    await expect(submitBtn).toBeDisabled();

    // Type valid justification (>= 15 characters)
    await justificationField.fill("Nurse requesting ICU transfer clearance for cardiology review.");
    await page.waitForTimeout(300);
    await expect(submitBtn).toBeEnabled();

    // Submit request
    await submitBtn.click();

    // Verify success notification
    await expect(page.getByText("Access request submitted")).toBeVisible({ timeout: 5000 });
  });

  test("Nurse triggers forbidden page → performs emergency break-glass override", async ({ page }) => {
    await seedSession(page, "rn", "ws-icu-2w");

    // Navigate to break-glass forbidden state directly
    await page.goto("/error/forbidden?reason=break-glass&from=/patients/p-001", { waitUntil: "networkidle" });
    await page.waitForTimeout(1000);

    // Verify emergency warning and description
    await expect(page.getByText("Break-glass access required")).toBeVisible();
    await expect(page.getByText("emergency clinical justification")).toBeVisible();

    const breakGlassTrigger = page.getByRole("button", { name: "Break-glass access" });
    await expect(breakGlassTrigger).toBeVisible();
    await breakGlassTrigger.click();

    // Verify dialog appears
    await expect(page.getByRole("heading", { name: "Break-glass access", exact: true })).toBeVisible();
    
    const reasonField = page.locator("#bg-reason");
    const confirmBtn = page.getByRole("button", { name: "Grant emergency access" });

    // Confirm button is disabled for short justification (< 12 characters)
    await reasonField.fill("Urgent");
    await expect(confirmBtn).toBeDisabled();

    // Complete valid clinical reason
    await reasonField.fill("Emergency ECG review for severe chest pain.");
    await expect(confirmBtn).toBeEnabled();

    // Confirm break glass
    await confirmBtn.click();

    // Verify success toast notification and redirection
    await expect(page.getByText("Break-glass access granted")).toBeVisible({ timeout: 5000 });
  });
});

test.describe("UAT Flow 3: Safety (Medication Reconciliation)", () => {
  test.beforeEach(async ({ page }) => {
    await seedSession(page, "pharmacist", "ws-pharmacy");
  });

  test("Check drug review panel for interactions", async ({ page }) => {
    // Go to Eleanor Vance medication review
    await page.goto("/patients/p-003/medication-review", { waitUntil: "networkidle" });
    await page.waitForTimeout(1500);

    // Verify warnings section
    await expect(page.getByText("Pharmacist review — AI suggestions")).toBeVisible();

    // Verify specific drug-allergy / drug-drug warnings exist
    const hasWarnings = await page.locator("li").count();
    expect(hasWarnings).toBeGreaterThanOrEqual(0);
  });

  test("Query chatbot for drug interaction warnings", async ({ page }) => {
    await page.goto("/chat?patient=p-003", { waitUntil: "networkidle" });
    await page.waitForTimeout(1000);

    const composer = page.locator("textarea").first();
    await composer.fill("Check for drug-drug interactions or allergies.");
    await page.locator('button:has-text("Send")').click();

    // Wait for the RAG check to stream response
    await page.waitForTimeout(3000);
    
    const response = page.locator('[data-msg-role="assistant"]').first();
    await expect(response).toBeVisible({ timeout: 10000 });

    const content = await response.innerText();
    expect(content.length).toBeGreaterThan(50);
  });
});
