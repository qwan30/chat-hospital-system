# Documents UI contract task report

## Scope delivered

- Added `isDocumentReadyForRetrieval` as the shared UI contract for `ready`,
  `ready_with_warnings`, and legacy `indexed` document states.
- Made document detail page/intelligence/page-text requests and patient status
  coloring use that contract; the Documents side-rail now counts all ready
  states together.
- Added friendly `Ready` and `Ready with warnings` badges while preserving
  existing shared badge mappings.
- Removed the implicit Alice UUID fallback from document search. The entry page
  now requires an explicit Patient UUID, search routes do not run for q-only
  legacy links, and UI text accurately describes patient-scoped authorization.
- Removed the unsupported DICOM SR upload claim; supported UI formats are PDF,
  DOCX, JPG/PNG scans, and HL7 v2.

## TDD evidence

- RED: `bun run test -- src/lib/document-status.test.ts src/components/hms/StatusBadge.test.tsx src/routes/-documents-search.test.ts` failed before implementation because the helper and search guard were missing and the warning status used only the generic fallback.
- GREEN: the same command passed with 17 files / 126 tests.

## Additional validation

- `bun run typecheck` passed.
- `bun run lint` passed after formatting the owned files.
- GitNexus impact before edits: `StatusBadge` was CRITICAL (6 direct consumers, 5 flows); each affected Documents route was LOW. Regression tests preserve all known badge states.
- GitNexus staged change detection and `git diff --check` are run before commit.

## Boundary notes

- No API route, backend permission rule, authentication code, upload handler, or DICOM support was changed.
- q-only historical deep links remain renderable, but do not trigger a search until an explicit patient scope is supplied.

## Review follow-up

- Independent review found that a route navigation could call the search
  mutation with stale React state even though URL parameters were valid.
- The mutation now accepts `DocumentSearchRequest` directly. Both route-param
  auto-search and manual submission build an explicit, trimmed payload at the
  call site; route state also synchronizes when search parameters change.
- Added regression tests that assert the mutation receives the current URL
  patient scope and that q-only links submit nothing.
- Follow-up validation: focused Vitest passed with 17 files / 128 tests;
  typecheck and lint passed.

## Route-level regression follow-up

- The final review required a component-level navigation regression, not only
  a pure mutation-helper assertion. `DocumentSearchPage` now owns the route
  behavior while the route wrapper supplies validated search parameters.
- A jsdom component test renders that page with one QueryClient, rerenders it
  with a new URL query/patient scope, and verifies exactly one API mutation
  carries the new scope. It also verifies that a q-only legacy URL makes zero
  API calls.
- Focused validation passed with 18 files / 130 tests, followed by typecheck.
