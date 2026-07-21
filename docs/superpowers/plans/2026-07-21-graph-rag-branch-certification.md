# Graph RAG Branch Certification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the known authorization and evidence-integrity blockers on the dynamic-patient/Graph-RAG branch and produce a reviewable, locally certified pull request.

**Architecture:** Keep the existing FastAPI, SQLAlchemy, TanStack Start, and retrieval interfaces. Harden behavior at four existing seams: the patient-registration route, `RetrievalService`, the patient graph response builder, and the centralized frontend API client. Public/global knowledge remains fail-closed and runtime-excluded; introducing a provenance/licensing data model is explicitly deferred to the separate corpus-governance project.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy async, pytest, TypeScript, React 19, TanStack Start, Vitest, Bun.

## Global Constraints

- Use synthetic or de-identified data only; never add real PHI, secrets, credentials, or raw patient identifiers to audit metadata.
- Permission filtering must occur before any retrieved text reaches an LLM.
- A patient evidence result must prove the same patient and active lifecycle across `DocumentChunk`, `Document`, and `DocumentPage`, including `DocumentPage.document_id == DocumentChunk.document_id`.
- Global/public knowledge is runtime-excluded until a separate provenance, license, review, workspace, and access-tag design is approved.
- `/chat` and `/chat/stream` must retain citation validation, cited-only evidence, sanitized errors, retrieval audit, trace persistence, threshold behavior, and graph `top_k` parity.
- Follow strict TDD: add one behavior test, run it and observe the expected failure, implement the minimum production change, then rerun the focused test and affected suite.
- Preserve the original checkout's dirty worktree. Modify and commit only files inside `D:\projects\chatbot-hospital-system-graph-rag-cert`.
- Do not refactor `seed_dev.py`, `GraphCanvas.tsx`, database migrations, or the corpus importer in this certification slice.

---

## File Responsibility Map

- `app/backend/src/hospital_ai/api/routes/patients.py`: validate patient-registration input, authorize the records workflow, grant least-privilege creator scopes, and emit non-PHI audit metadata.
- `app/backend/tests/test_patients.py`: patient-create role matrix, least-privilege, input validation, and audit regression tests.
- `app/frontend/src/lib/rbac.ts`: expose the one frontend capability used to show patient registration.
- `app/frontend/src/lib/rbac.test.ts`: capability matrix for patient registration.
- `app/frontend/src/routes/_app.patients.index.tsx`: hide the registration control from roles that cannot call the backend route.
- `app/backend/src/hospital_ai/services/retrieval.py`: fail closed for global knowledge and enforce an exact patient/document/page/chunk join chain in vector, BM25, portable, and graph-evidence paths.
- `app/backend/tests/test_retrieval_sql.py`: executable SQL-shape and live SQLite adversarial retrieval contracts.
- `app/backend/tests/test_graph_rag_chat_release_gates.py`: transport-facing leakage and parity regression gates.
- `app/backend/src/hospital_ai/api/routes/graph.py`: return only source-supported edges and preserve distinct lab facts without substring canonicalization collisions.
- `app/backend/tests/test_graph_endpoint.py`: patient graph response behavior at the route seam.
- `app/frontend/src/lib/api-client.ts`: translate demo identifiers only in schema-known identifier fields, never arbitrary clinical strings.
- `app/frontend/src/lib/api-client.test.ts`: response and request mapping regressions.

### Task 1: Lock Patient Registration to the Records Workflow

**Files:**
- Modify: `app/backend/src/hospital_ai/api/routes/patients.py:68-115`
- Modify: `app/backend/tests/test_patients.py`
- Modify: `app/frontend/src/lib/rbac.ts`
- Modify: `app/frontend/src/lib/rbac.test.ts`
- Modify: `app/frontend/src/routes/_app.patients.index.tsx`

**Interfaces:**
- Consumes: `get_current_user() -> User`, `AuditService.record(...)`, `PermissionDeniedError`, and `PatientPermission`.
- Produces: `canCreatePatient(role: Role): boolean`; `create_patient(...)` accepts only backend roles `records_staff` and `admin`; patient creation grants no implicit PHI permission to the creator.

- [ ] **Step 1: Add failing backend role-matrix and least-privilege tests**

Add test helpers that call `create_patient()` directly with a synthetic `PatientCreate`, then add:

