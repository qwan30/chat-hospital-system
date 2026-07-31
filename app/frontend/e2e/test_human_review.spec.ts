import { expect, test } from "@playwright/test";
import { seedSession } from "./_helpers";
import { mountApiMocks } from "./fixtures/api-mocks";

test.describe("Document Upload and Human Review workflows", () => {
  test.beforeEach(async ({ page }) => {
    await seedSession(page);
    await mountApiMocks(page);

    // Mock upload response
    await page.route("**/api/documents", async (route) => {
      if (route.request().method() === "POST") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            id: "doc-123",
            patient_id: "20000000-0000-0000-0000-000000000003",
            title: "Test Document",
            document_type: "clinical_note",
            status: "indexed",
          }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ items: [], total: 0 }),
        });
      }
    });

    // Mock document details
    await page.route("**/api/documents/doc-123", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: "doc-123",
          patient_id: "20000000-0000-0000-0000-000000000003",
          uploaded_by: "Dr. Smith",
          title: "Test Document",
          document_type: "clinical_note",
          storage_uri: "s3://test/doc-123",
          mime_type: "application/pdf",
          status: "indexed",
          page_count: 1,
          ocr_error: null,
          created_at: new Date().toISOString(),
          processing_events: [],
        }),
      });
    });

    // Mock document content/blob (for preview)
    await page.route("**/api/documents/doc-123/content", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/pdf",
        body: "mock pdf content",
      });
    });

    // Mock document page
    await page.route("**/api/documents/doc-123/pages/*", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: "page-1",
          document_id: "doc-123",
          page_number: 1,
          ocr_text: "Patient has history of hypertension.",
          ocr_confidence: 0.95,
        }),
      });
    });

    // Mock document facts
    await page.route("**/api/documents/doc-123/facts", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          facts: [
            { id: "fact-1", confidence: 0.45 },
            { id: "fact-2", confidence: 0.96 },
          ],
        }),
      });
    });

    // Mock document intelligence
    await page.route("**/api/documents/doc-123/intelligence", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          document_id: "doc-123",
          status: "needs_review",
          facts_count: 2,
          review_items_count: 2,
        }),
      });
    });

    // Mock document review items
    await page.route("**/api/documents/doc-123/review-items", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          review_items: [
            {
              id: "review-1",
              fact_id: "fact-1",
              field_name: "allergies",
              original_value: "penicillin (anaphylaxis)",
              suggested_value: "penicillin (anaphylaxis)",
              review_status: "pending",
            },
            {
              id: "review-2",
              fact_id: "fact-2",
              field_name: "mrn",
              original_value: "MRN-48201",
              suggested_value: "MRN-48201",
              review_status: "approved",
            },
          ],
        }),
      });
    });

    // Mock patch review item
    await page.route("**/api/documents/doc-123/review-items/*", async (route) => {
      if (route.request().method() === "PATCH") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ success: true }),
        });
      }
    });
  });

  test("Document upload and human review flow", async ({ page }) => {
    page.on("console", (msg) => console.log(`[Browser Console] ${msg.type()}: ${msg.text()}`));
    page.on("pageerror", (err) => console.log(`[Browser Error] ${err.name}: ${err.message}`));

    // 1. Navigate to upload page
    await page.goto("/documents/upload");

    // 2. Fill the form
    await page.fill('input[id="patientId"]', "20000000-0000-0000-0000-000000000003");
    await page.fill('input[id="title"]', "Test Document");
    await page.selectOption('select[id="documentType"]', "clinical_note");

    // Create a mock file
    const buffer = Buffer.from("mock content");
    await page.setInputFiles('input[id="file"]', {
      name: "test.pdf",
      mimeType: "application/pdf",
      buffer,
    });

    // 3. Submit the form
    await page.click('button[type="submit"]');

    // 4. Verify we are navigated to the document page
    await page.waitForURL("**/documents/doc-123**");

    // 5. Verify the document details are rendered
    await expect(page.getByText("Test Document", { exact: true })).toBeVisible();

    // 6. Navigate to the Human Review page via client-side link to bypass SSR
    // The "Review 2 items" link should be visible based on the mocked intelligence response
    await page.click('a:has-text("Review 2 items")');
    await page.waitForURL("**/documents/doc-123/review");

    // Check elements on the review page
    try {
      await expect(page.getByText("OCR review")).toBeVisible({ timeout: 10000 });
    } catch (e) {
      console.log("FAILED TO FIND OCR REVIEW. PAGE CONTENT:");
      console.log(await page.content());
      throw e;
    }
    await expect(
      page.getByText("Low-confidence regions flagged for human verification."),
    ).toBeVisible();

    // Check some mocked fields rendered by the review component
    await expect(page.getByText("MRN-48201")).toBeVisible();
    await expect(page.getByText("penicillin (anaphylaxis)")).toBeVisible();

    // Check if the Approve button exists and click it
    const approveButton = page.getByRole("button", { name: "Approve" }).first();
    await expect(approveButton).toBeVisible();
    await approveButton.click();

    // Wait for the success toast
    await expect(page.getByText("Review item updated")).toBeVisible();
  });
});
