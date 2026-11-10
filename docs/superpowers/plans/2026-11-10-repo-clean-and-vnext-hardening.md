# Repo Clean, Clinical Safety & Contract Hardening, and vNext Blueprint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clean repository dead weight and router hygiene issues, close P0/P1 API contract and clinical safety gaps (`verify_contracts.py`, `metrics.ts`, `auth.ts`, `chat.ts`, `cdss.py`, `drug_check.py`, `metrics_endpoint.py`), reduce Cyclomatic Complexity / CRAP scores on core backend hotspots (`chat_stream.py`, `upload_sessions.py`, `claim_validation.py`), wire static mock frontend routes to live BFF APIs, add unit coverage for 0%-covered loaders/providers, and deliver complete SA/BA vNext specifications in `report.md`.

**Architecture:** We execute directly on a single feature branch (`refactor/repo-clean-and-vnext-hardening`) in the active workspace without creating git worktrees. Work is partitioned into 7 non-overlapping Agent Kanban tasks (`CARD-01` through `CARD-07`) with strict file-ownership boundaries, TDD (`RED -> GREEN -> REFACTOR`) verification gates, and a final deterministic quality gate pass.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0 (AsyncSession), Pydantic, Pytest, Ruff, TanStack Start (Vite 8 + React 19 + TypeScript), Vitest, Testing Library.

**Spec:** `report.md`

## Global Constraints

- **Branch Strategy:** Execute on branch `refactor/repo-clean-and-vnext-hardening` in the root workspace (`d:\projects\chatbot-hospital-system`); do NOT create `git worktree` directories.
- **Branch Naming Rule:** Follow `<type>/<short-kebab-case>` (`refactor/repo-clean-and-vnext-hardening`); never use `codex/` or `subagent-` branch prefixes.
- **Systematic Debugging Law:** No production code fixes before reproducing the failure via an automated unit/contract test (`RED -> GREEN -> REFACTOR`).
- **Immutability & Ponytail Simplicity:** Prefer pure helper functions (`< 50` lines), zero new external dependencies, and minimal diffs.
- **Deterministic Quality Gate:** Every backend change must pass `ruff check src/ tests/`, `ruff format --check src/ tests/`, `calculate_crap_score.py`, and `verify_contracts.py`; every frontend change must pass `bun run lint`, `bun run typecheck`, `bun run test -- --run`, and `bun run build`.

## Review Focus

1. **Template literal & query-string URLs in `verify_contracts.py`:** `apiFetch(\`/patients/\${patientId}/labs\`)` and `apiFetch(\`/audit/logs?\${params.toString()}\`)` contain `${...}` expressions that naive regexes truncate at the first `/`; tested in Task 2 (`test_verify_contracts_extracts_interpolated_api_paths`).
2. **Re-indexing a document with existing acknowledged vs. unacknowledged CDSS alerts:** Re-running `run_cdss_analysis(session, document_id)` must replace unacknowledged stale alerts for that `source_document_id` without deleting clinician-acknowledged (`is_acknowledged=True`) historical alerts; tested in Task 3 (`test_cdss_re_run_is_idempotent_and_preserves_acknowledged_alerts`).
3. **Superseded or unauthorized target entities in `DrugCheckService.check_interactions` Step 1:** A `GraphRelationAssertion` whose `subject_entity_id` is an active drug in the query but whose `object_entity_id` belongs to a deleted/superseded document generation or unauthorized chunk must not emit a `DrugWarning`; tested in Task 3 (`test_check_interactions_blocks_superseded_or_unauthorized_relation_evidence`).
4. **Non-admin / non-security clinician calling `GET /api/v1/metrics/vector`:** A regular clinician role (`rn`, `front_desk`, `cardiologist`) must only see counts/sources for documents within their authorized patient scope (or be restricted if un-scoped), never leaking `document_id`s of unauthorized patients; tested in Task 3 (`test_vector_metrics_scopes_sources_to_authorized_patients`).
5. **Missing or non-UUID `traceId` in `/_app/audit/traces/$traceId` and `/_app/integrations/traces/$traceId`:** When `getQueryTrace(traceId)` rejects with `404`/`422`, the route must render an explicit error/empty state instead of crashing or silently showing another patient's static mock trace; tested in Task 5 (`TraceRouteFallback.test.tsx`).

---

## File Structure & Ownership Map

