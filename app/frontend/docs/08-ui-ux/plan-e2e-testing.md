# Plan: E2E Testing — 3-Agent Pipeline

**Source**: Frontend rebuild commit `8200b41` (175 files, 19 routes, 97 components)
**Complexity**: Medium
**Language**: TypeScript
**Framework**: Next.js 16 + Playwright

## Summary

The frontend has been fully rebuilt with 19 routes across 10 modules. This plan covers E2E testing across 3 specialized agents: one writes Playwright tests for critical user flows, one reviews test quality and coverage, and one performs browser-based UI/UX verification simulating a human reviewer.

## Scope

19 routes across these modules:
- Auth: `/login`, `/login/mfa`
- Dashboard: `/dashboard`
- Patients: `/patients`, `/patients/[id]`, `/patients/[id]/summary`, `/patients/[id]/meds`, `/patients/[id]/denied`
- Chat: `/chat`, `/chat/new`, `/chat/[id]`
- Documents: `/documents`, `/documents/upload`, `/documents/[id]`, `/documents/[id]/review`
- Audit: `/audit`
- Metrics: `/metrics`
- Settings: `/settings`

---

## Step 1 — Write Playwright E2E Tests

**Intent**: Generate a complete Playwright E2E test suite covering all 19 routes. Each test verifies that the page renders without errors, key interactive elements are present, and navigation works. Focus on critical user flows: login -> dashboard -> patient list -> patient overview -> AI summary, chat landing -> new thread -> send message, documents -> upload, audit events, metrics charts, settings form.

**Tags**: `test`

**Chain**: `e2e-runner`

**Acceptance**:
- Playwright config created with Chromium, viewport 1440x900
- All 19 routes have at minimum a smoke test (page loads, no console errors)
- Critical flows (login, patient overview, chat thread, document upload) have multi-step interaction tests
- Tests run with `npx playwright test` and produce HTML report

**Out of scope**: Visual regression/screenshot diffing, mobile viewport testing, performance profiling.

---

## Step 2 — Review E2E Test Quality & Coverage

**Intent**: Review the generated Playwright tests for completeness, correct selectors, proper assertions, flakiness risks, and edge case coverage. Verify that all critical user flows are tested and that tests follow Playwright best practices (auto-waiting, test isolation, fixture usage).

**Tags**: `review`, `test`

**Chain**: `typescript-reviewer,code-reviewer`

**Acceptance**:
- No hardcoded waits (`page.waitForTimeout`) — use auto-waiting instead
- Selectors use `getByRole`/`getByText`/`getByLabel` (accessible) over CSS
- Each test is self-contained and does not depend on other test state
- Error paths and empty states are tested where applicable

**Out of scope**: Unit test review (already passing), backend API integration tests.

---

## Step 3 — Browser-Based UI/UX Human Review

**Intent**: Launch each page in a real Chromium browser, inspect the rendered UI against the Figma design specs, and report any visual discrepancies, layout issues, missing elements, or usability problems. Act as a human QA reviewer would — check colors, spacing, typography, responsive behavior, loading states, error states, and interactive feedback (hover, focus, click).

**Tags**: `test`, `review`

**Chain**: `e2e-runner,typescript-reviewer`

**Acceptance**:
- Every route screenshot captured and compared against Figma design tokens (colors, spacing, typography)
- Report generated listing: misaligned elements, missing components, color/token mismatches, broken interactions
- Loading skeletons, error states, and empty states verified on each page
- Keyboard navigation and focus states validated

**Out of scope**: Cross-browser testing (Safari, Firefox), mobile responsive testing, accessibility WCAG audit.
