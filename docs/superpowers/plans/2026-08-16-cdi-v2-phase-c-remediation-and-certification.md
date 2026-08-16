# CDI V2 Phase C — Production Remediation & Certification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete Phase C (Tasks 8–11) of the CDI V2 roadmap following the promotion of PR A (`d528c43` to `main`), establishing an authoritative runtime source-of-truth across backend services, sanitizing all P1/P2 frontend error and auth routes, hardening server-side audit boundaries, and generating a SHA-bound production certification report for PR B.

**Architecture:** Implement a single source-of-truth identity contract `(document_id, active_generation_id)` across Document, Dashboard, Vector Metrics, Chat, and Graph services; sanitize frontend error states and secure SSO callback query parameters; enforce strict role-based audit access server-side; execute full regression test suites.

**Tech Stack:** FastAPI, SQLAlchemy/Alembic, PostgreSQL/pgvector, Pydantic v2, TanStack Start/React, TypeScript, Bun, Vitest, Playwright, Pytest.

## Global Constraints
## Strict Output & Quality Guarantees
- **Exact File Editing:** Only the exact files listed under the 'Files' section of each task may be modified. No wildcard editing.
- **TDD Coverage Guarantee:** Every newly implemented function, route, or UI component must have 100% line coverage verified in its respective unit/integration test.
- **Type Safety Guarantee:** Zero ny types allowed in TypeScript. Zero missing type hints in Python routes.
- **Error Handling Guarantee:** Zero raw JSON errors leaked to the frontend. All UI error states must be caught by an ErrorBoundary and mapped to human-readable text.
- **Git State:** Every task must end with a single, clean commit containing only its approved files.


- Never commit directly to `main`; work on branch `fix/production-evidence-and-audit-gates`.
- Preserve existing dirty files in worktree (`AGENTS.md`, `CLAUDE.md`, `.tmp-ci-*`, `.tmp-pytest-retrieval/`, synthetic E2E files).
- All fixtures, logs, and traces must use synthetic/de-identified data only.
- Strict TDD (RED → GREEN → REFACTOR) for every task.
- Zero raw error JSON or exceptions displayed to frontend users.

---

### Task 8: Backend & Frontend Runtime Source of Truth (`(document_id, generation_id)`)

**Files:**
- Create: `app/backend/tests/test_runtime_source_of_truth.py`
- Modify: `app/backend/src/hospital_ai/api/routes/metrics_endpoint.py`
- Modify: `app/backend/src/hospital_ai/api/routes/dashboard.py`
- Modify: `app/backend/src/hospital_ai/api/routes/documents.py`
- Modify: `app/backend/src/hospital_ai/api/routes/graph.py`
- Modify: `app/frontend/src/routes/_app.integrations.vector-index.tsx`
- Modify: `app/frontend/src/lib/api/metrics.ts`

**Interfaces:**
- Consumes: `session_and_settings`, `create_indexed_document`, `db_session`, `active_user`.
- Produces: `GET /metrics/vector` endpoint returning `{ indexed_document_count: int, active_chunk_count: int, sources: list[dict] }`; `generation_id` field on document and dashboard payloads.

- [ ] **Step 1: Write failing backend integration test for unified source of truth**

```python
# app/backend/tests/test_runtime_source_of_truth.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_runtime_source_identity_cross_surface_contract(client: AsyncClient, auth_headers_cardiologist, seeded_patient_document):
    patient_id, doc_id, gen_id = seeded_patient_document
    
    # 1. Documents detail exposes active generation
    doc_res = await client.get(f"/documents/{doc_id}", headers=auth_headers_cardiologist)
    assert doc_res.status_code == 200
    doc_data = doc_res.json()
    assert doc_data["id"] == doc_id
    assert doc_data.get("active_generation_id") == gen_id

    # 2. Vector metrics endpoint exposes live count and matching source
    vec_res = await client.get("/metrics/vector", headers=auth_headers_cardiologist)
    assert vec_res.status_code == 200
    vec_data = vec_res.json()
    assert vec_data["indexed_document_count"] >= 1
    assert any(s["document_id"] == doc_id and s["generation_id"] == gen_id for s in vec_data["sources"])

    # 3. Dashboard summary uses live document source counts
    dash_res = await client.get("/dashboard/summary", headers=auth_headers_cardiologist)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert dash_data["document_stats"]["indexed_documents"] >= 1

    # 4. Graph endpoint exposes matching generation provenance
    graph_res = await client.get(f"/graph/patient/{patient_id}", headers=auth_headers_cardiologist)
    assert graph_res.status_code == 200
    graph_data = graph_res.json()
    assert all(node.get("generation_id") in [None, gen_id] for node in graph_data.get("nodes", []))
```