| Task / Card | Responsibility | Created Files | Modified Files | Deleted / Moved Files |
|---|---|---|---|---|
| **Task 1 (`CARD-01`)** | Branch setup, repo dead-weight cleanup, `.gitignore` hardening, TanStack Router code-split & test-file naming hygiene | `app/frontend/src/components/hms/SsoCallbackCard.tsx`, `app/frontend/src/routes/-auth.sso.callback.test.ts` | `.gitignore`, `app/frontend/src/routes/auth.sso.callback.tsx`, `app/frontend/src/routes/__root.tsx` | Delete: `.review-d90d02f.tar`, `.review-*`, `app/backend/scripts/stats.py`, `app/backend/scripts/stats2.py`, `app/backend/src/hospital_ai/rag_spike_adapter.py`, `app/frontend/src/lib/api/example.functions.ts`, `app/frontend/src/lib/lovable-error-reporting.ts`, `app/frontend/e2e/demo.cjs`, `app/frontend/e2e/discover.cjs`, `app/frontend/e2e/screenshots/page@adb81ea1325bed6a13981951de9cc079.webm`, `app/frontend/src/routes/auth.sso.callback.test.ts` |
| **Task 2 (`CARD-02`)** | Full `src/lib/api/*.ts` scanning in `verify_contracts.py` & fixing `metrics.ts` (404), `auth.ts` (422), `chat.ts` (dropped `document_ids`) | `app/backend/tests/test_verify_contracts_scanner.py`, `app/frontend/src/lib/api/client-contracts.test.ts` | `app/backend/scripts/verify_contracts.py`, `app/frontend/src/lib/api/metrics.ts`, `app/frontend/src/lib/api/auth.ts`, `app/frontend/src/lib/api/chat.ts` | — |
| **Task 3 (`CARD-03`)** | Clinical safety hardening in `workers/cdss.py`, `services/drug_check.py`, and `api/routes/metrics_endpoint.py` | — | `app/backend/src/hospital_ai/workers/cdss.py`, `app/backend/src/hospital_ai/services/drug_check.py`, `app/backend/src/hospital_ai/api/routes/metrics_endpoint.py`, `app/backend/tests/test_cdss_agent.py`, `app/backend/tests/test_drug_check.py`, `app/backend/tests/test_metrics.py` | — |
| **Task 4 (`CARD-04`)** | Decompose high-CRAP functions (`upload_sessions.create`, `claim_validation.deterministic_entailment`, `chat_stream.chat_stream`) | — | `app/backend/src/hospital_ai/services/upload_sessions.py`, `app/backend/src/hospital_ai/services/claim_validation.py`, `app/backend/src/hospital_ai/api/routes/chat_stream.py`, `app/backend/tests/cdi_v2/test_upload_sessions.py`, `app/backend/tests/cdi_v2/test_claim_validation.py`, `app/backend/tests/test_chat_stream_endpoint.py` | — |
| **Task 5 (`CARD-05`)** | Wire static mock frontend routes (`SystemHealthCard`, `ocr-queue`, `traces`) to live BFF APIs | `app/frontend/src/components/hms/SystemHealthCard.test.tsx` | `app/frontend/src/components/hms/SystemHealthCard.tsx`, `app/frontend/src/routes/_app.documents.ocr-queue.tsx`, `app/frontend/src/routes/_app.audit.traces.$traceId.tsx`, `app/frontend/src/routes/_app.integrations.traces.$traceId.tsx` | — |
| **Task 6 (`CARD-06`)** | Add unit coverage for 0%-covered document loaders (`text_loader`, `html_loader`, `excel_loader`) and LLM providers (`openai`, `ollama`, `gemini`) | `app/backend/tests/test_loaders_and_providers_unit.py` | — | — |
| **Task 7 (`CARD-07`)** | Finalize BA PRD user stories (Gherkin), SA vNext architecture blueprints, and Before/After verification matrix in `report.md` | — | `report.md` | — |

---

### Task 1: Branch Setup, Repo Cleanup & TanStack Router Hygiene (`CARD-01`)

**Files:**
- Modify: `.gitignore:33-89`
- Create: `app/frontend/src/components/hms/SsoCallbackCard.tsx`
- Modify: `app/frontend/src/routes/auth.sso.callback.tsx:1-104`
- Create: `app/frontend/src/routes/-auth.sso.callback.test.ts`
- Modify: `app/frontend/src/routes/__root.tsx:12-102`
- Delete: `app/frontend/src/routes/auth.sso.callback.test.ts`, `app/frontend/src/lib/lovable-error-reporting.ts`, `app/frontend/src/lib/api/example.functions.ts`, `app/frontend/e2e/demo.cjs`, `app/frontend/e2e/discover.cjs`, `app/frontend/e2e/screenshots/page@adb81ea1325bed6a13981951de9cc079.webm`, `app/backend/scripts/stats.py`, `app/backend/scripts/stats2.py`, `app/backend/src/hospital_ai/rag_spike_adapter.py`

**Interfaces:**
- Consumes: `@tanstack/react-router` (`createFileRoute`, `useNavigate`), `@/components/shell/AuthSplitLayout`, `@/components/hms/ErrorState`
- Produces: `export function SsoCallbackCard(): JSX.Element` in `app/frontend/src/components/hms/SsoCallbackCard.tsx` (used by `auth.sso.callback.tsx` and `-auth.sso.callback.test.ts` so `auth.sso.callback.tsx` only exports `Route`)

- [ ] **Step 1: Checkout target branch `refactor/repo-clean-and-vnext-hardening` and remove untracked/tracked clutter**