```python
@pytest.mark.asyncio
@pytest.mark.parametrize("role", ["doctor", "nurse", "pharmacist", "lab_staff", "security", "admin"])
async def test_create_patient_denies_non_records_roles(session_and_settings, role):
    user = User(email=f"{role}@test.local", full_name=role, role=role)
    session.add(user)
    await session.commit()
    with pytest.raises(PermissionDeniedError):
        await create_patient(PatientCreate(mrn="MRN-90001", full_name="Synthetic Person"), _post_request(), session, user)

@pytest.mark.asyncio
async def test_create_patient_grants_no_implicit_patient_permissions(session_and_settings):
    # create records_staff user, call route, query PatientPermission
    assert permissions == []
```

- [ ] **Step 2: Run the new backend tests and verify RED**

Run: `py -3.12 -m pytest tests/test_patients.py -k "create_patient" -q`

Expected: non-records roles do not raise and/or the creator receives `admin`, proving the regression tests catch the current vulnerability.

- [ ] **Step 3: Add bounded input and non-PHI audit tests**

Add tests that assert `PatientCreate` rejects blank names, malformed MRNs, and unsupported status values, and assert the successful `patient.create` audit row does not contain `mrn` or `full_name`.

Use these exact validation rules:

```python
class PatientCreate(BaseModel):
    mrn: str = Field(min_length=5, max_length=64, pattern=r"^[A-Z0-9-]+$")
    full_name: str = Field(min_length=1, max_length=255)
    dob: Optional[date] = None
    department: Optional[str] = Field(default=None, max_length=128)
    status: Literal["active", "stable", "watch", "critical"] = "active"
```

- [ ] **Step 4: Implement the minimal backend authorization and least-privilege behavior**

At the start of `create_patient()`, reject roles outside `{"records_staff", "admin"}` with `PermissionDeniedError("Only records staff or admins can register patients.")`. Strip `full_name` before constructing `Patient`, remove the implicit `PatientPermission` loop entirely, and record metadata containing only `{"department": payload.department, "status": payload.status}`. Access must subsequently flow through the existing access-request approval workflow.

- [ ] **Step 5: Run focused and adjacent backend tests GREEN**

Run:

```powershell
py -3.12 -m pytest tests/test_patients.py tests/test_patient_bff.py tests/test_permissions.py -q
py -3.12 -m ruff check src/hospital_ai/api/routes/patients.py tests/test_patients.py
py -3.12 -m ruff format --check src/hospital_ai/api/routes/patients.py tests/test_patients.py
```

Expected: all selected tests pass and Ruff reports no errors.

- [ ] **Step 6: Add the frontend capability test and verify RED**

Add to `rbac.test.ts`:

```typescript
it("allows only front desk to register patients", () => {
  expect(canCreatePatient("front_desk")).toBe(true);
  for (const role of ROLES.map((entry) => entry.id).filter((role) => role !== "front_desk")) {
    expect(canCreatePatient(role)).toBe(false);
  }
});
```

Run: `bun run test -- src/lib/rbac.test.ts --run`

Expected: FAIL because `canCreatePatient` does not exist.

- [ ] **Step 7: Implement frontend capability gating**

Add `export function canCreatePatient(role: Role): boolean { return role === "front_desk"; }`, obtain the current session role in `_app.patients.index.tsx`, and render `AddPatientDialog` only when the capability returns true.

- [ ] **Step 8: Run frontend focused gates GREEN**

Run:

```powershell
bun run test -- src/lib/rbac.test.ts --run
bun run typecheck
bun run lint
```

Expected: test and typecheck pass; lint has no new errors or warnings.

- [ ] **Step 9: Commit Task 1**

```powershell
git add app/backend/src/hospital_ai/api/routes/patients.py app/backend/tests/test_patients.py app/frontend/src/lib/rbac.ts app/frontend/src/lib/rbac.test.ts app/frontend/src/routes/_app.patients.index.tsx
git commit -m "fix: restrict patient registration privileges"
```

### Task 2: Quarantine Global Knowledge and Enforce the Full Evidence Join Chain

**Files:**
- Modify: `app/backend/src/hospital_ai/services/retrieval.py:19-620`
- Modify: `app/backend/tests/test_retrieval_sql.py`
- Modify: `app/backend/tests/test_graph_rag_chat_release_gates.py`

**Interfaces:**
- Consumes: `RetrievalService.search`, `hybrid_search`, `_bm25_search_*`, `_search_*`, and `get_chunks_by_ids`.
- Produces: every method returns `[]` when `patient_id is None`; patient-linked methods return only rows where chunk and document both equal `patient_id`, the page belongs to the same document, all three rows are active, and an active accepted patient permission exists.

