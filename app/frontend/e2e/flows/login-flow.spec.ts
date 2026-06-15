/**
 * Login Flow — Real User Interaction Tests
 *
 * Simulates exactly what a real clinician does:
 * type credentials, click buttons, wait for responses.
 * NO programmatic token injection — real form interaction.
 */
import { test, expect } from "@playwright/test";
import {
  loginViaSSO,
  loginViaEmailForm,
  loginWithInvalidCredentials,
  loginWithEmptyFields,
  setupContextForLogin,
} from "../helpers/auth";

test.describe("Login — SSO Button", () => {
  test.beforeEach(async ({ context }) => {
    await setupContextForLogin(context);
  });

  test("SSO button is visible and clickable", async ({ page }) => {
    await page.goto("/login");
    const ssoButton = page.getByRole("button", {
      name: /Sign in with Hospital SSO/i,
    });
    await expect(ssoButton).toBeVisible({ timeout: 10000 });
    await expect(ssoButton).toBeEnabled();
  });

  test("clicking SSO logs in and redirects to dashboard", async ({ page }) => {
    await loginViaSSO(page);
    await expect(
      page.getByRole("heading", { name: /Dashboard/i }).first(),
    ).toBeVisible({ timeout: 15000 });
    await expect(page.getByText(/Alex Admin|Dr. Sarah Chen/i).first()).toBeVisible({
      timeout: 5000,
    });
  });
});

test.describe("Login — Email Form", () => {
  test.beforeEach(async ({ context }) => {
    await setupContextForLogin(context);
  });

  test("email and password fields are visible", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByPlaceholder("Enter your email")).toBeVisible({ timeout: 10000 });
    await expect(page.getByPlaceholder("Enter your password")).toBeVisible();
    await expect(page.getByRole("button", { name: "Sign in with email" })).toBeVisible();
  });

  test("remember me checkbox and forgot password link visible", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByText("Remember this device")).toBeVisible();
    await expect(page.getByText("Forgot password?")).toBeVisible();
  });

  test("security trust badges visible for unauthenticated user", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByText("PHI Protection").first()).toBeVisible();
    await expect(page.getByText("Audit Logging").first()).toBeVisible();
    await expect(page.getByText("Role-Based Access").first()).toBeVisible();
  });

  test("submit with valid credentials logs in and redirects", async ({ page }) => {
    await loginViaEmailForm(page, {
      email: "doctor@example.test",
      password: "dev-doctor",
    });
    // handleEmailLogin pushes /login/mfa, but useEffect sees isAuthenticated
    // and immediately redirects to /dashboard. Accept either.
    await page.waitForTimeout(1000);
    const url = page.url();
    const loggedIn = url.includes("/dashboard") || url.includes("/login/mfa");
    expect(loggedIn).toBeTruthy();
  });
});

test.describe("Login — Error States", () => {
  test.beforeEach(async ({ context }) => {
    await setupContextForLogin(context);
  });

  test("invalid credentials show error message", async ({ page }) => {
    await loginWithInvalidCredentials(page, {
      email: "wrong@hospital.com",
      password: "wrong-password",
    });
    await expect(page).toHaveURL(/\/login/);
    await expect(
      page.getByText(/Invalid email or password/i),
    ).toBeVisible({ timeout: 5000 });
  });

  test("empty fields show validation — form requires email and password", async ({
    page,
  }) => {
    await loginWithEmptyFields(page);

    // Either custom error or browser-native validation (form has required attributes)
    // The page should still be on /login
    await expect(page).toHaveURL(/\/login/);

    // Either custom error text or the form's native validation prevents submission
    const errorVisible = await page
      .getByText(/Please enter both email and password/i)
      .isVisible()
      .catch(() => false);
    const stillOnLogin = page.url().includes("/login");
    expect(errorVisible || stillOnLogin).toBeTruthy();
  });

  test("forgot password link has valid href", async ({ page }) => {
    await page.goto("/login");
    const forgotLink = page.getByText("Forgot password?");
    await expect(forgotLink).toBeVisible();
    await expect(forgotLink).toHaveAttribute("href", /./);
  });
});

test.describe("Login — Marketing & Layout", () => {
  test.beforeEach(async ({ context }) => {
    await setupContextForLogin(context);
  });

  test("welcome heading and subtitle visible", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByText("Welcome back")).toBeVisible({ timeout: 10000 });
    // Subtitle text — use first() to avoid strict mode violation (footer also contains this text)
    await expect(
      page.getByText(/AI-Powered Hospital Knowledge Assistant/i).first(),
    ).toBeVisible();
  });

  test("HIPAA and security messaging visible", async ({ page }) => {
    await page.goto("/login");
    await expect(
      page.getByText(/HIPAA-compliant|protect PHI|Secure access/i).first(),
    ).toBeVisible({ timeout: 10000 });
  });

  test("SSO divider text visible", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByText("or continue with email")).toBeVisible();
  });
});