Run:
```powershell
git checkout -b refactor/repo-clean-and-vnext-hardening
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue .review-d90d02f.tar, .review-archive-7e478b8, .review-archive-d90d02f, .review-prb-20260815, .review-prb-20260815b, app/backend/.verify-pycache, app/backend/scripts/stats.py, app/backend/scripts/stats2.py, app/backend/src/hospital_ai/rag_spike_adapter.py, app/frontend/src/lib/api/example.functions.ts, app/frontend/src/lib/lovable-error-reporting.ts, app/frontend/e2e/demo.cjs, app/frontend/e2e/discover.cjs, "app/frontend/e2e/screenshots/page@adb81ea1325bed6a13981951de9cc079.webm"
```
Expected: All listed clutter files/directories are removed.

- [ ] **Step 2: Harden `.gitignore` to ignore `.venv-dev/`, `.verify-pycache/`, and `.review*`**

In `.gitignore`, append under `# Temporary test runner, CI directories & caches`:
```gitignore
.venv-dev/
.verify-pycache/
.review*
```

- [ ] **Step 3: Move `SsoCallback` component into `app/frontend/src/components/hms/SsoCallbackCard.tsx` and rename `auth.sso.callback.test.ts` to `-auth.sso.callback.test.ts`**

Move `export function SsoCallback()` from `app/frontend/src/routes/auth.sso.callback.tsx` into `app/frontend/src/components/hms/SsoCallbackCard.tsx` (keeping `export function SsoCallback()`), and update `app/frontend/src/routes/auth.sso.callback.tsx` so it only exports `Route`:
```tsx
import { createFileRoute } from "@tanstack/react-router";
import { SsoCallback } from "@/components/hms/SsoCallbackCard";

export const Route = createFileRoute("/auth/sso/callback")({
  head: () => ({ meta: [{ title: "Signing in — HMS AI Copilot" }] }),
  component: SsoCallback,
});
```
Move `app/frontend/src/routes/auth.sso.callback.test.ts` to `app/frontend/src/routes/-auth.sso.callback.test.ts` and update its import to `import { SsoCallback } from "@/components/hms/SsoCallbackCard";`.

- [ ] **Step 4: Remove `reportLovableError` and `@Lovable` metadata from `app/frontend/src/routes/__root.tsx`**

In `app/frontend/src/routes/__root.tsx`, remove `import { reportLovableError } from "../lib/lovable-error-reporting";` (line 13), remove `reportLovableError(error, { boundary: "tanstack_root_error_component" });` (line 46), and remove `{ name: "twitter:site", content: "@Lovable" },` (line 101).

- [ ] **Step 5: Verify zero TanStack Router warnings and commit**

Run: `cd app/frontend; bun run typecheck; bunx vitest run src/routes/-auth.sso.callback.test.ts --run`
Expected: PASS with `2 passed` and zero `Warning: Route file ... does not export a Route` or `will not be code-split` messages.

```powershell
git add .gitignore app/backend app/frontend
git commit -m "chore: clean repo dead weight and fix tanstack router route hygiene"
```

---

### Task 2: API Contract Gate Expansion & Frontend API Client Fixes (`CARD-02`)

**Files:**
- Create: `app/backend/tests/test_verify_contracts_scanner.py`
- Modify: `app/backend/scripts/verify_contracts.py:33-155`
- Create: `app/frontend/src/lib/api/client-contracts.test.ts`
- Modify: `app/frontend/src/lib/api/metrics.ts:9-11`
- Modify: `app/frontend/src/lib/api/auth.ts:19-25`
- Modify: `app/frontend/src/lib/api/chat.ts:1-25`

**Interfaces:**
- Consumes: `apiFetch` from `app/frontend/src/lib/api-client.ts`
- Produces:
  - `discover_frontend_scan_files(frontend_root: str) -> list[str]` in `app/backend/scripts/verify_contracts.py`
  - `getVectorMetrics(): Promise<VectorMetricsResponse>` calling `apiFetch<VectorMetricsResponse>("/metrics/vector")` in `app/frontend/src/lib/api/metrics.ts`
  - `login(email: string, password: string): Promise<TokenResponse>` sending `application/x-www-form-urlencoded` (`username`, `password`) to `/auth/token` in `app/frontend/src/lib/api/auth.ts`
  - `sendMessage(request: ChatRequest): Promise<ChatResponse>` sending `{ question: request.message, patient_id: request.patient_id, thread_id: request.thread_id, context: request.document_ids ? { patient_id: request.patient_id, document_ids: request.document_ids } : undefined }` in `app/frontend/src/lib/api/chat.ts`

- [ ] **Step 1: Write failing backend test `app/backend/tests/test_verify_contracts_scanner.py` and frontend test `app/frontend/src/lib/api/client-contracts.test.ts`**

Create `app/backend/tests/test_verify_contracts_scanner.py`:
```python
from pathlib import Path
import sys

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import verify_contracts as vc  # noqa: E402


def test_verify_contracts_extracts_interpolated_api_paths() -> None:
    frontend_root = Path(__file__).resolve().parents[2] / "frontend"
    scan_files = vc.discover_frontend_scan_files(str(frontend_root))
    assert any(f.endswith("metrics.ts") for f in scan_files)
    paths = vc.get_frontend_paths(str(frontend_root), scan_files)
    normalized = {vc.normalize_path(p) for p in paths}
    assert "/metrics/vector" in normalized
    assert "/patients/*/labs" in normalized
    assert "/audit/logs" in normalized
    assert "/api/v1/metrics/vector" not in normalized
```

