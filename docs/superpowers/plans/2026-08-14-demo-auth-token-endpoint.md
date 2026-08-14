# Backend-Issued Demo Authentication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the frontend-generated Demo Role bearer flow with backend-issued, short-lived JWT demo sessions while preserving Real Login and synthetic-data boundaries.

**Architecture:** The backend exposes `/auth/demo/status` and `/auth/demo`. The status endpoint is authoritative for UI visibility; the login endpoint maps an allowlisted persona to a seeded synthetic user and signs a restricted HS256 JWT. The frontend calls those contracts, keeps the bearer in memory, and lets the existing `SessionProvider` map the verified identity into the current persona UI.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy async sessions, PyJWT, React 19, TanStack Start, TypeScript, Vitest, Playwright, pytest.

## Global Constraints

- Preserve the existing `Real Login` tab and `/auth/token` contract.
- Demo Role must never accept an arbitrary email, user ID, patient ID, permission scope, or workspace from the browser.
- Demo issuance requires `demo_mode=true` and a non-empty backend-only `HOSPITAL_AI_DEMO_JWT_SECRET`.
- Demo JWTs must expire; default lifetime is 30 minutes and configuration is bounded to 5–1440 minutes.
- Use synthetic or de-identified data only; do not add secrets, real patient data, or real credentials.
- Bearer tokens remain in frontend memory only; API URL persistence remains unchanged.
- Preserve unrelated dirty files (`AGENTS.md`, `CLAUDE.md`, `.tmp-*`, and synthetic E2E fixtures) and stage only owned files.
- Follow RED → GREEN → REFACTOR for each production behavior and run the covering test after every implementation step.

---

### Task 1: Backend demo-auth contract and JWT validation

**Files:**
- Modify: `app/backend/src/hospital_ai/core/config.py`
- Modify: `app/backend/src/hospital_ai/schemas/auth.py`
- Modify: `app/backend/src/hospital_ai/services/jwt_auth.py`
- Modify: `app/backend/src/hospital_ai/api/deps.py`
- Modify: `app/backend/src/hospital_ai/api/routes/auth.py`
- Test: `app/backend/tests/test_auth.py`
- Test: `app/backend/tests/test_audit_2026_05.py`
- Modify: `app/backend/.env.example`

**Interfaces:**
- `DemoLoginRequest(role: DemoRole)` and `DemoStatusResponse(enabled: bool)` are public schemas.
- `GET /auth/demo/status` returns `{ "enabled": boolean }`.
- `POST /auth/demo` returns the existing `TokenResponse`.
- `JwtAuthService.validate_demo_token(token)` returns `JwtTokenData | None`.

- [ ] **Step 1: Write failing backend tests.**

Add tests for status gating, valid cardiologist issuance, `demo=true`/issuer/exp claims, disabled mode, invalid role validation, demo JWT lookup through `get_current_user`, and rejection after `demo_mode` is disabled. Configure the fixture with `demo_jwt_secret="demo-test-secret"` and `demo_jwt_issuer="test-demo-issuer"`.

```python
claims = jwt.decode(
    response.access_token,
    settings.demo_jwt_secret,
    algorithms=["HS256"],
    issuer=settings.demo_jwt_issuer,
    options={"verify_aud": False},
)
assert claims["demo"] is True
assert claims["email"] == "doctor@example.test"
assert claims["exp"] > claims["iat"]
```

- [ ] **Step 2: Run RED.**

```powershell
cd app/backend
python -m pytest tests/test_auth.py -q
```

Expected: failure because the new settings, schemas, endpoint, and validator do not exist.

- [ ] **Step 3: Add settings and schemas.**

Add `demo_jwt_secret: str = Field(default="", repr=False)`, `demo_jwt_issuer: str = "hospital-ai-demo"`, and `demo_token_ttl_minutes: int = Field(default=30, ge=5, le=1440)` to `Settings`. Add `DemoRole = Literal["cardiologist", "hospitalist", "rn", "pharmacist", "front_desk", "admin", "security"]`, `DemoLoginRequest`, and `DemoStatusResponse` to `schemas/auth.py`.

- [ ] **Step 4: Add demo JWT validation without weakening HMS JWT validation.**

Implement `JwtAuthService.validate_demo_token()` with HS256, the demo secret/issuer, expiration verification, and safe `None` returns for malformed/expired/disabled tokens. In `get_current_user`, validate normal JWTs first and demo JWTs second only when `settings.demo_mode` is true; resolve the returned email against an active local user exactly as the normal JWT path does.