- [ ] **Step 2: Run test to verify it fails (RED)**

Run: `cd app/backend && pytest tests/test_runtime_source_of_truth.py -v`
Expected: FAIL with 404 on `/metrics/vector` or missing `active_generation_id`.

- [ ] **Step 3: Implement minimal backend routes and schemas (GREEN)**

In `app/backend/src/hospital_ai/api/routes/metrics_endpoint.py`:
Add `GET /metrics/vector` endpoint querying `Document` and `DocumentChunk` where `status = 'ready'` and filtered by user's patient permissions.

In `app/backend/src/hospital_ai/api/routes/documents.py`:
Expose `active_generation_id` in `DocumentDetailResponse`.

In `app/frontend/src/routes/_app.integrations.vector-index.tsx`:
Remove hardcoded `48,221` and `1.42M` cards; wire `getVectorMetrics()` API client query with loading and empty states.

- [ ] **Step 4: Run test to verify it passes (GREEN)**

Run: `cd app/backend && pytest tests/test_runtime_source_of_truth.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/backend/tests/test_runtime_source_of_truth.py app/backend/src/hospital_ai/api/routes/metrics_endpoint.py app/backend/src/hospital_ai/api/routes/documents.py app/frontend/src/routes/_app.integrations.vector-index.tsx
git commit -m "feat(backend): establish unified runtime source-of-truth contract across metrics and documents"
```

---

### Task 9: P1 Frontend Error Sanitization & Route Boundaries

**Files:**
- Modify: `app/frontend/src/lib/stream-client.ts`
- Modify: `app/frontend/src/lib/stream-client.test.ts`
- Modify: `app/frontend/src/routes/_app.chat.index.tsx`
- Modify: `app/frontend/src/lib/errors.ts`
- Modify: `app/frontend/src/lib/errors.test.ts`
- Modify: `app/frontend/src/routes/_app.audit.index.tsx`
- Modify: `app/frontend/src/routes/_app.access-requests.$requestId.review.tsx`
- Modify: `app/frontend/src/routes/_app.access-requests.$requestId.tsx`
- Modify: `app/frontend/src/routes/_app.documents.$documentId.tsx`
- Modify: `app/frontend/src/routes/_app.graph.patients.$patientId.tsx`
- Modify: `app/frontend/src/routes/auth.sso.callback.tsx`
- Create: `app/frontend/src/routes/auth.sso.callback.test.ts`

- [ ] **Step 1: Write failing Vitest tests for Error & SSO helpers (RED)**

```typescript
// app/frontend/src/routes/auth.sso.callback.test.ts
import { describe, it, expect, vi } from 'vitest';
import { sanitizeSsoCallbackUrl, getSsoCallbackState } from './auth.sso.callback';

describe('SSO Callback Fail-Closed & URL Sanitization', () => {
  it('identifies unconfigured state and cleans query/hash from history', () => {
    const replaceStateSpy = vi.spyOn(window.history, 'replaceState');
    const state = getSsoCallbackState('?code=secret_code&state=xyz#token=123');
    expect(state).toBe('unconfigured');
    
    sanitizeSsoCallbackUrl();
    expect(replaceStateSpy).toHaveBeenCalledWith({}, '', window.location.pathname);
  });
});
```

- [ ] **Step 2: Run Vitest to verify failure (RED)**

Run: `cd app/frontend && bun run test src/routes/auth.sso.callback.test.ts`
Expected: FAIL

- [ ] **Step 3: Implement Error Sanitization & Route Protections (GREEN)**

1. `stream-client.ts`: Map 401/403/422/429/5xx transport errors to human-readable strings; never emit raw JSON or stack traces.
2. `errors.ts`: Implement `safeApiErrorMessage(err)` returning generic safe messages for non-admin viewers.
3. `_app.audit.index.tsx`: Use `safeApiErrorMessage` on fetch failure.
4. `_app.access-requests.$requestId.review.tsx`: Disable automatic query retry on 401/403/404; restrict review route rendering to `admin` and `security` roles.
5. `_app.documents.$documentId.tsx`: Wrap document detail in an accessible retryable error card when 404 or fetch fails.
6. `_app.graph.patients.$patientId.tsx`: Add explicit `EmptyState` component when `!patientGraph` or nodes are empty, with a "Retry graph" button.
7. `auth.sso.callback.tsx`: Remove infinite fake timer; fail-closed immediately; call `history.replaceState` to scrub sensitive `code`/`state` from browser history.