Create `app/frontend/src/lib/api/client-contracts.test.ts`:
```ts
import { beforeEach, describe, expect, it, vi } from "vitest";
import * as apiClient from "../api-client";
import { getVectorMetrics } from "./metrics";
import { login } from "./auth";
import { sendMessage } from "./chat";

describe("Frontend API client contracts", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("calls /metrics/vector without duplicate /api/v1 prefix", async () => {
    const spy = vi.spyOn(apiClient, "apiFetch").mockResolvedValue({
      indexed_document_count: 1,
      active_chunk_count: 2,
      sources: [],
    });
    await getVectorMetrics();
    expect(spy).toHaveBeenCalledWith("/metrics/vector");
  });

  it("sends OAuth2 form-urlencoded username and password in login()", async () => {
    const spy = vi.spyOn(apiClient, "apiFetch").mockResolvedValue({
      access_token: "tok",
      token_type: "bearer",
      user: { id: "1", email: "doctor@example.test", full_name: "Doc", role: "cardiologist", is_active: true },
    });
    await login("doctor@example.test", "demo");
    expect(spy).toHaveBeenCalledWith("/auth/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: "username=doctor%40example.test&password=demo",
    });
  });

  it("maps message to question and nests document_ids inside context in sendMessage()", async () => {
    const spy = vi.spyOn(apiClient, "apiFetch").mockResolvedValue({
      answer: "ok",
      thread_id: "t1",
      citations: [],
    });
    await sendMessage({
      message: "Check labs",
      patient_id: "p1",
      document_ids: ["d1", "d2"],
      thread_id: "t1",
    });
    expect(spy).toHaveBeenCalledWith("/chat", {
      method: "POST",
      body: JSON.stringify({
        question: "Check labs",
        patient_id: "p1",
        thread_id: "t1",
        context: { patient_id: "p1", document_ids: ["d1", "d2"] },
      }),
    });
  });
});
```

- [ ] **Step 2: Run both tests to verify they fail**

Run:
```powershell
app/backend/.venv/Scripts/python.exe -m pytest app/backend/tests/test_verify_contracts_scanner.py -v
cd app/frontend; bunx vitest run src/lib/api/client-contracts.test.ts --run
```
Expected: FAIL (`AttributeError: module 'verify_contracts' has no attribute 'discover_frontend_scan_files'` and assertion mismatches in `client-contracts.test.ts`).

- [ ] **Step 3: Implement `metrics.ts`, `auth.ts`, `chat.ts`, and `verify_contracts.py` updates**

1. In `app/frontend/src/lib/api/metrics.ts`: change `"/api/v1/metrics/vector"` to `"/metrics/vector"`.
2. In `app/frontend/src/lib/api/auth.ts`: build `const form = new URLSearchParams({ username: email, password });` and pass `headers: { "Content-Type": "application/x-www-form-urlencoded" }, body: form.toString()` to `apiFetch<TokenResponse>("/auth/token", ...)`.
3. In `app/frontend/src/lib/api/chat.ts`: construct payload `{ question: request.message, patient_id: request.patient_id, thread_id: request.thread_id, ...(request.document_ids ? { context: { patient_id: request.patient_id, document_ids: request.document_ids } } : {}) }` and pass `JSON.stringify(payload)` to `apiFetch<ChatResponse>("/chat", ...)`.
4. In `app/backend/scripts/verify_contracts.py`:
   - Add `discover_frontend_scan_files(frontend_root: str) -> list[str]` that returns `["src/lib/api-client.ts", "src/lib/auth-context.tsx", "src/lib/stream-client.ts"]` plus all sorted `src/lib/api/*.ts` files (excluding `*.test.ts` and `example.functions.ts`).
   - In `get_frontend_paths`, match `apiFetch(?:<[^>]+>)?\(\s*([`"\'])(/[a-zA-Z0-9_/\-.$?={}&()*]+)\1` and variable `const path = ... ? \`/documents/\${documentId}/graph?\${queryString}\` : \`/documents/\${documentId}/graph\`` (extracting template/string literals starting with `/documents/`, `/patients/`, `/chat`, `/access-requests`, `/audit/`, `/search/`, `/medication-safety/`, `/timeline`, `/metrics/`, `/dashboard/`, `/auth/`, `/graph`), while ignoring bare path fragments that are not root endpoints.

- [ ] **Step 4: Run tests and `verify_contracts.py` to verify they pass**

Run:
```powershell
app/backend/.venv/Scripts/python.exe -m pytest app/backend/tests/test_verify_contracts_scanner.py -v
app/backend/.venv/Scripts/python.exe app/backend/scripts/verify_contracts.py
cd app/frontend; bunx vitest run src/lib/api/client-contracts.test.ts --run
```
Expected: All tests PASS and `verify_contracts.py` exits `0` with 35+ frontend API endpoints matched against backend OpenAPI routes.

