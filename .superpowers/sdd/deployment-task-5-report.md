# Deployment Task 5 Report

Date: 2026-08-03
Last updated: 2026-08-04
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
  - Original 2026-08-03 claim is superseded by the 2026-08-04 Windows CLI fix evidence below.
- `node scripts/verify-public-bundle.mjs .vercel/output`
  - Original 2026-08-03 claim is superseded by the 2026-08-04 Windows CLI fix evidence below.

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

Task 5 implementation is complete for the repository-side contract, with the
Windows CLI evidence refreshed on 2026-08-04. No external deployment is
claimed.

## Review-fix evidence

- Final-review Critical issue addressed on 2026-08-04: the CLI entrypoint is no
  longer a silent no-op on Windows. Direct execution now uses a resolved
  `pathToFileURL(path.resolve(process.argv[1]))` comparison, so
  `node scripts/verify-public-bundle.mjs ...` actually runs cross-platform.
- The dependency-free self-test now includes a real subprocess smoke test of
  the documented CLI path from `app/frontend`, pointed at a temporary failing
  bundle containing `HOSPITAL_AI_DATABASE_URL`. The self-test asserts child
  exit code `2` and output containing both the scanned path and offending
  marker.
- Recursive scanning, backend-only name/value marker detection, and explicit
  missing-target failure behavior are preserved.
- Earlier 2026-08-03 scanner claims were stale on Windows because the direct
  CLI entrypoint check did not execute there. The fresh 2026-08-04 results
  below supersede those two CLI lines only. Other 2026-08-03 Task 5 evidence in
  this report was not re-run by this final-review worker.

Focused review-fix verification:

- `node scripts/verify-public-bundle.mjs --self-test`
  - Result: pass
  - Confirms:
    - recursive scanning still works
    - backend-only DB/Redis name markers are detected
    - backend-only DB/Redis value markers are detected
    - backend-only R2/LLM/HMS/JWT name markers remain detected
    - missing-target failure remains explicit
    - documented CLI path is exercised in a real child process and fails with
      exit code `2`, the scanned path, and `HOSPITAL_AI_DATABASE_URL`
- `node scripts/verify-public-bundle.mjs .vercel/output`
  - Result: pass
  - Fresh output: `Public bundle scan passed:
    D:\projects\chatbot-hospital-system\app\frontend\.vercel\output (413
    files)`
- Manual reviewer repro from `app/frontend`
  - Command shape: `node scripts/verify-public-bundle.mjs <temp-dir>`
  - Fixture: temporary failing directory containing `env.js` with
    `HOSPITAL_AI_DATABASE_URL=leak`
  - Result: exit code `2`
  - Output included:
    - scanned temp directory path
    - offending marker `HOSPITAL_AI_DATABASE_URL`

Additional scope note:

- This final-review worker changed only
  `app/frontend/scripts/verify-public-bundle.mjs` and
  `.superpowers/sdd/deployment-task-5-report.md`.
- No build was re-run here; the existing `.vercel/output` directory was scanned
  exactly as requested.

Final contract correction:

- Local development now documents `VITE_API_URL=/api`, matching the governing
  plan and the Vite `/api` -> `/api/v1` proxy contract.