- [ ] **Step 1: Add failing global-quarantine tests**

Replace the existing global-success expectation with:

```python
@pytest.mark.asyncio
async def test_global_knowledge_is_runtime_quarantined(session_and_settings):
    session, _ = session_and_settings
    await create_indexed_document(session, patient_id=None, uploaded_by=DOCTOR_ID,
        title="Unreviewed Guideline", content="Unreviewed public guidance.")
    service = RetrievalService(session)
    assert await service.search(user_id=DOCTOR_ID, patient_id=None,
        query_embedding=deterministic_embedding("guidance"), top_k=5) == []
    assert await service.hybrid_search(user_id=DOCTOR_ID, patient_id=None,
        query_embedding=deterministic_embedding("guidance"), query_text="guidance", top_k=5) == []
```

Also add a patient-linked test proving a `patient_id=None` document/chunk is not mixed into patient evidence.

- [ ] **Step 2: Run quarantine tests and verify RED**

Run: `py -3.12 -m pytest tests/test_retrieval_sql.py -k "global_knowledge or patient_linked_excludes_global" -q`

Expected: current retrieval returns the global guideline.

- [ ] **Step 3: Add failing graph-evidence mismatch tests**

In `test_graph_rag_chat_release_gates.py`, create adversarial fixtures where:

1. an Alice chunk points to a Bob document;
2. an Alice chunk points to a page belonging to another document;
3. the requested chunk or its document/page is soft-deleted;
4. the caller permission is revoked or expired.

For every case call `get_chunks_by_ids(...)` and assert `evidence == []`.

- [ ] **Step 4: Run graph-evidence tests and verify RED**

Run: `py -3.12 -m pytest tests/test_graph_rag_chat_release_gates.py -k "graph_evidence" -q`

Expected: at least the mismatched document-patient case returns evidence under current code.

- [ ] **Step 5: Implement fail-closed retrieval**

Make `search()` and `hybrid_search()` return `[]` immediately when `patient_id is None`. Remove `OR ... IS NULL` global mixing from patient-linked vector SQL, PostgreSQL BM25, portable BM25/vector statements, and `get_chunks_by_ids`. In every ORM path use the exact join:

```python
.join(Document, Document.id == DocumentChunk.document_id)
.join(DocumentPage, and_(
    DocumentPage.id == DocumentChunk.page_id,
    DocumentPage.document_id == DocumentChunk.document_id,
))
.where(
    DocumentChunk.patient_id == patient_id,
    Document.patient_id == patient_id,
    Document.status == "indexed",
    DocumentChunk.deleted_at.is_(None),
    Document.deleted_at.is_(None),
    DocumentPage.deleted_at.is_(None),
)
```

Keep `GLOBAL_RETRIEVAL_SQL` exported only if an existing contract imports it; otherwise remove it and update imports. Do not add a bypass flag.

- [ ] **Step 6: Strengthen executable SQL-shape assertions**

Assert the patient SQL contains exact document and chunk patient predicates plus the page-document join, and does not contain patient-null fallback predicates. These assertions supplement—not replace—the live SQLite adversarial tests.

- [ ] **Step 7: Run retrieval and transport parity gates GREEN**

Run:

```powershell
py -3.12 -m pytest tests/test_retrieval_sql.py tests/test_graph_rag_chat_release_gates.py tests/test_chat_endpoint.py tests/test_chat_stream_endpoint.py -q
py -3.12 -m ruff check src/hospital_ai/services/retrieval.py tests/test_retrieval_sql.py tests/test_graph_rag_chat_release_gates.py
py -3.12 -m ruff format --check src/hospital_ai/services/retrieval.py tests/test_retrieval_sql.py tests/test_graph_rag_chat_release_gates.py
```

Expected: all selected tests pass, including existing stream/non-stream citation and graph `top_k` gates.

- [ ] **Step 8: Commit Task 2**

```powershell
git add app/backend/src/hospital_ai/services/retrieval.py app/backend/tests/test_retrieval_sql.py app/backend/tests/test_graph_rag_chat_release_gates.py
git commit -m "fix: fail closed on ungoverned retrieval"
```

### Task 3: Restore Streaming and Non-Streaming Safety Parity

