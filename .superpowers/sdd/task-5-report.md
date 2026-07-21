# Task 5: Restrict Demo-ID Translation to Identifier Fields

## Delivered

- Replaced unconditional recursive string mapping with `mapApiIds`, a pure mapper that carries the current property key.
- Demo ID translations now apply only to `id`, keys ending in `_id`, and graph keys `from_node` and `to_node`.
- JSON request bodies are parsed, identifier fields are translated, and the resulting JSON is serialized again. Non-JSON string bodies are preserved unchanged.
- URL/path mapping remains unchanged.

## TDD evidence

### RED

Command:

```powershell
bun run test -- src/lib/api-client.test.ts --run
```

Result: 2 failures of 75 tests before implementation.

- A UUID-only `citation_text` response field was incorrectly converted to `ar-002`.
- The request `question` prose incorrectly converted embedded `p-001` and `ar-002` values to UUIDs.

### GREEN

The same focused command passed after the minimal mapper change: 9 test files and 75 tests passed.

## Verification

```powershell
bun run test
# 9 test files, 75 tests passed

bun run typecheck
# passed

bun run lint
# 0 errors; 3 pre-existing warnings remain in GraphCanvas.tsx, routeTree.gen.ts, and _app.chat.index.tsx
```

`app/frontend/src/lib/api/graph.ts` normalization produced no semantic Git diff and was reverted/not delivered.

## Self-review

- The mapper creates new arrays/objects and does not mutate request or response data.
- Array values retain their parent key, so arrays assigned to an identifier key map correctly.
- Unknown/prose keys are never scanned heuristically for UUIDs.
- Request parsing failure is intentionally swallowed only to retain the original raw body.
- `git diff --check` completed with no whitespace errors.

## Concerns

- The three remaining lint warnings are outside Task 5 scope and unchanged by this work.
- The test runner emits an existing Vite `vite-tsconfig-paths` deprecation warning.

## Coverage follow-up

The reviewer requested post-fix regression/characterization coverage for the CRITICAL `apiFetch` adapter. These cases passed the already-implemented mapper; they are not represented as a new RED cycle.

- Exact `id`, `from_node`, and `to_node` response keys translate correctly.
- Identifier arrays retain their parent key while translating each entry.
- Identifier fields nested inside response array elements translate correctly.
- Invalid JSON request bodies are forwarded byte-for-byte.
- Existing demo-ID path translation remains unchanged.

Focused and full frontend unit runs passed 80 tests. Typecheck passed. Lint completed with zero errors and the same three pre-existing warnings.