- [ ] **Step 5: Commit**

```powershell
git add app/backend/scripts/verify_contracts.py app/backend/tests/test_verify_contracts_scanner.py app/frontend/src/lib/api/metrics.ts app/frontend/src/lib/api/auth.ts app/frontend/src/lib/api/chat.ts app/frontend/src/lib/api/client-contracts.test.ts
git commit -m "fix: enforce full frontend api contract verification and fix client endpoints"
```

---

### Task 3: Clinical Safety Hardening in CDSS Worker, Drug Check & Metrics RBAC (`CARD-03`)

**Files:**
- Modify: `app/backend/src/hospital_ai/workers/cdss.py:19-133`
- Modify: `app/backend/src/hospital_ai/services/drug_check.py:185-262`
- Modify: `app/backend/src/hospital_ai/api/routes/metrics_endpoint.py:21-73`
- Modify: `app/backend/tests/test_cdss_agent.py`
- Modify: `app/backend/tests/test_drug_check.py`
- Modify: `app/backend/tests/test_metrics.py`

**Interfaces:**
- Consumes: `ActiveEvidenceScope` from `hospital_ai.services.evidence_scope`, `PATIENT_READ_SCOPES` from `hospital_ai.core.security`, `PermissionGrant` from `hospital_ai.db.models`
- Produces:
  - Generation-scoped, soft-delete-aware, idempotent `run_cdss_analysis(session: AsyncSession, document_id: uuid.UUID) -> None` in `app/backend/src/hospital_ai/workers/cdss.py`
  - Generation- and `user_id`-scoped Step 1 assertion filtering in `DrugCheckService.check_interactions` in `app/backend/src/hospital_ai/services/drug_check.py`
  - Role/patient-scope filtered `get_vector_metrics` in `app/backend/src/hospital_ai/api/routes/metrics_endpoint.py`

- [ ] **Step 1: Write the 3 failing clinical safety tests in `test_cdss_agent.py`, `test_drug_check.py`, and `test_metrics.py`**

1. Append `test_cdss_re_run_is_idempotent_and_preserves_acknowledged_alerts` and `test_cdss_ignores_deleted_and_superseded_chunks` in `app/backend/tests/test_cdss_agent.py`:
```python
@pytest.mark.asyncio
async def test_cdss_re_run_is_idempotent_and_preserves_acknowledged_alerts(db_session, monkeypatch):
    # Setup patient, document with active_index_generation_id=gen_active,
    # one active chunk, one superseded chunk (gen_old), one deleted chunk,
    # one existing unacknowledged ClinicalAlert and one acknowledged ClinicalAlert.
    # Run run_cdss_analysis twice; assert superseded/deleted chunk text is NOT in LLM prompt,
    # acknowledged alert is preserved, and unacknowledged alert is replaced (no duplicate rows).
```
2. Append `test_check_interactions_blocks_superseded_or_unauthorized_relation_evidence` in `app/backend/tests/test_drug_check.py`:
```python
@pytest.mark.asyncio
async def test_check_interactions_blocks_superseded_or_unauthorized_relation_evidence(db_session):
    # Setup active drug entity "warfarin" in active generation doc1,
    # and target entity "aspirin" linked via GraphRelationAssertion whose GraphRelationEvidence
    # points to a superseded generation chunk (or a patient without PermissionGrant for user_id).
    # Assert check_interactions(..., user_id=unauthorized_user.id) returns [] for that assertion.
```
3. Append `test_vector_metrics_scopes_sources_to_authorized_patients` in `app/backend/tests/test_metrics.py`:
```python
@pytest.mark.asyncio
async def test_vector_metrics_scopes_sources_to_authorized_patients(client, db_session):
    # Create two ready documents for two different patients; grant clinician access to patient 1 only.
    # Call GET /api/v1/metrics/vector as clinician -> assert sources only contains patient 1's document_id.
```

- [ ] **Step 2: Run the 3 tests to verify they fail**

Run:
```powershell
app/backend/.venv/Scripts/python.exe -m pytest app/backend/tests/test_cdss_agent.py app/backend/tests/test_drug_check.py app/backend/tests/test_metrics.py -v
```
Expected: FAIL on the 3 new tests.

- [ ] **Step 3: Implement the safety filters in `cdss.py`, `drug_check.py`, and `metrics_endpoint.py`**

1. In `app/backend/src/hospital_ai/workers/cdss.py`:
   - Filter `DocumentChunk` by `DocumentChunk.document_id == document_id`, `DocumentChunk.deleted_at.is_(None)`, and (when `document.active_index_generation_id is not None`) `DocumentChunk.generation_id == document.active_index_generation_id`. If `not chunks`, return early.
   - Filter `GraphEntity` and `GraphRelationAssertion` by `lifecycle_status == "active"`.
   - Before inserting new `ClinicalAlert` rows for `(document.patient_id, document_id)`, delete existing `ClinicalAlert` rows where `patient_id == document.patient_id`, `source_document_id == document_id`, and `is_acknowledged.is_(False)`.