**Files:**
- Modify: `app/backend/src/hospital_ai/api/routes/chat_stream.py:75-747`
- Modify: `app/backend/tests/test_chat_stream_endpoint.py`
- Modify: `app/backend/tests/test_audit_2026_05.py`
- Modify: `app/backend/tests/test_graph_rag_chat_release_gates.py`

**Interfaces:**
- Consumes: `get_input_guardrail()`, `get_output_guardrail()`, `SAFE_PHI_LEAK_BLOCKED_ANSWER`, `_generate_sse_events()`, and `_apply_stream_completion()`.
- Produces: streaming runs the same input/output guardrails as `ChatService.answer`, persists only `completion.cited_evidence`, and leaves every terminal query in `completed`, `refused`, or `failed`—never `streaming`.

- [ ] **Step 1: Add failing input-guardrail and no-downstream-work tests**

Patch the existing guardrail getter to return a deterministic blocked result, call `chat_stream()`, and assert that retrieval and `LLMManager.get()` are never invoked. Assert the client receives only the established safe refusal event/text and the audit metadata reason is `input_guardrail_blocked`.

- [ ] **Step 2: Run the input-guardrail test and verify RED**

Run: `py -3.12 -m pytest tests/test_chat_stream_endpoint.py -k "input_guardrail" -q`

Expected: streaming currently proceeds to retrieval/LLM because it does not invoke the guardrail.

- [ ] **Step 3: Add failing output-guardrail and cited-only persistence tests**

Add tests that buffer an unsafe generated answer and assert no unsafe token is emitted, the safe PHI-blocked answer is emitted, and the query/audit terminal state is recorded. Add a direct `_apply_stream_completion()` test whose `evidence` contains `E1` and `E2` but `cited_evidence` contains only `E1`; assert the database stores only `E1`.

- [ ] **Step 4: Add a failing internal-error terminal-state test**

Make the streaming LLM raise `RuntimeError("secret provider detail")`. Assert the client error event is sanitized, the provider detail is absent, the `AiQuery.status` is `failed`, and a failure audit row exists.

- [ ] **Step 5: Implement minimal safety parity**

Import and invoke the same guardrail getters/constants used by `ChatService`. Run the input guardrail before embedding/retrieval. Because `_generate_sse_events()` already buffers generated text for validation, run the output guardrail before emitting generated tokens; on block, emit only the safe answer. Change `_apply_stream_completion()` to iterate `completion.cited_evidence`. Centralize terminal query/audit finalization in an internal helper used by success, refusal, guardrail denial, invalid citation, and unexpected-error paths without changing the public SSE event schema.

- [ ] **Step 6: Run chat transport gates GREEN**

Run:

```powershell
py -3.12 -m pytest tests/test_chat_endpoint.py tests/test_chat_stream_endpoint.py tests/test_chat_citations.py tests/test_audit_2026_05.py tests/test_graph_rag_chat_release_gates.py -q
py -3.12 -m ruff check src/hospital_ai/api/routes/chat_stream.py tests/test_chat_stream_endpoint.py tests/test_audit_2026_05.py tests/test_graph_rag_chat_release_gates.py
py -3.12 -m ruff format --check src/hospital_ai/api/routes/chat_stream.py tests/test_chat_stream_endpoint.py tests/test_audit_2026_05.py tests/test_graph_rag_chat_release_gates.py
```

Expected: all transport, citation, audit, and graph parity tests pass.

- [ ] **Step 7: Commit Task 3**

```powershell
git add app/backend/src/hospital_ai/api/routes/chat_stream.py app/backend/tests/test_chat_stream_endpoint.py app/backend/tests/test_audit_2026_05.py app/backend/tests/test_graph_rag_chat_release_gates.py
git commit -m "fix: align streaming RAG safety contracts"
```

### Task 4: Make Patient Graph Responses Source-Supported

**Files:**
- Modify: `app/backend/src/hospital_ai/api/routes/graph.py:25-330`
- Modify: `app/backend/src/hospital_ai/schemas/graph.py`
- Modify: `app/frontend/src/lib/api/graph.ts`
- Create: `app/backend/tests/test_graph_endpoint.py`

**Interfaces:**
- Consumes: `GraphEntity`, `GraphRelation`, `GraphDataResponse`, and `PermissionService.require_read`.
- Produces: `_canonical_entity_info(name, entity_type)` performs exact alias/token normalization; `get_patient_graph()` emits only persisted `GraphRelation` edges, preserves distinct lab observations, and exposes source document/chunk identifiers on returned clinical nodes and edges.

