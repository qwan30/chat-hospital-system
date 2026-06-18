import type { Page } from "@playwright/test";

/**
 * Seed the mock-session localStorage entry before the app boots so the
 * `_app` gate doesn't redirect us to /auth/login.
 */
export async function seedSession(
  page: Page,
  role: string = "cardiologist",
  workspaceId: string = "ws-cardio-4n",
) {
  await page.addInitScript(
    ({ role, workspaceId }) => {
      localStorage.setItem("hms.session", JSON.stringify({ role, workspaceId }));
    },
    { role, workspaceId },
  );
}

/**
 * Returns the number of assistant messages currently on screen.
 * We count by the Send button form siblings — but simpler: count by role
 * "article" if available, else fall back to a known wrapper. Tests use the
 * citation-chip / user-bubble heuristic via testid where set.
 */
export async function countMessages(page: Page) {
  // Each ChatMessage renders the message content; we use the [data-msg-role]
  // attribute injected by the test seam in ChatMessage.
  return page.locator("[data-msg-role]").count();
}
