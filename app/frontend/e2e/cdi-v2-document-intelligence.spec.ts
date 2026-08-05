import { test, expect } from "@playwright/test";

test("upload, correct, approve, explore, chat, and open exact evidence", async ({ page }) => {
  await uploadSyntheticScan(page);
  await expect(page.getByText("Review required")).toBeVisible();
  await editPageAndSave(page, "Corrected 500 mg dose", "Correct numeric dose");
  await submitAndApproveWithDifferentUsers(page);
  await expect(page.getByText("Generation active")).toBeVisible();
  await page.getByRole("link", { name: "Open graph" }).click();
  await expect(page.getByText("Source evidence")).toBeVisible();
  await askPatientQuestion(page, "What is the approved metformin dose?");
  await expect(page.getByText("Validated sentence streaming")).toBeVisible();
  await page.getByRole("link", { name: "Open exact evidence" }).click();
  await expect(page.getByText("Revision v2")).toBeVisible();
});

async function uploadSyntheticScan(page) {
  // stub
}
async function editPageAndSave(page, a, b) {
  // stub
}
async function submitAndApproveWithDifferentUsers(page) {
  // stub
}
async function askPatientQuestion(page, a) {
  // stub
}