- [ ] **Step 1: Add failing canonicalization tests**

Create `test_graph_endpoint.py` with direct tests:

```python
def test_canonicalization_does_not_match_ast_or_alt_substrings():
    assert _canonical_entity_info("fasting glucose", "lab")[0] != "AST"
    assert _canonical_entity_info("salt intake", "concept")[0] != "ALT"

def test_distinct_lab_values_have_distinct_consolidation_keys():
    first = _canonical_entity_info("Potassium 3.1", "lab")
    second = _canonical_entity_info("Potassium 4.4", "lab")
    assert first[2] != second[2]
```

- [ ] **Step 2: Add a failing route-level unsupported-edge test**

Seed a patient document and two `GraphEntity` rows but no `GraphRelation`, call `get_patient_graph()`, and assert `response.edges == []`. Add a second route test with one persisted relation and assert exactly that relation plus its real `source_document_id` and `source_chunk_id` are returned.

- [ ] **Step 3: Run graph endpoint tests and verify RED**

Run: `py -3.12 -m pytest tests/test_graph_endpoint.py -q`

Expected: the substring cases canonicalize incorrectly and the route fabricates patient-to-entity edges.

- [ ] **Step 4: Implement exact normalization and stable consolidation**

Replace substring checks for short lab tokens with word-boundary matching. Consolidate non-lab aliases by `(canonical_name, canonical_type)` and lab observations by `(canonical_name, canonical_type, sublabel)`. When a key is first seen, use `node-{ent.id}` as its stable node ID; map later aliases to the existing node ID.

Extend `GraphNode`, `GraphEdge`, and `GraphPathStep` with typed optional `source_document_id` and `source_chunk_id` fields and mirror them in `app/frontend/src/lib/api/graph.ts`. Populate them from persisted `GraphEntity`/`GraphRelation` rows; do not use generic strings such as `"Indexed document chunk"` as provenance.

- [ ] **Step 5: Remove fabricated patient edges**

Delete the loop that automatically emits `diagnosed_with`, `prescribed`, `has_lab`, `attended`, `allergic_to`, and `has`. Keep the patient root node for orientation, but emit edges only from persisted `GraphRelation` rows whose source and target both map to visible nodes.

- [ ] **Step 6: Run graph and release suites GREEN**

Run:

```powershell
py -3.12 -m pytest tests/test_graph_endpoint.py tests/test_graph_rag_integration.py tests/test_graph_rag_chat_release_gates.py -q
py -3.12 -m ruff check src/hospital_ai/api/routes/graph.py tests/test_graph_endpoint.py
py -3.12 -m ruff format --check src/hospital_ai/api/routes/graph.py tests/test_graph_endpoint.py
```

Expected: all selected tests pass and no unsupported semantic edge is returned.

- [ ] **Step 7: Commit Task 3**

```powershell
git add app/backend/src/hospital_ai/api/routes/graph.py app/backend/src/hospital_ai/schemas/graph.py app/backend/tests/test_graph_endpoint.py app/frontend/src/lib/api/graph.ts
git commit -m "fix: preserve graph evidence provenance"
```

### Task 5: Restrict Demo-ID Translation to Identifier Fields

**Files:**
- Modify: `app/frontend/src/lib/api-client.ts:35-130`
- Modify: `app/frontend/src/lib/api-client.test.ts`

**Interfaces:**
- Consumes: `apiFetch<T>()` and existing demo UUID mappings.
- Produces: `mapApiIds(value, key?)` maps only `id`, keys ending in `_id`, and graph endpoint keys `from_node`/`to_node`; arbitrary strings such as `content`, `answer`, `title`, `label`, and citation text remain byte-for-byte unchanged.

- [ ] **Step 1: Add failing response-mapping tests**

Add tests that mock this response:

```typescript
{
  patient_id: "20000000-0000-0000-0000-000000000001",
  content: "Reference 20000000-0000-0000-0000-000000000001 exactly",
  nested: { document_id: "90000000-0000-0000-0000-000000000002", title: "Case 90000000-0000-0000-0000-000000000002" }
}
```

Assert `patient_id === "p-001"`, `nested.document_id === "ar-002"`, and both prose fields remain unchanged.

- [ ] **Step 2: Run the frontend test and verify RED**

Run: `bun run test -- src/lib/api-client.test.ts --run`