2. In `app/backend/src/hospital_ai/services/drug_check.py` (lines 202–230):
   - Join `Document` on `Document.id == GraphRelationEvidence.document_id` and filter `GraphRelationAssertion.lifecycle_status == "active"`, `Document.deleted_at.is_(None)`, `Document.status.in_(("ready", "ready_with_warnings"))`, and `Document.active_index_generation_id == GraphRelationEvidence.generation_id`.
   - When `user_id is not None`, filter `GraphRelationEvidence.chunk_id.in_(ActiveEvidenceScope(self.session).authorized_chunk_ids(user_id=user_id, patient_id=patient_id))`.
   - Filter `related_entity_ids` using `await self._filter_generation_valid_entities(patient_id, raw_related_entities, user_id=user_id)` and skip any relation whose `other_id` is not in `entity_name_map`.
3. In `app/backend/src/hospital_ai/api/routes/metrics_endpoint.py`:
   - If `current_user.role not in ("admin", "security")`, restrict `Document` queries (`doc_stmt`, `chunk_stmt`, `sources_stmt`) to documents where `Document.patient_id.is_(None)` or `Document.patient_id` has an active `PermissionGrant` for `current_user.id` (using `PermissionService` / `ActiveEvidenceScope` predicate).

- [ ] **Step 4: Run the test suites to verify they pass**

Run:
```powershell
app/backend/.venv/Scripts/python.exe -m pytest app/backend/tests/test_cdss_agent.py app/backend/tests/test_drug_check.py app/backend/tests/test_metrics.py -v
```
Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add app/backend/src/hospital_ai/workers/cdss.py app/backend/src/hospital_ai/services/drug_check.py app/backend/src/hospital_ai/api/routes/metrics_endpoint.py app/backend/tests/test_cdss_agent.py app/backend/tests/test_drug_check.py app/backend/tests/test_metrics.py
git commit -m "fix(security): enforce active generation and scope filters in cdss, drug check, and vector metrics"
```

---

### Task 4: Decompose High-CRAP Backend Hotspots (`CARD-04`)

**Files:**
- Modify: `app/backend/src/hospital_ai/services/upload_sessions.py:161-294`
- Modify: `app/backend/src/hospital_ai/services/claim_validation.py:198-303`
- Modify: `app/backend/src/hospital_ai/api/routes/chat_stream.py:1025-1529`
- Modify: `app/backend/tests/cdi_v2/test_upload_sessions.py`
- Modify: `app/backend/tests/cdi_v2/test_claim_validation.py`
- Modify: `app/backend/tests/test_chat_stream_endpoint.py`

**Interfaces:**
- Consumes: Existing `UploadSessionService`, `ClaimValidator`, and `chat_stream` signatures (no breaking public API changes)
- Produces:
  - Pure helper functions in `upload_sessions.py`: `_extract_and_validate_create_params(...) -> tuple[Optional[uuid.UUID], str, str, str, int, str, str]`, `_assert_object_key_available(storage: Any, object_key: str) -> None`, `_create_presigned_put_or_rollback(session: AsyncSession, storage: Any, object_key: str, mime_type: str) -> tuple[str, dict[str, str]]`
  - Pure helper functions in `claim_validation.py`: `_check_multi_date_clause_alignment(claim: Claim, evidence: str, claim_dates: set[str]) -> Optional[ClaimResult]`, `_check_negation_consistency(claim: Claim, evidence: str) -> Optional[ClaimResult]`
  - Modular helper functions in `chat_stream.py`: `_build_disambiguation_sse_response(...) -> StreamingResponse`, `_check_stream_patient_scope_or_deny(...) -> Optional[StreamingResponse]`, `_check_stream_input_guardrail_or_deny(...) -> Optional[StreamingResponse]`

- [ ] **Step 1: Write unit tests targeting the extracted helper boundaries in `test_upload_sessions.py` and `test_claim_validation.py`**

Append direct unit tests in `app/backend/tests/cdi_v2/test_upload_sessions.py` and `app/backend/tests/cdi_v2/test_claim_validation.py` exercising `_extract_and_validate_create_params`, `_check_multi_date_clause_alignment`, and `_check_negation_consistency`.

- [ ] **Step 2: Run pytest on those test files to verify the new helper tests fail**

Run:
```powershell
app/backend/.venv/Scripts/python.exe -m pytest app/backend/tests/cdi_v2/test_upload_sessions.py app/backend/tests/cdi_v2/test_claim_validation.py -v
```
Expected: FAIL (`ImportError` / `AttributeError` for the not-yet-extracted helpers).

- [ ] **Step 3: Extract the helpers in `upload_sessions.py`, `claim_validation.py`, and `chat_stream.py`**

Refactor `UploadSessionService.create`, `deterministic_entailment`, and `chat_stream` to delegate to the single-responsibility helpers listed in **Interfaces**, keeping each function's McCabe complexity `< 20`.

- [ ] **Step 4: Run pytest with coverage and `calculate_crap_score.py` to verify complexity drop**

Run:
```powershell
app/backend/.venv/Scripts/python.exe -m pytest app/backend/tests/cdi_v2/test_upload_sessions.py app/backend/tests/cdi_v2/test_claim_validation.py app/backend/tests/test_chat_stream_endpoint.py -v
app/backend/.venv/Scripts/python.exe app/backend/scripts/calculate_crap_score.py --top-n 20
```
Expected: All tests PASS; McCabe complexity of `upload_sessions.create`, `deterministic_entailment`, and `chat_stream` drops below `20`.

- [ ] **Step 5: Commit**

```powershell
git add app/backend/src/hospital_ai/services/upload_sessions.py app/backend/src/hospital_ai/services/claim_validation.py app/backend/src/hospital_ai/api/routes/chat_stream.py app/backend/tests/cdi_v2/test_upload_sessions.py app/backend/tests/cdi_v2/test_claim_validation.py
git commit -m "refactor(backend): decompose high-complexity functions in chat_stream, upload_sessions, and claim_validation"
```

---

### Task 5: Wire Frontend Static Mock Routes to Live BFF APIs (`CARD-05`)

**Files:**
- Create: `app/frontend/src/components/hms/SystemHealthCard.test.tsx`
- Modify: `app/frontend/src/components/hms/SystemHealthCard.tsx:1-47`
- Modify: `app/frontend/src/routes/_app.audit.traces.$traceId.tsx:1-25`
- Modify: `app/frontend/src/routes/_app.integrations.traces.$traceId.tsx:1-24`
- Modify: `app/frontend/src/routes/_app.documents.ocr-queue.tsx:1-53`

**Interfaces:**
- Consumes:
  - `getDashboardSummary` (`SystemsHealth`) from `@/lib/api/dashboard`
  - `getQueryTrace` (`RagTraceResponse`) from `@/lib/api/citations`
  - `listDocuments` (`DocumentRead[]`) from `@/lib/api/documents`
- Produces:
  - `SystemHealthCard({ health?: SystemsHealth })` in `app/frontend/src/components/hms/SystemHealthCard.tsx` that fetches `getDashboardSummary()` via `useQuery` (or accepts `health` prop) and maps live `hms_api` and `ollama_inference` statuses alongside fallback metrics.
  - Live query-trace loading with explicit error/empty state in `_app.audit.traces.$traceId.tsx` and `_app.integrations.traces.$traceId.tsx`.
  - Live document queue table backed by `listDocuments()` in `_app.documents.ocr-queue.tsx`.

- [ ] **Step 1: Write failing component test `app/frontend/src/components/hms/SystemHealthCard.test.tsx`**

Create `app/frontend/src/components/hms/SystemHealthCard.test.tsx`:
```tsx
// @vitest-environment jsdom
import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import * as dashboardApi from "@/lib/api/dashboard";
import { SystemHealthCard } from "./SystemHealthCard";

