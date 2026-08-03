# Deployment Task 5 Report

Date: 2026-08-03
Branch: `feat/deployment-tasks-5-6`
Base: `062ed94`

## Scope completed

- Unified the frontend API-base contract around the same resolved URL for:
  - `apiFetch` / `getBaseUrl`
  - `AuthProvider` login and `/auth/me`
  - `getStoredApiUrl` consumers in chat
  - blob fetches
  - `POST /chat/stream`
- Preserved the local fallback contract:
  - local browser fallback is `/api`
  - Vite rewrites `/api` to `/api/v1`
- Preserved the authoritative production/preview contract:
  - non-empty `VITE_API_URL` is used as-is
  - no `/api/v1` suffix is appended or inferred
  - stale `hospital_ai_api_url` localStorage values cannot override a non-empty build-time `VITE_API_URL`
- Kept bearer tokens memory-only and updated stale comments accordingly.
- Completed the public bundle scanner:
  - default target is `app/frontend/.vercel/output`
  - recursive scan
  - explicit directory override supported
  - nonzero failure when target is missing
  - nonzero failure when secret markers are detected
  - deterministic built-in fixture self-test added
- Updated environment documentation with exact local/preview/production API paths and explicit backend CORS origins.

## Files changed

- `app/frontend/src/lib/api-client.ts`
- `app/frontend/src/lib/auth-context.tsx`
- `app/frontend/src/lib/api-client.test.ts`
- `app/frontend/src/lib/auth-context.test.tsx`
- `app/frontend/src/lib/stream-client.test.ts`
- `app/frontend/scripts/verify-public-bundle.mjs`
- `app/frontend/package.json`
- `docs/10-deployment/env-variables.md`

## Verification run

Focused tests:

- `bun run test -- src/lib/api-client.test.ts src/lib/auth-context.test.tsx src/lib/stream-client.test.ts`
  - Result: pass
  - Coverage in scope:
    - build-time API URL precedence over stale localStorage
    - local `/api` fallback behavior
    - auth token remains out of localStorage
    - SSE endpoint path and bearer header preservation
    - existing abort behavior preserved

Scanner checks:

- `node scripts/verify-public-bundle.mjs --self-test`
  - Result: pass
- `node scripts/verify-public-bundle.mjs .vercel/output`
  - Result: pass after local build

Frontend verification:

- `bun run typecheck`
  - Result: pass
- `bun run lint`
  - Result: pass
- `$env:VITE_API_URL='https://api.example.com/api/v1'; bun run build`
  - Result: pass
  - Output included `.vercel/output`, which was then scanned successfully

## Notes

- No provider provisioning or outbound deployment actions were performed.
- Task 6 files were not edited.
- `AGENTS.md` and `CLAUDE.md` were not edited.

## Result

Task 5 implementation is complete and locally verified.