Expected: current recursive string mapping changes both prose fields.

- [ ] **Step 3: Implement key-aware response mapping**

Replace `mapIds` with a pure recursive function carrying the property key:

```typescript
const ID_KEYS = new Set(["id", "from_node", "to_node"]);
function isIdentifierKey(key: string | undefined): boolean {
  return key !== undefined && (ID_KEYS.has(key) || key.endsWith("_id"));
}
```

Map a string only when `isIdentifierKey(key)` is true; recurse through objects with each property key and through arrays while retaining the parent key. Keep path mapping unchanged. Do not add heuristic UUID scanning.

- [ ] **Step 4: Add request-body non-corruption test**

Post JSON containing `{ patient_id: "p-001", question: "Compare p-001 with the literal text ar-002" }`. Assert the identifier field is mapped but the question is unchanged. Parse JSON request bodies, recursively map identifier fields, then `JSON.stringify` the mapped object; if parsing fails, leave the original body unchanged.

- [ ] **Step 5: Run frontend gates GREEN**

Run:

```powershell
bun run test -- src/lib/api-client.test.ts --run
bun run typecheck
bun run lint
```

Expected: tests and typecheck pass; no new lint warnings.

- [ ] **Step 6: Commit Task 4**

```powershell
git add app/frontend/src/lib/api-client.ts app/frontend/src/lib/api-client.test.ts
git commit -m "fix: scope demo identifier translation"
```

### Task 6: Certify, Review, Push, and Open the Pull Request

**Files:**
- Modify only if required by verification: files already owned by Tasks 1-4.
- Do not stage ignored dependencies, test artifacts, screenshots, Khuym state, or files from the original checkout.

**Interfaces:**
- Consumes: all Task 1-5 commits.
- Produces: green local gates, clean task reviews, clean final whole-branch review, pushed `codex/graph-rag-certification`, and one PR targeting `main`.

- [ ] **Step 1: Run backend certification gates**

```powershell
py -3.12 -m pytest tests -q
py -3.12 -m ruff check src tests
py -3.12 -m ruff format --check src tests
py -3.12 scripts/verify_contracts.py
```

Expected: 0 failures, Ruff clean, contracts pass with only the already documented `/api` gap.

- [ ] **Step 2: Run frontend certification gates**

```powershell
bun run typecheck
bun run lint
bun run test -- --run
VITE_API_URL=http://localhost:8000/api/v1 bun run build
```

Expected: typecheck/build/unit tests pass and lint introduces no errors or new warnings.

- [ ] **Step 3: Run targeted browser and live-service gates when infrastructure is available**

Run the existing critical chat/graph/patient Playwright specifications against port `8082` and backend port `8000`. If Docker/PostgreSQL or browser infrastructure is unavailable, report the exact blocker and do not describe the PR as release-certified; local unit/integration green remains development evidence only.

- [ ] **Step 4: Run GitNexus changed-scope analysis**

Run `detect_changes({scope: "compare", base_ref: "main", worktree: "D:\\projects\\chatbot-hospital-system-graph-rag-cert"})`. Review every affected process and resolve all unexpected HIGH/CRITICAL effects before committing any verification fix.

- [ ] **Step 5: Run task reviews and final whole-branch review**

For each task, provide the task brief, implementer report, and `review-package` diff to a fresh reviewer. Require both spec compliance and code-quality approval. After all tasks pass, generate a review package from `git merge-base main HEAD` to `HEAD` and dispatch one final high-capability reviewer. Fix every Critical/Important finding and re-review.

- [ ] **Step 6: Confirm branch hygiene**

Run:

```powershell
git status --short
git diff --check main...HEAD
git log --oneline main..HEAD
```

Expected: no uncommitted files, no whitespace errors, and only intentional certification commits on top of the inherited feature branch commits.

- [ ] **Step 7: Push and create the PR**

```powershell
git push -u origin codex/graph-rag-certification
gh pr create --base main --head codex/graph-rag-certification --title "fix: certify Graph RAG branch safety" --body-file <generated-pr-body.md>
```

The PR body must separate local verification from GitHub CI, enumerate PHI/permission impacts, describe global-KB quarantine, list skipped live gates explicitly, and link the relevant test files.

- [ ] **Step 8: Inspect PR checks**

Run `gh pr checks <number> --watch`. Do not merge. Report failed, skipped, pending, and successful checks separately; a created PR is not equivalent to a certified release.