- [ ] **Step 5: Add the backend endpoints.**

In `auth.py`, use this allowlist and no client-supplied identity fields:

```python
DEMO_ROLE_EMAILS = {
    "cardiologist": "doctor@example.test",
    "hospitalist": "doctor@example.test",
    "rn": "nurse@example.test",
    "pharmacist": "pharmacist@example.test",
    "front_desk": "records@example.test",
    "admin": "admin@example.test",
    "security": "security@example.test",
}
```

`GET /demo/status` is enabled only when `demo_mode` and the secret are truthy. `POST /demo` is rate-limited to `10/minute`, returns 403 when disabled, 503 when the secret or seeded active user is unavailable, and signs `{sub, email, name, role, demo: True, iss, iat, exp}`. Never expose secret/database details.

- [ ] **Step 6: Run GREEN/refactor checks.**

```powershell
cd app/backend
python -m pytest tests/test_auth.py tests/test_audit_2026_05.py -q
ruff check src/ tests/
ruff format --check src/ tests/
```

Add the four demo variables, with backend-only secret comments, to `.env.example`. Refactor only while tests remain green.

- [ ] **Step 7: Commit backend work.**

```powershell
git add app/backend/src/hospital_ai/core/config.py app/backend/src/hospital_ai/schemas/auth.py app/backend/src/hospital_ai/services/jwt_auth.py app/backend/src/hospital_ai/api/deps.py app/backend/src/hospital_ai/api/routes/auth.py app/backend/tests/test_auth.py app/backend/tests/test_audit_2026_05.py app/backend/.env.example
git commit -m "feat(auth): issue restricted demo JWTs from backend"
```

### Task 2: Frontend Demo Role integration and UI gating

**Files:**
- Modify: `app/frontend/src/lib/auth-context.tsx`
- Modify: `app/frontend/src/routes/auth.login.tsx`
- Test: `app/frontend/src/lib/auth-context.test.tsx`
- Test: `app/frontend/e2e/auth-flow.spec.ts`

**Interfaces:**
- `useAuth()` exposes `demoEnabled`, `demoStatusLoading`, `demoError`, and `demoLogin(role: Role): Promise<boolean>`.
- `demoLogin()` posts `{ role }`, verifies the returned token using `/auth/me`, stores it only through `persistToken`, and records the selected persona in memory.

- [ ] **Step 1: Write failing frontend tests.**

Test that status `{enabled:true}` is loaded, `demoLogin("cardiologist")` posts exactly `{role:"cardiologist"}`, verifies `/auth/me`, sets the memory token, and never writes the bearer to localStorage. Test that a status/network failure fails closed and leaves `demoEnabled=false`.

```typescript
expect(init?.method).toBe("POST");
expect(JSON.parse(String(init?.body))).toEqual({ role: "cardiologist" });
expect(captured?.token).toBe("demo-jwt");
expect(getMockStore()).not.toHaveProperty("hospital_ai_token");
```

- [ ] **Step 2: Run RED.**

```powershell
cd app/frontend
bun run test -- src/lib/auth-context.test.tsx
```

Expected: failure because the new context state and method do not exist.

- [ ] **Step 3: Implement AuthProvider demo state.**

Fetch `/auth/demo/status` after hydration and default to disabled on non-2xx/network errors. Implement `demoLogin(role)` with the JSON POST, memory-only token persistence, `/auth/me` verification, selected-persona state, and cleanup on verification failure. Do not alter Real Login or API URL persistence.

- [ ] **Step 4: Update the login route.**

Remove `signIn` from the Demo Role handler. Render the Demo Role tab/content only when enabled, keep Real Login unchanged, call `await demoLogin(role)`, and navigate only on success. Show a safe error without navigating on failure. Preserve role/workspace visuals.

- [ ] **Step 5: Update browser auth evidence.**

Stub `**/auth/demo/status`, `POST **/auth/demo`, and `GET **/auth/me` in `auth-flow.spec.ts`. Add a disabled-status test asserting Demo Role is absent and Real Login remains visible. Keep click-based navigation assertions and verify the bearer is not written to storage. Existing business-flow seed helpers remain test-only compatibility fixtures and are not called by the production login route.

- [ ] **Step 6: Run frontend checks.**

```powershell
cd app/frontend
bun run test -- src/lib/auth-context.test.tsx src/lib/session.test.tsx
bun run typecheck
bun run lint
```

- [ ] **Step 7: Commit frontend work.**

