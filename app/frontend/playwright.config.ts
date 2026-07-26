import { defineConfig, devices } from "@playwright/test";

const PORT = Number(process.env.PORT ?? 8082);
const BASE_URL = process.env.E2E_BASE_URL ?? `http://localhost:${PORT}`;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  // One retry absorbs backend-contention flake. Measured on this suite: a page
  // that renders its table in ~2.2s and its dashboard greeting in ~1.9s when
  // run alone will blow a 5s assertion timeout once six workers hammer a single
  // dev backend concurrently. Serial re-runs of those "failures" passed 35/36.
  retries: 1,
  // Cap concurrency for the same reason -- the bottleneck is the single backend
  // on :8000, not local CPU, so more workers only deepen the queue.
  workers: process.env.CI ? 2 : 4,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: BASE_URL,
    trace: "retain-on-failure",
    actionTimeout: 15_000,
    // Videos for every passing test cost minutes of wall-clock and hundreds of
    // MB; failures are what we actually inspect.
    video: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: process.env.E2E_BASE_URL
    ? undefined
    : {
        command: `bun run dev --port ${PORT}`,
        url: BASE_URL,
        reuseExistingServer: !process.env.CI,
        timeout: 120_000,
      },
});