- [ ] **Step 4: Run frontend tests, typecheck & lint (GREEN)**

Run: `cd app/frontend && bun run test && bun run typecheck && bun run lint`
Expected: All tests PASS, 0 type errors, 0 lint warnings.

- [ ] **Step 5: Commit**

```bash
git add app/frontend/src/lib/stream-client.ts app/frontend/src/lib/errors.ts app/frontend/src/routes/
git commit -m "fix(frontend): sanitize error boundaries, secure SSO history, and add retryable states"
```

---

### Task 10: P2 Consistency Gaps & Server-Side Audit Hardening

**Files:**
- Modify: `app/backend/src/hospital_ai/api/routes/audit.py`
- Modify: `app/backend/src/hospital_ai/schemas/audit.py`
- Create: `app/backend/tests/test_audit_authorization_boundary.py`
- Modify: `app/frontend/src/routes/_app.dashboard.index.tsx`
- Modify: `app/frontend/src/routes/_app.chat.history.tsx`

- [ ] **Step 1: Write failing backend test for audit role enforcement & redaction (RED)**

```python
# app/backend/tests/test_audit_authorization_boundary.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_audit_endpoint_strict_rbac_and_field_redaction(client: AsyncClient, auth_headers_doctor, auth_headers_admin):
    # 1. Non-admin / non-security role is blocked
    res_doc = await client.get("/audit", headers=auth_headers_doctor)
    assert res_doc.status_code == 403
    assert "detail" in res_doc.json()

    # 2. Admin receives sanitized audit logs with sensitive metadata redacted
    res_adm = await client.get("/audit", headers=auth_headers_admin)
    assert res_adm.status_code == 200
    logs = res_adm.json()["items"]
    for log in logs:
        assert "access_token" not in str(log)
        assert "password" not in str(log)
        assert "raw_prompt_phi" not in str(log)
```

- [ ] **Step 2: Run test to verify it fails (RED)**

Run: `cd app/backend && pytest tests/test_audit_authorization_boundary.py -v`
Expected: FAIL

- [ ] **Step 3: Implement server-side audit RBAC, field redaction & dashboard degraded banner (GREEN)**

1. `audit.py`: Require `SecurityRole.ADMIN` or `SecurityRole.SECURITY_AUDITOR` on `GET /audit`. Redact sensitive dictionary keys in `event_metadata`.
2. `_app.dashboard.index.tsx`: Show a subtle degraded banner when backend health check returns `status == 'degraded'` or indexed document count is 0.

- [ ] **Step 4: Run test to verify it passes (GREEN)**

Run: `cd app/backend && pytest tests/test_audit_authorization_boundary.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/backend/src/hospital_ai/api/routes/audit.py app/backend/tests/test_audit_authorization_boundary.py app/frontend/src/routes/_app.dashboard.index.tsx
git commit -m "fix(audit): enforce server-side RBAC and metadata redaction on audit trail"
```

---

### Task 11: Full Automation Verification & Production Certification Report

**Files:**
- Create: `docs/09-testing/production-certification-final.md`
- Modify: `docs/09-testing/evidence/c01-c50-registry.yaml`

- [ ] **Step 1: Execute complete backend test & contract verification**

Run: `cd app/backend && python -m pytest tests/ -q && python scripts/verify_contracts.py && ruff check src/ tests/`
Expected: All backend tests PASS, contracts verified, 0 lint errors.

- [ ] **Step 2: Execute complete frontend verification & E2E**

Run: `cd app/frontend && bun run typecheck && bun run lint && bun run test -- --run && bun run test:e2e`
Expected: Typecheck 0 errors, lint 0 errors, Vitest & Playwright E2E PASS.

- [ ] **Step 3: Generate SHA-bound Production Certification Report**

Create `docs/09-testing/production-certification-final.md` recording:
- Exact Git commit SHA
- Test results for all C01–C50 cases with commands and exit codes
- Final Release Decision: PASS (or explicit caveats)

- [ ] **Step 4: Commit & Prepare PR B**

```bash
git add docs/09-testing/production-certification-final.md docs/09-testing/evidence/c01-c50-registry.yaml
git commit -m "docs(certification): complete Phase C remediation and production certification report"
```