```powershell
git add app/frontend/src/lib/auth-context.tsx app/frontend/src/routes/auth.login.tsx app/frontend/src/lib/auth-context.test.tsx app/frontend/e2e/auth-flow.spec.ts
git commit -m "feat(auth): route Demo Role through backend token issuance"
```

### Task 3: Documentation and contract evidence

**Files:**
- Modify: `docs/10-deployment/env-variables.md`
- Modify: `docs/05-api/api-overview.md`
- Modify: `docs/09-testing/test-plan.md`
- Test: `app/backend/tests/test_auth_contracts.py`

- [ ] **Step 1: Write failing documentation contract assertions.**

Create a focused test that reads the three docs and requires `/auth/demo/status`, `POST /auth/demo`, `HOSPITAL_AI_DEMO_MODE`, `HOSPITAL_AI_DEMO_JWT_SECRET`, short-lived tokens, synthetic data, and the statement that secrets remain backend-only.

- [ ] **Step 2: Run RED.**

```powershell
cd app/backend
python -m pytest tests/test_auth_contracts.py -q
```

Expected: failure because the docs do not yet describe the new contract.

- [ ] **Step 3: Update docs and run GREEN.**

Document request/response/error behavior, local/staging configuration using synthetic values only, the difference between Demo JWT and HMS/OIDC Real Login, and evidence needed before claiming the demo works.

```powershell
cd app/backend
python -m pytest tests/test_auth_contracts.py -q
git diff --check
```

- [ ] **Step 4: Commit docs.**

```powershell
git add docs/10-deployment/env-variables.md docs/05-api/api-overview.md docs/09-testing/test-plan.md app/backend/tests/test_auth_contracts.py
git commit -m "docs(auth): document backend-issued demo sessions"
```

### Task 4: Full verification, review, and delivery

**Files:**
- No planned source files; fixes may touch only files identified by failed checks or review findings.

- [ ] **Step 1: Run complete backend verification.**

```powershell
cd app/backend
python -m pytest tests/ -q
ruff check src/ tests/
ruff format --check src/ tests/
python scripts/verify_contracts.py
```

- [ ] **Step 2: Run complete frontend verification.**

```powershell
cd app/frontend
bun run test
bun run typecheck
bun run lint
bun run build
```

- [ ] **Step 3: Run browser auth verification.**

```powershell
cd app/frontend
bun run test:e2e -- auth-flow.spec.ts --reporter=list
```

Capture Real Login visibility, Demo Role enabled/disabled behavior, one-click login, dashboard navigation, and no bearer in storage.

- [ ] **Step 4: Run GitNexus change-scope verification.**

Call `detect_changes({scope: "compare", base_ref: "main"})` and verify only auth/docs/tests and expected flows are affected. Review unexpected high-risk symbols before committing fixes.

- [ ] **Step 5: Request code review.**

Generate a `main..HEAD` review package and dispatch a fresh reviewer with the design/plan requirements. Fix every Critical/Important finding, rerun covering tests, and re-review before push.

- [ ] **Step 6: Push and create the PR.**

Create `docs/pr/demo-auth-token-endpoint.md` with the problem, security boundary, exact tests, synthetic-data limitation, and deployment variables, then run:

```powershell
git status --short
git push -u origin feat/demo-auth-token-endpoint
gh pr create --base main --head feat/demo-auth-token-endpoint --title "feat(auth): issue restricted demo tokens from backend" --body-file docs/pr/demo-auth-token-endpoint.md
```

The PR body must include the problem, security boundary, exact tests, synthetic-data limitation, and deployment variables. Do not claim production auth replacement or real-hospital readiness.

- [ ] **Step 7: Inspect checks/logs and fix failures.**

Resolve the PR number with `$prNumber = gh pr view --json number --jq .number`, then use `gh pr checks $prNumber --watch`. For a failed workflow, resolve `$runId = gh run list --branch feat/demo-auth-token-endpoint --limit 1 --json databaseId --jq '.[0].databaseId'` and use `gh run view $runId --log-failed`. For every failure, reproduce locally, write or extend a failing regression test, fix, run the covering suite, commit, push, and wait again. Do not merge with red or skipped required checks.

- [ ] **Step 8: Merge only when green.**

Re-query the actual PR with `gh pr view $prNumber --json state,mergeStateStatus,statusCheckRollup,url`. Merge only when checks are green, review is clean, and the branch is mergeable:

```powershell
gh pr merge $prNumber --squash --delete-branch
```

Verify the PR is merged and report local tests, remote checks, review, merge state, and deployment/log limitations separately.