describe("SystemHealthCard", () => {
  it("renders live HMS and LLM health statuses from getDashboardSummary", async () => {
    vi.spyOn(dashboardApi, "getDashboardSummary").mockResolvedValue({
      recent_patients: [],
      document_stats: { indexed: 5, processing: 1, failed: 0 },
      metrics: { hours_saved: 2.5, cost_saved_usd: 150 },
      systems_health: { hms_api: "online", ollama_inference: "degraded" },
    });

    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={qc}>
        <SystemHealthCard />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText(/HMS FHIR bridge/i)).toBeTruthy();
      expect(screen.getByText(/online/i)).toBeTruthy();
      expect(screen.getByText(/degraded/i)).toBeTruthy();
    });
  });
});
```

- [ ] **Step 2: Run Vitest on `SystemHealthCard.test.tsx` to verify it fails**

Run: `cd app/frontend; bunx vitest run src/components/hms/SystemHealthCard.test.tsx --run`
Expected: FAIL (`getDashboardSummary` is not called and static `systemHealth` values are rendered instead).

- [ ] **Step 3: Update `SystemHealthCard.tsx`, `_app.audit.traces.$traceId.tsx`, `_app.integrations.traces.$traceId.tsx`, and `_app.documents.ocr-queue.tsx`**

1. In `SystemHealthCard.tsx`: use `useQuery({ queryKey: ["dashboard", "summary"], queryFn: getDashboardSummary })` to derive live rows for `LLM inference`, `Vector index (pgvector)`, and `HMS FHIR bridge` from `data.systems_health` and `data.document_stats`, falling back gracefully if `data` is loading/unavailable.
2. In `_app.audit.traces.$traceId.tsx` and `_app.integrations.traces.$traceId.tsx`: query `getQueryTrace(traceId)` via `useQuery`, convert `RagTraceResponse` into a `Trace` object for `TraceTimeline`, and render `ErrorState` if `traceId` is not found in both the API and fallback list (Review Focus #5).
3. In `_app.documents.ocr-queue.tsx`: fetch `listDocuments()` via `useQuery({ queryKey: ["documents", "ocr-queue"], queryFn: () => listDocuments() })` and map live documents (`title`, `page_count`, `status`, `created_at`) with fallback to `ocrQueue` only when the response is empty in demo mode.

- [ ] **Step 4: Run Vitest, ESLint, and TypeScript check**

Run:
```powershell
cd app/frontend; bunx vitest run src/components/hms/SystemHealthCard.test.tsx --run; bun run typecheck; bun run lint
```
Expected: PASS with zero errors.

- [ ] **Step 5: Commit**

```powershell
git add app/frontend/src/components/hms/SystemHealthCard.tsx app/frontend/src/components/hms/SystemHealthCard.test.tsx app/frontend/src/routes/_app.audit.traces.`$traceId.tsx app/frontend/src/routes/_app.integrations.traces.`$traceId.tsx app/frontend/src/routes/_app.documents.ocr-queue.tsx
git commit -m "feat(frontend): connect system health, ocr queue, and trace routes to live bff apis"
```

---

### Task 6: Unit Tests for 0%-Covered Document Loaders & LLM/Embedding Providers (`CARD-06`)

**Files:**
- Create: `app/backend/tests/test_loaders_and_providers_unit.py`

**Interfaces:**
- Consumes:
  - `TextLoader` (`hospital_ai.services.loaders.text_loader`)
  - `HtmlLoader` (`hospital_ai.services.loaders.html_loader`)
  - `ExcelLoader` (`hospital_ai.services.loaders.excel_loader`)
  - `OpenAIProvider` (`hospital_ai.services.llm.openai_provider`)
  - `OllamaProvider` (`hospital_ai.services.llm.ollama_provider`)
  - `GeminiProvider` (`hospital_ai.services.llm.gemini_provider`)
  - `OpenAIEmbeddingProvider` (`hospital_ai.services.embedding.openai_provider`)
  - `OllamaEmbeddingProvider` (`hospital_ai.services.embedding.ollama_provider`)
- Produces: Comprehensive unit test suite `app/backend/tests/test_loaders_and_providers_unit.py` covering normal execution and HTTP/file error handling without external network access.

- [ ] **Step 1: Create `app/backend/tests/test_loaders_and_providers_unit.py` testing loaders and provider error/success paths**

Write unit tests in `app/backend/tests/test_loaders_and_providers_unit.py` using `tmp_path` for `TextLoader`, `HtmlLoader`, and `ExcelLoader`, and `monkeypatch` / `httpx.MockTransport` for `OpenAIProvider`, `OllamaProvider`, `GeminiProvider`, `OpenAIEmbeddingProvider`, and `OllamaEmbeddingProvider` (testing 200 OK responses, streaming chunks, and 429/500 error handling).

- [ ] **Step 2: Run pytest with coverage on those modules**

Run:
```powershell
app/backend/.venv/Scripts/python.exe -m pytest app/backend/tests/test_loaders_and_providers_unit.py --cov=hospital_ai.services.loaders --cov=hospital_ai.services.llm --cov=hospital_ai.services.embedding -v
```
Expected: PASS with coverage on loaders, LLM providers, and embedding providers jumping from `0%` to `> 75%`.

- [ ] **Step 3: Commit**

```powershell
git add app/backend/tests/test_loaders_and_providers_unit.py
git commit -m "test(backend): add unit coverage for document loaders and llm/embedding providers"
```

---

### Task 7: Complete SA/BA vNext Specifications & Before/After Audit Matrix in `report.md` (`CARD-07`)

**Files:**
- Modify: `report.md`

**Interfaces:**
- Consumes: Output of `calculate_crap_score.py`, `verify_contracts.py`, `verify_deterministic_gates.py --mode smoke`, `pytest`, and `vitest`
- Produces: Updated `report.md` with:
  1. Live Kanban status (`Merged / Verified`) for `CARD-01` through `CARD-06`
  2. Before vs. After Quality & Testing Metrics Table
  3. Detailed BA User Stories & Gherkin Acceptance Criteria (`Given / When / Then`) for all 4 vNext Clinical Flows
  4. Detailed SA Sequence & Component Blueprints + Database DDL proposals for all 4 vNext Architectural Upgrades

- [ ] **Step 1: Run full backend and frontend quality gates to collect exact post-remediation metrics**

Run:
```powershell
cd app/backend; .venv/Scripts/python.exe -m ruff check src/ tests/; .venv/Scripts/python.exe -m ruff format --check src/ tests/; .venv/Scripts/python.exe scripts/verify_contracts.py; .venv/Scripts/python.exe scripts/calculate_crap_score.py --top-n 15
cd app/frontend; bun run lint; bun run typecheck; bun run test -- --run; bun run build
```
Expected: All commands exit `0`.

- [ ] **Step 2: Update `report.md` with Before/After Metrics, Gherkin BA User Stories, and SA Sequence Diagrams**

Append Section 5 (`Before vs. After Verification Evidence`) and expand Section 4 (`Detailed BA Gherkin Stories & SA Sequence Diagrams / DDL Specs`) in `report.md`.

- [ ] **Step 3: Commit final report**

```powershell
git add report.md docs/superpowers/plans/2026-11-10-repo-clean-and-vnext-hardening.md
git commit -m "docs(report): record before-after verification metrics and full sa/ba vnext specifications"
```
