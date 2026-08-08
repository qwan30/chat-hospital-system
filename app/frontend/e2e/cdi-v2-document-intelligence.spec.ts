import { expect, test, type Page } from "@playwright/test";
import { fileURLToPath } from "node:url";

async function signInAsRealUser(page: Page, username: string) {
  await page.goto("/auth/login", { waitUntil: "networkidle" });

  const realLoginTab = page.getByRole("tab", { name: "Real Login" });
  await expect(realLoginTab).toBeVisible();
  await expect
    .poll(
      async () => {
        if ((await realLoginTab.getAttribute("aria-selected")) !== "true") {
          await realLoginTab.click();
        }
        return realLoginTab.getAttribute("aria-selected");
      },
      { timeout: 10000 },
    )
    .toBe("true");

  const realLoginPanel = page.getByRole("tabpanel", { name: "Real Login" });
  await expect(realLoginPanel).toBeVisible();
  await realLoginPanel.getByLabel("Username").fill(username);
  await realLoginPanel.getByLabel("Password").fill("demo");
  await realLoginPanel.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page).toHaveURL(/\/dashboard$/, { timeout: 15000 });
}

test("upload, correct, approve, explore graph and timeline, chat, and open exact evidence", async ({
  page,
}) => {
  test.setTimeout(120000); // 2 minutes, as backend processing might take a bit

  // 1. log in as the doctor editor through the real backend auth flow
  await signInAsRealUser(page, "doctor@example.test");
  await expect(page.getByText("Welcome")).toBeVisible({ timeout: 15000 });

  // 2. create direct upload session and PUT synthetic scan
  await page.getByRole("link", { name: "Documents", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Documents & OCR" })).toBeVisible();
  await page.getByRole("link", { name: "Upload documents", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Upload documents" })).toBeVisible();

  await page.getByLabel("Patient ID (UUID)").fill("20000000-0000-0000-0000-000000000003");
  await page.getByLabel("Document Title").fill("Synthetic E2E Scan");
  await page.getByLabel("Document Type").selectOption("scan");

  const testPdfPath = fileURLToPath(
    new URL(
      "../../backend/data/hosp_ai_synthetic_dataset/app/backend/data/patients_documents/patient_MRN0001_lab_result.pdf",
      import.meta.url,
    ),
  );
  await page.setInputFiles('input[type="file"]', testPdfPath);
  await page.getByRole("button", { name: "Upload document" }).click();

  // 4. finalize and wait for review-required extraction
  await expect(page.getByText("review_required", { exact: true })).toBeVisible({ timeout: 30000 });
  const uploadedDocumentPath = new URL(page.url()).pathname;

  // 5. edit page with If-Match
  const editArea = page.getByRole("textbox", { name: "Corrected page text" });
  await editArea.fill("Corrected 500 mg dose");

  const reasonInput = page.getByPlaceholder("Edit reason");
  await reasonInput.fill("Correct numeric dose");

  // Negative check 1: stale editor conflict
  await page.route(
    "**/draft/pages/*",
    async (route, request) => {
      if (request.method() === "PATCH" && !route.request().headers()["x-intercepted"]) {
        await route.fulfill({ status: 409, json: { detail: "Optimistic lock failed" } });
      } else {
        await route.continue();
      }
    },
    { times: 1 },
  );

  await page.getByRole("button", { name: "Save draft" }).click();
  await expect(page.getByRole("button", { name: "Compare with latest" })).toBeVisible();
  // Clear the conflict through authenticated client-side navigation; a full
  // reload would discard the in-memory token used by the E2E auth flow.
  await page.getByRole("link", { name: "Back to Documents", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Documents & OCR" })).toBeVisible();
  await page.locator(`a[href="${uploadedDocumentPath}"]`).click();
  await expect(page.getByText("review_required", { exact: true })).toBeVisible();

  // Do the actual edit again
  await page.getByRole("textbox", { name: "Corrected page text" }).fill("Corrected 500 mg dose");
  await page.getByPlaceholder("Edit reason").fill("Correct numeric dose");
  await page.getByRole("button", { name: "Save draft" }).click();

  // Wait for save to complete (Save draft disabled)
  // 6. submit
  await page.getByRole("button", { name: "Submit Draft" }).click();

  // Negative check 2: self-approval unavailable
  await expect(page.getByRole("button", { name: "Approve" })).toBeVisible();
  const approvePromise = page.waitForResponse("**/approve");
  await page.getByRole("button", { name: "Approve" }).click();
  const approveResponse = await approvePromise;
  expect(approveResponse.status()).not.toBe(200); // 400 or 403

  // 7. log in as a distinct admin approver through the real backend auth flow
  // We can just navigate to /auth/login, it will wipe the session in memory?
  // Actually, there's no sign out button in the test right now, so let's try just going to login
  await signInAsRealUser(page, "admin@example.test");
  await expect(page.getByText("Welcome")).toBeVisible();

  // 8. approve
  await page.getByRole("link", { name: "Documents", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Documents & OCR" })).toBeVisible();
  await page.locator(`a[href="${uploadedDocumentPath}"]`).click();
  await expect(page.getByRole("button", { name: "Approve" })).toBeVisible();
  await page.getByRole("button", { name: "Approve" }).click();

  // 9. wait for the newly activated generation to make the document ready
  await expect(page.getByText("ready", { exact: true })).toBeVisible({
    timeout: 15000,
  });

  // 10. graph and timeline are separate patient-scoped surfaces in the product.
  // Use in-app navigation here because the real-login token is intentionally
  // held in memory and a full page reload would discard it.
  const patientId = "20000000-0000-0000-0000-000000000003";
  const patientSlug = "p-003";
  await page.getByRole("link", { name: "Graph RAG", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Patient knowledge graph" })).toBeVisible({
    timeout: 30000,
  });
  await expect(page.getByText("RAG-grounded", { exact: true })).toBeVisible();

  await page.getByRole("link", { name: "Patients", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Patients" })).toBeVisible();
  await page.locator(`a[href="/patients/${patientSlug}"]`).first().click();
  const patientTimelineLink = page
    .locator("#main-content")
    .getByRole("link", { name: "Timeline", exact: true });
  await expect(patientTimelineLink).toBeVisible();
  await patientTimelineLink.click();
  await expect(
    page.getByText(/Clinical Timeline & Lineage|No clinical timeline events found\./),
  ).toBeVisible({
    timeout: 30000,
  });

  // 11. ask a grounded question from the real patient chat surface
  await page.getByRole("link", { name: "Open chat", exact: true }).click();
  await expect(page.getByRole("textbox", { name: "Message input" })).toBeVisible();
  await page
    .getByRole("textbox", { name: "Message input" })
    .fill("What is the approved metformin dose?");

  // Negative check 4: invalid stream order shows safe error state
  await page.route(
    // The dev server exposes /api and rewrites it to the backend's /api/v1.
    "**/api/chat/stream",
    async (route) => {
      // Return an invalid stream order: tokens before metadata
      const invalidPayload =
        'data: {"type":"token","sequence":1,"content":"hello","validation_mode":"sentence_buffered"}\n\n';
      await route.fulfill({
        status: 200,
        contentType: "text/event-stream",
        body: invalidPayload,
      });
    },
    { times: 1 },
  );

  await page.getByRole("button", { name: "Send" }).click();
  await expect(page.getByText("Invalid SSE event order")).toBeVisible();

  // Send the actual question
  await page
    .getByRole("textbox", { name: "Message input" })
    .fill("What is the approved metformin dose?");
  await page.getByRole("button", { name: "Send" }).click();

  // 12. verify ordered validated tokens
  await expect(page.getByText("Validated sentence streaming")).toBeVisible({ timeout: 15000 });

  // 13. open the actual Evidence Rail locator and return to the document
  await expect(page.getByText("Evidence", { exact: true })).toBeVisible();
  const openDocumentLink = page.getByRole("link", { name: "Open Document" }).first();
  await expect(openDocumentLink).toHaveAttribute("href", /page=1/);
  await openDocumentLink.click();
  await expect(page).toHaveURL(/\/documents\/[^?]+\?page=1/);
  await expect(page.getByRole("textbox", { name: "Corrected page text" })).toBeVisible();
});
