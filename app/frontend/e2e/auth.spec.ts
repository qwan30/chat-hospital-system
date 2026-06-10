import { test, expect } from "@playwright/test";

test.describe("Auth - Login", () => {
  test("renders login page with heading", async ({ page }) => {
    await page.goto("/login");
    await expect(page.locator("h1").first()).toBeVisible();
  });
  test("displays SSO button", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByRole("button", { name: /Sign in with Hospital SSO/i })).toBeVisible();
  });
  test("has email and password inputs", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByPlaceholder(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
  });
  test("renders marketing bullet points", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByText(/HIPAA-compliant/i)).toBeVisible();
  });
  test("shows trust badges", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByText(/PHI Protection/i).first()).toBeVisible();
    await expect(page.getByText(/Audit Logging/i).first()).toBeVisible();
    await expect(page.getByText(/Role-Based Access/i).first()).toBeVisible();
  });
});

test.describe("Auth - MFA", () => {
  test("renders MFA heading", async ({ page }) => {
    await page.goto("/login/mfa");
    await expect(page.getByText(/Two-Factor Authentication/i)).toBeVisible();
  });
  test("has 6 OTP inputs", async ({ page }) => {
    await page.goto("/login/mfa");
    await expect(page.getByRole("textbox")).toHaveCount(6);
  });
  test("verify button disabled when empty", async ({ page }) => {
    await page.goto("/login/mfa");
    await expect(page.getByRole("button", { name: /Verify Code/i })).toBeDisabled();
  });
  test("shows resend countdown", async ({ page }) => {
    await page.goto("/login/mfa");
    await expect(page.getByText(/Resend in/i)).toBeVisible();
  });
  test("has back to sign in", async ({ page }) => {
    await page.goto("/login/mfa");
    await expect(page.getByText(/Back to sign in/i)).toBeVisible();
  });
});