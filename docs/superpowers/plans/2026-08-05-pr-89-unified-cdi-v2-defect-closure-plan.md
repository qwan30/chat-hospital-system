# PR #89 Unified CDI V2 Defect Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` or `superpowers:executing-plans` to implement this plan task-by-task. Use `superpowers:test-driven-development` for each defect, `superpowers:systematic-debugging` for every unexpected failure, and `superpowers:verification-before-completion` before any completion claim. Do not mark a task complete from file presence or mocked evidence.

**Goal:** Convert PR #89 from a scaffolded, failing CDI V2 branch into one evidence-backed candidate that satisfies the 19-task normative implementation plan, has zero migration-model drift, enforces patient/capability boundaries on every PHI path, preserves active serving generations on failure, and passes real backend and browser acceptance gates on one unchanged SHA.

**Architecture:** Keep immutable upload, extraction, revision, generation, graph, timeline, and validated-stream records as separate authority layers. A verified/finalized immutable source may create machine revisions; human draft edits create new immutable revisions; submit freezes a content-hashed revision set; approval authorizes a build but does not publish authority; a complete generation is atomically activated with compare-and-swap and supersedes the old generation only after all required projections pass. All lexical, vector, graph, timeline, citation, and chat reads consume one shared patient-authorized active-generation scope. Release gates consume persisted test artifacts, never hard-coded booleans.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2 async, Alembic, PostgreSQL 16 + pgvector, Redis/RQ, Cloudflare R2/boto3, OCR workers, React 19, TanStack Start/Query/Router, TypeScript 5.8, Bun, Vitest, Playwright, GitHub Actions.

## Global constraints

- Work from PR head `29e5b8351f6be40fbe235ff7728b1dcffef287a1` or record the replacement SHA before starting.
- Preserve V1 roles, accepted formats, observability, and deployment behavior unless V2 explicitly replaces them.
- Do not introduce `tenant_id` or a new clinical-reviewer role.
- Never send real PHI to external providers or print PHI-bearing entities/content.
- Do not delete or redefine `DocumentPage` serving semantics before backfill and parity gates pass.
- All write APIs require `Idempotency-Key`; draft save and submit additionally require strong `If-Match`.
- A request payload must never enable synthetic/demo self-approval.
- Do not make a release gate pass by weakening, skipping, defaulting, or fabricating evidence.
- Every task follows RED → GREEN → REFACTOR and ends with a focused commit.
- Before each commit: run the focused tests, `git diff --check`, and the relevant lint/type check.
- Before final review: run the complete verification matrix on the exact head SHA.

## Evidence baseline and non-goals

### Existing failures to preserve as regression evidence

- CI run `31014463001` is red.
- backend job `92334831156` fails at Ruff and skips pytest/contracts/acceptance.
- migration job `92334831412` fails `alembic check`.
- frontend job `92334831160` fails the CDI V2 Playwright journey.
- normative harness always reports `Not implemented`.
- release verifier fabricates all gates as passing.

### Non-goals

- No unrelated UI redesign.
- No migration deletion to make `alembic check` superficially pass.
- No broad `# noqa`, `type: ignore`, `|| true`, skipped test, or advisory-gate workaround.
- No production fallback that treats unreadable data, unknown MIME, unavailable malware scanner, or graph extraction errors as success.

---

## Task 1: Freeze the failing baseline and make CI diagnostics deterministic

**Plan coverage:** prerequisite for original Tasks 1–19.

**Files:**
- Modify: `.github/workflows/ci.yml`
- Modify: `app/backend/pyproject.toml` only if current Ruff configuration is inconsistent with repository policy.
- Create: `docs/09-testing/pr-89-defect-baseline.md`

**Interfaces:**
- Consumes: GitHub Actions run/job metadata and exact head SHA.
- Produces: a reproducible command matrix and artifact paths for lint, migration, backend tests, frontend tests, E2E, and release evidence.

- [ ] **Step 1: Record the reviewed SHA and exact failing commands**

Document:

```text
head_sha=29e5b8351f6be40fbe235ff7728b1dcffef287a1
backend: python -m ruff check .
migration: alembic upgrade head && alembic check
frontend: bun run lint && bun run typecheck && bun run test && bun run build
e2e: bun run test:e2e -- cdi-v2-document-intelligence.spec.ts
```

- [ ] **Step 2: Reproduce each failure locally or in the same CI container**

Run from `app/backend`:

```bash
python -m ruff check .
python -m ruff format --check .
```

Run with the CI PostgreSQL URL:

```bash
alembic upgrade head
alembic check
```

Run from `app/frontend`:

```bash
bun run lint
bun run typecheck
bun run test
bun run build
bun run test:e2e -- cdi-v2-document-intelligence.spec.ts
```

Expected: preserve the known failures before changing production behavior.

- [ ] **Step 3: Ensure CI uploads full diagnostics even after an early failure**

Keep gates blocking, but add `if: always()` artifact uploads for:

- Ruff output;
- pytest JUnit/XML;
- Alembic check output;
- Playwright report;
- CDI V2 release evidence directory.

Do not use `continue-on-error` on a required gate.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/ci.yml docs/09-testing/pr-89-defect-baseline.md
git commit -m "test: preserve PR 89 defect baseline"
```

---

## Task 2: Clear Ruff without hiding defects

**Plan coverage:** unblocks verification for all original tasks.

**Files:**
- Modify every PR-added backend file reported by Ruff, especially:
  - `app/backend/src/hospital_ai/services/capabilities.py`
  - `app/backend/src/hospital_ai/services/idempotency.py`
  - `app/backend/src/hospital_ai/services/clinical_timeline.py`
  - `app/backend/src/hospital_ai/api/routes/document_generations.py`
  - `app/backend/src/hospital_ai/api/routes/document_graph.py`
  - `app/backend/src/hospital_ai/evaluation/*.py`
  - `app/backend/scripts/verify_cdi_v2_release.py`

- [ ] **Step 1: Add a CI regression test for zero Ruff findings**

No blanket exclusions. Save the command output as an artifact.

- [ ] **Step 2: Fix imports, types, exception chaining, unused values, and import order**

Examples:

```python
from typing import Any, Optional
```

Use:

```python
raise DomainError("...") from exc
```

Move late imports unless they are proven cycle breakers; where a cycle exists, refactor the dependency boundary instead of suppressing E402 globally.

- [ ] **Step 3: Run**

```bash
cd app/backend
python -m ruff check .
python -m ruff format --check .
```

Expected: exit 0, zero findings.

- [ ] **Step 4: Commit**

```bash
git add app/backend
git commit -m "chore: make CDI v2 backend lint clean"
```

---

## Task 3: Reconcile ORM metadata and migrations with zero destructive drift

**Plan coverage:** original Tasks 1, 2, 10, and 13.

**Files:**
- Modify: `app/backend/src/hospital_ai/db/models.py`
- Modify: `app/backend/src/hospital_ai/db/clinical_documents.py`
- Modify: `app/backend/src/hospital_ai/db/clinical_graph.py`
- Modify:
  - `app/backend/alembic/versions/cdi_v2_0001_add_revision_generation_schema.py`
  - `app/backend/alembic/versions/cdi_v2_0002_add_graph_provenance_schema.py`
  - `app/backend/alembic/versions/cdi_v2_0003_add_validated_stream_state.py`
- Modify/Create tests:
  - `app/backend/tests/cdi_v2/test_model_contracts.py`
  - `app/backend/tests/cdi_v2/test_revision_generation_migration.py`
  - `app/backend/tests/cdi_v2/test_graph_migration.py`
  - `app/backend/tests/cdi_v2/test_validated_stream_migration.py`
  - `app/backend/tests/test_migrations.py`

**Interfaces:**
- ORM metadata must exactly describe the upgraded schema.
- Upgrade on populated legacy fixtures must preserve all V1 rows, indexes, and search-vector behavior.
- Downgrade tests may be limited to reversible test fixtures but must not silently discard production data.

- [ ] **Step 1: Write failing metadata tests**

Assert:

- `DocumentUpload.quarantine_result` is mapped.
- `AiQuery.validation_mode` and `AiQuery.last_emitted_sequence` are mapped.
- graph composite FKs/unique constraints/indexes match migrations.
- `DocumentChunk` uniqueness includes generation without dropping required search-vector/HNSW definitions.
- all state fields have consistent Python constants, ORM defaults, and database checks.

- [ ] **Step 2: Write a populated-database migration test**

Seed pre-V2:

- documents;
- pages/chunks;
- vector/search indexes;
- legacy graph rows;
- AI query rows.

Run upgrade, then assert no row/index loss and safe defaults/backfills.

For `retention_state`, use an expand/backfill/constrain sequence:

1. add nullable/server-default column;
2. backfill existing rows;
3. set non-null;
4. retain or intentionally remove the server default according to runtime policy.

- [ ] **Step 3: Make model and migration names identical**

Do not “fix” drift by dropping legacy objects unless the normative migration explicitly replaces them and parity has passed.

- [ ] **Step 4: Verify**

```bash
cd app/backend
alembic upgrade head
alembic check
python -m pytest \
  tests/cdi_v2/test_model_contracts.py \
  tests/cdi_v2/test_revision_generation_migration.py \
  tests/cdi_v2/test_graph_migration.py \
  tests/cdi_v2/test_validated_stream_migration.py \
  tests/test_migrations.py -q
```

Expected:

```text
No new upgrade operations detected.
```

- [ ] **Step 5: Commit**

```bash
git add app/backend/src/hospital_ai/db app/backend/alembic app/backend/tests
git commit -m "fix: align CDI v2 models and migrations"
```

---

## Task 4: Make upload creation and finalization fail closed

**Plan coverage:** original Task 4 and acceptance scenario `upload_integrity_before_ocr`.

**Files:**
- Modify:
  - `app/backend/src/hospital_ai/services/storage.py`
  - `app/backend/src/hospital_ai/services/upload_sessions.py`
  - `app/backend/src/hospital_ai/api/routes/document_uploads.py`
  - `app/backend/src/hospital_ai/schemas/document_uploads.py`
- Tests:
  - `app/backend/tests/cdi_v2/test_upload_sessions.py`
  - `app/backend/tests/cdi_v2/test_upload_api.py`
  - `app/backend/tests/test_r2_storage.py`
  - `app/backend/tests/test_storage_api_integration.py`
  - create `app/backend/tests/security/test_storage_object_key_validation.py`

**Interfaces:**
- `hash_stream()` must either return bytes-derived SHA/prefix/size or raise.
- MIME detection must return an allowed exact type or reject.
- malware scanner unavailable/error must quarantine or reject.
- only `verified` can transition atomically to `finalized`.
- only finalized upload IDs can enter extraction.
- object keys are server-generated and immutable.

- [ ] **Step 1: Write failing integrity tests**

Cover:

- unreadable stream;
- short/partial stream;
- SHA mismatch;
- byte-size mismatch;
- unknown magic bytes;
- claimed MIME versus detected MIME mismatch;
- malware positive;
- scanner unavailable;
- duplicate object;
- storage HEAD error;
- presign error;
- concurrent finalize;
- retry of finalized upload;
- non-finalized extraction attempt.

Each failure must assert no `finalized_upload_id` and no OCR enqueue.

- [ ] **Step 2: Remove fail-open defaults**

Delete behavior that substitutes expected hashes, fixed prefixes, default PDF MIME, or hard-coded clean scans.

Introduce explicit adapters:

```python
class UploadContentReader(Protocol):
    async def hash_and_sniff(self, key: str) -> VerifiedObjectDigest: ...

class MalwareScanner(Protocol):
    async def scan(self, key: str) -> MalwareScanResult: ...
```

- [ ] **Step 3: Validate generated object keys**

Reject absolute paths, drive prefixes, `..`, backslashes, empty segments, and unexpected prefixes before calling local or R2 storage.

- [ ] **Step 4: Persist every lifecycle transition and audit outcome**

Use legal transitions only:

```text
pending_upload
→ uploaded_unverified
→ quarantined | verified | rejected
→ finalized
```

- [ ] **Step 5: Verify**

```bash
cd app/backend
python -m pytest \
  tests/cdi_v2/test_upload_sessions.py \
  tests/cdi_v2/test_upload_api.py \
  tests/test_r2_storage.py \
  tests/test_storage_api_integration.py \
  tests/security/test_storage_object_key_validation.py -q
```

- [ ] **Step 6: Commit**

```bash
git add app/backend/src/hospital_ai/services/storage.py \
  app/backend/src/hospital_ai/services/upload_sessions.py \
  app/backend/src/hospital_ai/api/routes/document_uploads.py \
  app/backend/src/hospital_ai/schemas/document_uploads.py \
  app/backend/tests
git commit -m "fix: fail closed on immutable source finalization"
```

---

## Task 5: Enforce one capability, permission, and identifier-binding boundary

**Plan coverage:** original Task 3 and every PHI-bearing API in Tasks 4, 5, 7, 9, 11, and 13.

**Files:**
- Modify:
  - `app/backend/src/hospital_ai/services/capabilities.py`
  - `app/backend/src/hospital_ai/services/permissions.py`
  - `app/backend/src/hospital_ai/api/routes/document_uploads.py`
  - `app/backend/src/hospital_ai/api/routes/document_revisions.py`
  - `app/backend/src/hospital_ai/api/routes/document_generations.py`
  - `app/backend/src/hospital_ai/api/routes/document_graph.py`
  - `app/backend/src/hospital_ai/api/routes/documents.py`
- Tests:
  - `app/backend/tests/cdi_v2/test_capabilities.py`
  - `app/backend/tests/cdi_v2/test_revision_api.py`
  - `app/backend/tests/cdi_v2/test_generation_api.py`
  - `app/backend/tests/cdi_v2/test_document_graph_api.py`
  - create `app/backend/tests/cdi_v2/test_identifier_binding_security.py`

**Interfaces:**
- Every route loads one resource aggregate and derives `patient_id` from that aggregate.
- Path IDs must all belong to the same aggregate.
- PHI reads require patient permission plus the relevant capability.
- 404 versus 403 behavior must follow the existing disclosure policy consistently.

- [ ] **Step 1: Write cross-resource negative tests**

Examples:

- authorized path document A + revision-set B;
- document A + generation B;
- document A + page revision B;
- patient A user + graph document B;
- ordinary graph/timeline read without patient permission;
- raw revision read without `document_revision.view_raw`.

Expected: no mutation/read and an audited denial.

- [ ] **Step 2: Add aggregate loaders**

Create focused helpers that return:

```python
DocumentRevisionAggregate(document, revision_set, page_revision)
DocumentGenerationAggregate(document, generation)
```

Each helper validates ownership before capability enforcement or mutation.

- [ ] **Step 3: Apply read capabilities**

At minimum:

- raw OCR/revision workspace: `document_revision.view_raw`;
- superseded evidence: `superseded_evidence.read`;
- graph/timeline/grounded evidence: existing patient read capability plus patient scope.

- [ ] **Step 4: Verify**

```bash
cd app/backend
python -m pytest \
  tests/cdi_v2/test_capabilities.py \
  tests/cdi_v2/test_revision_api.py \
  tests/cdi_v2/test_generation_api.py \
  tests/cdi_v2/test_document_graph_api.py \
  tests/cdi_v2/test_identifier_binding_security.py -q
```

- [ ] **Step 5: Commit**

```bash
git add app/backend/src/hospital_ai/services/capabilities.py \
  app/backend/src/hospital_ai/services/permissions.py \
  app/backend/src/hospital_ai/api/routes \
  app/backend/tests/cdi_v2
git commit -m "fix: bind CDI v2 authorization to patient resources"
```

---

## Task 6: Make idempotency durable and universal for writes

**Plan coverage:** original Task 3 and all write APIs.

**Files:**
- Modify:
  - `app/backend/src/hospital_ai/services/idempotency.py`
  - all CDI V2 write routes
- Tests:
  - `app/backend/tests/cdi_v2/test_idempotency.py`
  - route-level tests for upload, revision, generation.

**Interfaces:**
- Same actor/scope/key + same payload returns the stored status/body.
- Same key + different payload returns 409.
- In-progress duplicate has an explicit retry response.
- Domain mutation and completed response are committed atomically or recoverably.

- [ ] **Step 1: Add failing tests for reject, restore, retry, rollback, and finalize**

These routes currently accept a key without consistently using the service.

- [ ] **Step 2: Define transaction ownership**

Do not let a domain service commit before the idempotency record is completed. Prefer:

```python
async with session.begin():
    decision = await idempotency.begin(...)
    result = await domain_service.mutate(...)
    await idempotency.complete(...)
```

Domain services should flush, not commit, when called from routes.

- [ ] **Step 3: Verify concurrent requests**

Use two sessions against PostgreSQL to prove the unique key and row lock behavior.

- [ ] **Step 4: Run**

```bash
cd app/backend
python -m pytest tests/cdi_v2/test_idempotency.py tests/cdi_v2/test_*_api.py -q
```

- [ ] **Step 5: Commit**

```bash
git add app/backend/src/hospital_ai/services/idempotency.py \
  app/backend/src/hospital_ai/api/routes \
  app/backend/tests/cdi_v2
git commit -m "fix: make CDI v2 writes idempotent"
```

---

## Task 7: Correct immutable draft, submit, approval, rejection, restore, and geometry behavior

**Plan coverage:** original Task 5 and acceptance scenarios `stale_if_match`, `production_self_approval`, and `stale_geometry_not_exact_evidence`.

**Files:**
- Modify:
  - `app/backend/src/hospital_ai/services/revisions.py`
  - `app/backend/src/hospital_ai/api/routes/document_revisions.py`
  - `app/backend/src/hospital_ai/schemas/document_revisions.py`
  - `app/backend/src/hospital_ai/core/config.py`
- Tests:
  - `app/backend/tests/cdi_v2/test_revision_service.py`
  - `app/backend/tests/cdi_v2/test_revision_api.py`
  - create `app/backend/tests/cdi_v2/test_revision_state_machine.py`
  - create `app/backend/tests/cdi_v2/test_geometry_alignment.py`

**Interfaces:**
- parent revision must equal the draft head’s selected revision for that page.
- submit freezes a canonical ordered page list and content hash.
- approval authorizes a generation build but does not update published document pointers.
- self-approval requires all three server-side conditions:
  - configured synthetic self-approval flag;
  - configured demo mode;
  - document is explicitly synthetic.
- restore creates a legal `human_draft` revision in the same document/page.
- changed text marks inherited geometry `stale` unless exact realignment succeeds.

- [ ] **Step 1: Write state-transition table tests**

Legal transitions only:

```text
machine_draft → human_draft
machine_draft|human_draft → submitted revision set
submitted → build_authorized | rejected
build_authorized → approved only during successful activation
approved → superseded only during later successful activation
```

Do not add undocumented statuses such as `machine_initial` or `restored`.

- [ ] **Step 2: Implement canonical revision-set hashing**

Hash:

- document ID;
- ordered page number;
- page revision ID;
- page content SHA;
- geometry alignment state;
- schema version.

Do not hash a random revision-set UUID as the content proof.

- [ ] **Step 3: Implement geometry invalidation/realignment**

For any changed text:

- create new immutable revision;
- copy raw snapshot lineage;
- mark old geometry stale for the new revision, or run deterministic alignment;
- exact-evidence serialization must reject stale geometry.

- [ ] **Step 4: Move self-approval policy to server configuration**

Remove client `demo_mode` authority. The request may describe intent, but the server computes eligibility.

- [ ] **Step 5: Verify**

```bash
cd app/backend
python -m pytest \
  tests/cdi_v2/test_revision_service.py \
  tests/cdi_v2/test_revision_api.py \
  tests/cdi_v2/test_revision_state_machine.py \
  tests/cdi_v2/test_geometry_alignment.py -q
```

- [ ] **Step 6: Commit**

```bash
git add app/backend/src/hospital_ai/services/revisions.py \
  app/backend/src/hospital_ai/api/routes/document_revisions.py \
  app/backend/src/hospital_ai/schemas/document_revisions.py \
  app/backend/src/hospital_ai/core/config.py \
  app/backend/tests/cdi_v2
git commit -m "fix: enforce immutable revision authority"
```

---

## Task 8: Implement finalized-only OCR extraction and real resource controls

**Plan coverage:** original Task 6.

**Files:**
- Modify:
  - `app/backend/src/hospital_ai/services/ocr.py`
  - `app/backend/src/hospital_ai/services/ocr_routing.py`
  - `app/backend/src/hospital_ai/workers/ocr_models.py`
  - `app/backend/src/hospital_ai/workers/extraction_jobs.py`
  - `app/backend/src/hospital_ai/workers/jobs.py`
  - `app/backend/src/hospital_ai/core/config.py`
- Tests:
  - `app/backend/tests/cdi_v2/test_ocr_routing.py`
  - `app/backend/tests/cdi_v2/test_extraction_worker.py`
  - `app/backend/tests/test_ocr_service.py`
  - `app/backend/tests/workers/test_documents_pipeline.py`

**Interfaces:**
- extraction requires `document.finalized_upload_id` and upload state `finalized`.
- source SHA must be read from actual immutable bytes and match finalization evidence.
- model artifact path/revision/SHA is verified before load.
- one OCR model acquisition at a time on 4 GB profile.
- OOM/fallback/latency/RSS are persisted.
- idle unload is real and testable.

- [ ] **Step 1: Add failing extraction eligibility tests**

Reject documents with:

- no finalized upload;
- mismatched upload/document;
- rejected/quarantined upload;
- missing source object;
- source hash drift.

- [ ] **Step 2: Replace model-manager placeholders**

Implement:

- approved artifact manifest;
- SHA-256 file verification;
- RSS measurement;
- OOM classification;
- deterministic fallback policy;
- scheduled idle unload with cancellation on reuse.

- [ ] **Step 3: Persist valid machine revisions and geometry**

Use only declared states and exact engine metadata.

- [ ] **Step 4: Verify**

```bash
cd app/backend
python -m pytest \
  tests/cdi_v2/test_ocr_routing.py \
  tests/cdi_v2/test_extraction_worker.py \
  tests/test_ocr_service.py \
  tests/workers/test_documents_pipeline.py -q
```

- [ ] **Step 5: Commit**

```bash
git add app/backend/src/hospital_ai/services/ocr.py \
  app/backend/src/hospital_ai/services/ocr_routing.py \
  app/backend/src/hospital_ai/workers \
  app/backend/src/hospital_ai/core/config.py \
  app/backend/tests
git commit -m "fix: enforce finalized review-gated OCR extraction"
```

---

## Task 9: Make generation build and activation atomic and complete

**Plan coverage:** original Task 7 and acceptance scenario `failed_generation_preserves_active`.

**Files:**
- Modify:
  - `app/backend/src/hospital_ai/services/generations.py`
  - `app/backend/src/hospital_ai/workers/generation_jobs.py`
  - `app/backend/src/hospital_ai/workers/queue.py`
  - `app/backend/src/hospital_ai/api/routes/document_generations.py`
  - `app/backend/src/hospital_ai/services/audit.py`
- Tests:
  - `app/backend/tests/cdi_v2/test_generation_service.py`
  - `app/backend/tests/cdi_v2/test_generation_worker.py`
  - `app/backend/tests/cdi_v2/test_generation_api.py`
  - create `app/backend/tests/cdi_v2/test_generation_failure_injection.py`

**Interfaces:**
- required stages produce real rows and hashes:
  `ocr_normalization`, `facts`, `chunks`, `embeddings`, `lexical_index`, `graph`, `timeline`.
- a failed or partial stage never activates.
- graph extraction errors fail the graph stage unless explicitly classified as a permitted degraded mode in the normative contract.
- activation is one CAS transaction:
  - lock document;
  - verify expected old pointer;
  - verify complete stage set and generation hash;
  - set revision set approved;
  - set active generation and approved revision pointers;
  - supersede old generation/revision set;
  - append audit event.
- rollback always requires CAS, actor, reason, and audit.

- [ ] **Step 1: Add failure injection for every stage**

For each required stage, force an exception and assert:

- old generation remains active;
- old revision set remains authoritative;
- new generation is failed;
- failed stage is recorded;
- no staged rows leak into active reads.

- [ ] **Step 2: Stop mutating legacy `DocumentPage` during a staged build**

Build generation-owned rows only. A compatibility projection may update only after successful activation and only if the V1 compatibility contract requires it.

- [ ] **Step 3: Implement complete-build verification**

Require one successful stage result per required stage and a recomputed generation hash.

- [ ] **Step 4: Verify**

```bash
cd app/backend
python -m pytest \
  tests/cdi_v2/test_generation_service.py \
  tests/cdi_v2/test_generation_worker.py \
  tests/cdi_v2/test_generation_api.py \
  tests/cdi_v2/test_generation_failure_injection.py -q
```

- [ ] **Step 5: Commit**

```bash
git add app/backend/src/hospital_ai/services/generations.py \
  app/backend/src/hospital_ai/workers/generation_jobs.py \
  app/backend/src/hospital_ai/workers/queue.py \
  app/backend/src/hospital_ai/api/routes/document_generations.py \
  app/backend/src/hospital_ai/services/audit.py \
  app/backend/tests/cdi_v2
git commit -m "fix: activate complete CDI generations atomically"
```

---

## Task 10: Make backfill resumable and prove legacy parity before cutover

**Plan coverage:** original Task 8.

**Files:**
- Modify:
  - `app/backend/src/hospital_ai/migrations/cdi_v2_backfill.py`
  - `app/backend/scripts/backfill_cdi_v2.py`
  - `app/backend/src/hospital_ai/core/config.py`
- Create/Modify tests:
  - `app/backend/tests/cdi_v2/test_backfill.py`
  - `app/backend/tests/cdi_v2/test_legacy_parity.py`
  - create `app/backend/tests/cdi_v2/test_backfill_resume.py`

**Interfaces:**
- durable checkpoint table or audit record, not debug logging.
- dry-run produces no writes.
- apply is idempotent and resumes from last completed phase.
- real data is never auto-approved.
- parity artifact includes lexical/vector IDs, citation locators, graph provenance, source hashes, and authorization outcomes.

- [ ] **Step 1: Write restart tests**

Interrupt after each phase, rerun, and prove no duplicate revisions/sets/generations.

- [ ] **Step 2: Expand parity checks**

For a synthetic frozen fixture, compare V1 and V2:

- retrieved source IDs and ranks within documented tolerance;
- exact citation document/page/offset;
- graph assertion/evidence identity;
- wrong-patient exclusion;
- superseded exclusion;
- source/revision/generation hashes.

- [ ] **Step 3: Gate compatibility flag changes on a signed parity artifact**

Do not enable V2-only reads from a debug count.

- [ ] **Step 4: Verify**

```bash
cd app/backend
python -m pytest \
  tests/cdi_v2/test_backfill.py \
  tests/cdi_v2/test_backfill_resume.py \
  tests/cdi_v2/test_legacy_parity.py -q
python scripts/backfill_cdi_v2.py --dry-run
```

- [ ] **Step 5: Commit**

```bash
git add app/backend/src/hospital_ai/migrations \
  app/backend/scripts/backfill_cdi_v2.py \
  app/backend/tests/cdi_v2
git commit -m "fix: prove resumable CDI v2 backfill parity"
```

---

## Task 11: Apply one active-evidence scope to lexical, vector, graph, timeline, and chat

**Plan coverage:** original Tasks 9 and 11; acceptance scenario `wrong_patient_and_superseded_filtered`.

**Files:**
- Modify:
  - `app/backend/src/hospital_ai/services/evidence_scope.py`
  - `app/backend/src/hospital_ai/services/retrieval.py`
  - `app/backend/src/hospital_ai/services/bm25.py`
  - `app/backend/src/hospital_ai/services/graph_query.py`
  - `app/backend/src/hospital_ai/services/clinical_timeline.py`
  - `app/backend/src/hospital_ai/services/chat.py`
  - `app/backend/src/hospital_ai/api/routes/chat_stream.py`
- Tests:
  - `app/backend/tests/cdi_v2/test_evidence_scope.py`
  - `app/backend/tests/cdi_v2/test_revision_aware_retrieval.py`
  - `app/backend/tests/cdi_v2/test_graph_query.py`
  - `app/backend/tests/cdi_v2/test_clinical_timeline.py`
  - create `app/backend/tests/cdi_v2/test_cross_path_evidence_scope.py`

**Interfaces:**
- one composable predicate must enforce:
  - user patient permission;
  - requested patient;
  - document lifecycle;
  - active generation pointer;
  - generation state active;
  - approved revision set matching generation;
  - active/non-deleted source row;
  - optional document scope.
- audit-only superseded reads use an explicit separate scope and capability.

- [ ] **Step 1: Write a cross-path matrix test**

Seed active, superseded, wrong-patient, deleted, and unapproved rows. Execute all five paths and assert identical inclusion/exclusion.

- [ ] **Step 2: Refactor graph/timeline/chat to consume the shared scope**

Do not copy fragments of the predicate into separate services.

- [ ] **Step 3: Implement all declared graph filters or remove unsupported contract fields**

Filters must be tested for type, confidence, revision set, dates, document scope, and limits. Hop traversal must remain patient/generation scoped at every hop.

- [ ] **Step 4: Implement timeline projection**

Persist and query generation-owned events with conflict preservation and exact evidence IDs.

- [ ] **Step 5: Verify**

```bash
cd app/backend
python -m pytest \
  tests/cdi_v2/test_evidence_scope.py \
  tests/cdi_v2/test_revision_aware_retrieval.py \
  tests/cdi_v2/test_graph_query.py \
  tests/cdi_v2/test_clinical_timeline.py \
  tests/cdi_v2/test_cross_path_evidence_scope.py -q
```

- [ ] **Step 6: Commit**

```bash
git add app/backend/src/hospital_ai/services \
  app/backend/src/hospital_ai/api/routes/chat_stream.py \
  app/backend/tests/cdi_v2
git commit -m "fix: unify active evidence across CDI read paths"
```

---

## Task 12: Preserve graph provenance under concurrency and failures

**Plan coverage:** original Task 10 and acceptance scenario `canonical_entity_multiple_sources`.

**Files:**
- Modify:
  - `app/backend/src/hospital_ai/db/clinical_graph.py`
  - `app/backend/src/hospital_ai/services/graph_index.py`
  - `app/backend/src/hospital_ai/services/graph_rag.py`
  - `app/backend/src/hospital_ai/workers/generation_jobs.py`
- Tests:
  - `app/backend/tests/cdi_v2/test_graph_index.py`
  - `app/backend/tests/test_graph_rag_integration.py`
  - create `app/backend/tests/cdi_v2/test_graph_index_concurrency.py`
  - create `app/backend/tests/security/test_graph_logging.py`

**Interfaces:**
- entity/assertion upsert must be race-safe in PostgreSQL.
- each mention/evidence has stable source identity derived from immutable source/revision/page/chunk, not merely a transient chunk UUID.
- multiple independent sources attach to one canonical entity/assertion without overwriting prior evidence.
- graph stage failure is visible and blocks activation.
- logs contain IDs/hashes only where safe, never extracted clinical text/entities.

- [ ] **Step 1: Write concurrent upsert tests**

Run two sessions inserting the same canonical entity and assertion; assert one canonical row and two independent provenance rows.

- [ ] **Step 2: Replace select-then-insert with dialect-safe upsert/retry**

Handle uniqueness races deterministically.

- [ ] **Step 3: Remove PHI-bearing `print()` calls**

Use structured telemetry with trace ID, generation ID, counts, latency, and error code.

- [ ] **Step 4: Verify**

```bash
cd app/backend
python -m pytest \
  tests/cdi_v2/test_graph_index.py \
  tests/cdi_v2/test_graph_index_concurrency.py \
  tests/test_graph_rag_integration.py \
  tests/security/test_graph_logging.py -q
```

- [ ] **Step 5: Commit**

```bash
git add app/backend/src/hospital_ai/db/clinical_graph.py \
  app/backend/src/hospital_ai/services/graph_index.py \
  app/backend/src/hospital_ai/services/graph_rag.py \
  app/backend/src/hospital_ai/workers/generation_jobs.py \
  app/backend/tests
git commit -m "fix: preserve generation-scoped graph provenance"
```

---

## Task 13: Implement deterministic claim validation and wire validated SSE to production

**Plan coverage:** original Tasks 12 and 13; acceptance scenario `validated_sse_sequence_and_interrupt`.

**Files:**
- Modify:
  - `app/backend/src/hospital_ai/services/query_planner.py`
  - `app/backend/src/hospital_ai/services/claim_validation.py`
  - `app/backend/src/hospital_ai/services/validated_stream.py`
  - `app/backend/src/hospital_ai/services/chat.py`
  - `app/backend/src/hospital_ai/api/routes/chat_stream.py`
  - `app/backend/src/hospital_ai/schemas/chat.py`
  - `app/backend/src/hospital_ai/db/models.py`
- Tests:
  - `app/backend/tests/cdi_v2/test_query_planner.py`
  - `app/backend/tests/cdi_v2/test_claim_validation.py`
  - `app/backend/tests/cdi_v2/test_validated_stream.py`
  - `app/backend/tests/test_chat_stream_endpoint.py`
  - `app/backend/tests/test_graph_rag_chat_release_gates.py`
  - create `app/backend/tests/cdi_v2/test_stream_interruption_persistence.py`

**Interfaces:**
- sentence claims reference only evidence from the authorized allow-list.
- deterministic validators cover number, unit, date, and negation.
- auxiliary judge cannot override deterministic safety failure.
- provider tokens remain private until a sentence passes or is replaced by a safe refusal.
- event order:
  `status → metadata → token(1..n) → citations → graph_explanation → done`.
- disconnect/error persists `interrupted`, last emitted sequence, and validation mode.

- [ ] **Step 1: Replace hard-coded claim heuristics with table-driven tests**

Include:

- exact and conflicting numeric values;
- unit conversion policy;
- date ambiguity;
- negation/allergy contradiction;
- unknown evidence ID;
- wrong-patient evidence ID;
- superseded evidence ID;
- unsupported claim.

- [ ] **Step 2: Wire the real endpoint**

The production `chat_stream.py` must obtain the authorized evidence map, stream provider tokens into `ValidatedSentenceStreamer`, serialize only its events, and persist terminal/interrupted state.

- [ ] **Step 3: Test cancellation**

Cancel after token sequence N and assert no raw buffered fragment reached the client and the database stores N/interrupted.

- [ ] **Step 4: Verify**

```bash
cd app/backend
python -m pytest \
  tests/cdi_v2/test_query_planner.py \
  tests/cdi_v2/test_claim_validation.py \
  tests/cdi_v2/test_validated_stream.py \
  tests/cdi_v2/test_stream_interruption_persistence.py \
  tests/test_chat_stream_endpoint.py \
  tests/test_graph_rag_chat_release_gates.py -q
```

- [ ] **Step 5: Commit**

```bash
git add app/backend/src/hospital_ai/services \
  app/backend/src/hospital_ai/api/routes/chat_stream.py \
  app/backend/src/hospital_ai/schemas/chat.py \
  app/backend/src/hospital_ai/db/models.py \
  app/backend/tests
git commit -m "fix: stream only authorized validated claims"
```

---

## Task 14: Complete frontend contracts and remove unsafe bespoke sanitization

**Plan coverage:** original Tasks 14 and 17.

**Files:**
- Modify:
  - `app/frontend/src/lib/api/document-revisions.ts`
  - `app/frontend/src/lib/api/document-graph.ts`
  - `app/frontend/src/lib/api/document-timeline.ts`
  - `app/frontend/src/lib/api/documents.ts`
  - `app/frontend/src/lib/stream-client.ts`
  - `app/frontend/src/components/hms/ChatMessage.tsx`
  - `app/frontend/src/components/hms/EvidenceRail.tsx`
  - `app/frontend/src/components/hms/GraphExplanationPanel.tsx`
- Tests beside each file.

**Interfaces:**
- clients send idempotency and ETag headers where required.
- stream client rejects invalid order, duplicate/gap sequence, token before metadata, event after done, and missing done.
- rendered assistant content uses plain React text or a maintained Markdown pipeline with raw HTML disabled.
- links allow only explicit safe protocols.
- citations use stable evidence identity and exact page/region locators.

- [ ] **Step 1: Add security regression tests**

Inputs include malformed tags, encoded protocols, nested markup, split-tag payloads, and citation-like text. Assert no HTML execution and correct visible text.

- [ ] **Step 2: Remove regex HTML sanitization**

Preferred implementation:

- parse Markdown with raw HTML disabled;
- sanitize URLs at the AST/component boundary;
- or render plain text if Markdown is not required.

Do not retain unused `allowHtml`/`allowedProtocols` props.

- [ ] **Step 3: Strengthen stream state machine tests**

Test full fixed ordering, interruption, and terminal handling.

- [ ] **Step 4: Verify**

```bash
cd app/frontend
bun run lint
bun run typecheck
bun run test
bun run build
```

- [ ] **Step 5: Commit**

```bash
git add app/frontend/src/lib app/frontend/src/components/hms
git commit -m "fix: harden CDI evidence and stream presentation"
```

---

## Task 15: Complete direct upload and revision workspace behavior

**Plan coverage:** original Tasks 15 and 16.

**Files:**
- Modify:
  - `app/frontend/src/routes/_app.documents.upload.tsx`
  - `app/frontend/src/components/hms/document-upload/*`
  - `app/frontend/src/components/hms/document-workspace/*`
  - `app/frontend/src/routes/_app.documents.$documentId.tsx`
  - `app/frontend/src/routes/_app.documents.$documentId.review.tsx`
- Unit/component tests beside changed components.

**Interfaces:**
- upload state machine displays pending/uploaded-unverified/quarantined/verified/finalized/rejected accurately.
- direct PUT sends every required signed header including `If-None-Match: *`.
- editor uses returned ETag/lock version.
- 409 stale edit presents compare/reload behavior without discarding local text.
- stale geometry cannot show “exact evidence”.
- approval UI cannot offer client-controlled demo bypass.

- [ ] **Step 1: Add component tests for every state and conflict**

- [ ] **Step 2: Connect workspace actions to typed clients**

Remove hard-coded/default page/revision IDs.

- [ ] **Step 3: Verify**

```bash
cd app/frontend
bun run lint
bun run typecheck
bun run test
bun run build
```

- [ ] **Step 4: Commit**

```bash
git add app/frontend/src/routes app/frontend/src/components/hms/document-upload \
  app/frontend/src/components/hms/document-workspace
git commit -m "fix: complete CDI upload and revision workspace"
```

---

## Task 16: Implement real graph and timeline exploration

**Plan coverage:** original Tasks 11 and 17.

**Files:**
- Modify:
  - `app/frontend/src/components/hms/GraphFilters.tsx`
  - `app/frontend/src/components/hms/GraphCanvas.tsx`
  - `app/frontend/src/components/hms/GraphExplanationPanel.tsx`
  - `app/frontend/src/components/hms/ClinicalTimelinePanel.tsx`
  - graph/timeline routes
- Tests beside components and route loaders.

**Interfaces:**
- every visible node/edge/event carries stable provenance.
- filters map exactly to supported backend filters.
- superseded mode is visibly audit-only and capability-gated.
- exact evidence navigation includes document, revision, page, offsets/region, and alignment status.
- conflicting timeline events remain visible and labeled.

- [ ] **Step 1: Add component and route integration tests**

- [ ] **Step 2: Remove UI controls unsupported by backend or implement the backend contract first**

- [ ] **Step 3: Verify**

```bash
cd app/frontend
bun run lint
bun run typecheck
bun run test
bun run build
```

- [ ] **Step 4: Commit**

```bash
git add app/frontend/src/components/hms app/frontend/src/routes
git commit -m "fix: expose traceable graph and timeline evidence"
```

---

## Task 17: Replace synthetic evaluation defaults with measured artifacts

**Plan coverage:** original Task 18.

**Files:**
- Modify:
  - `app/backend/src/hospital_ai/evaluation/corpus_v3.py`
  - `app/backend/src/hospital_ai/evaluation/threshold_artifact.py`
  - `app/backend/src/hospital_ai/evaluation/unified_metrics.py`
  - product adapters
  - `app/backend/src/hospital_ai/evaluation/runner.py`
  - `app/backend/scripts/run_ai_evaluation.py`
  - schemas/manifests under `app/backend/data/evaluation/`
- Tests under `app/backend/tests/evaluation/`.

**Interfaces:**
- no evaluation summary field defaults to a perfect release result.
- missing observations create blocking state, not zero defects.
- threshold artifact format matches the repository’s actual Pydantic version.
- holdout cannot run until a verified frozen qualification artifact exists.
- report binds git SHA, corpus/source hashes, approved revisions, model/embedding/graph/prompt/evaluator/metric versions.

- [ ] **Step 1: Write missing-evidence tests**

Construct an empty/incomplete run and assert `BLOCKED`/`NO-GO`, never pass.

- [ ] **Step 2: Remove optimistic defaults**

Require explicit measured values or use `None` plus blocking validation.

- [ ] **Step 3: Verify artifact tampering and split policy**

- [ ] **Step 4: Run**

```bash
cd app/backend
python -m pytest tests/evaluation -q
python scripts/run_ai_evaluation.py --help
```

Run the synthetic smoke corpus with the actual repository CLI and save artifacts.

- [ ] **Step 5: Commit**

```bash
git add app/backend/src/hospital_ai/evaluation \
  app/backend/data/evaluation \
  app/backend/scripts/run_ai_evaluation.py \
  app/backend/tests/evaluation
git commit -m "fix: require measured CDI v2 evaluation evidence"
```

---

## Task 18: Replace fake release verification with artifact-backed gates

**Plan coverage:** original Task 19.

**Files:**
- Rewrite: `app/backend/scripts/verify_cdi_v2_release.py`
- Modify: `.github/workflows/ci.yml`
- Create:
  - `app/backend/tests/cdi_v2/test_release_verifier.py`
  - `app/backend/data/evaluation/release-evidence.schema.json`
  - `docs/09-testing/cdi-v2-release-evidence.md`

**Interfaces:**
- verifier reads explicit artifact paths.
- every required gate has source artifact, producer SHA, schema version, and hash.
- missing, stale, malformed, tampered, or wrong-SHA evidence returns non-zero.
- `--mode source` validates source contract only and cannot return release `GO`.
- only artifact mode may return `GO`.

- [ ] **Step 1: Write RED tests**

Cases:

- empty directory;
- one missing gate;
- failed gate;
- stale head SHA;
- hash mismatch;
- unsigned/unfrozen threshold;
- one reviewer;
- fake OCR output;
- complete valid synthetic fixture.

- [ ] **Step 2: Implement schema-validated evidence loading**

Delete:

```python
{gate: GateEvidence(passed=True) for gate in REQUIRED_GATES}
```

- [ ] **Step 3: Make CI pass artifact directory and expected SHA**

Example:

```bash
python scripts/verify_cdi_v2_release.py \
  --mode artifact \
  --evidence-dir artifacts/cdi-v2 \
  --expected-git-sha "$GITHUB_SHA"
```

- [ ] **Step 4: Verify**

```bash
cd app/backend
python -m pytest tests/cdi_v2/test_release_verifier.py -q
python scripts/verify_cdi_v2_release.py --mode artifact --evidence-dir /tmp/empty
```

Expected for empty evidence: `NO-GO`, non-zero exit.

- [ ] **Step 5: Commit**

```bash
git add app/backend/scripts/verify_cdi_v2_release.py \
  app/backend/tests/cdi_v2/test_release_verifier.py \
  app/backend/data/evaluation/release-evidence.schema.json \
  .github/workflows/ci.yml \
  docs/09-testing/cdi-v2-release-evidence.md
git commit -m "test: enforce artifact-backed CDI release gates"
```

---

## Task 19: Implement real normative backend acceptance scenarios

**Plan coverage:** original Task 19 and all nine normative scenarios.

**Files:**
- Rewrite:
  - `app/backend/tests/cdi_v2/conftest.py`
  - `app/backend/tests/cdi_v2/test_normative_acceptance.py`
- Create focused fixture/builders under:
  - `app/backend/tests/cdi_v2/acceptance/`

**Interfaces:**
- harness invokes actual services/routes/database/storage/queue fakes at contract boundaries.
- no `DummyHarness`, no constant pass/fail, no monkeypatch of the behavior under test.
- evidence contains persisted IDs, states, hashes, and denial/audit results.

- [ ] **Step 1: Implement one scenario at a time**

Order:

1. stale `If-Match`;
2. production self-approval denied;
3. failed generation preserves active A;
4. stale edited geometry not exact evidence;
5. canonical entity with multiple independent sources;
6. wrong-patient and superseded filtered across all paths;
7. upload integrity before OCR;
8. validated SSE order and interruption persistence;
9. legacy synthetic retrieval/citation parity.

For each scenario:

- write the failing assertion;
- run only that scenario;
- implement minimum production fix;
- rerun;
- remove any test-only bypass.

- [ ] **Step 2: Make evidence human-readable**

On failure, show resource IDs, expected/actual state, and the violated invariant without PHI.

- [ ] **Step 3: Verify**

```bash
cd app/backend
python -m pytest tests/cdi_v2/test_normative_acceptance.py -q
```

Expected: nine real scenarios pass.

- [ ] **Step 4: Commit**

```bash
git add app/backend/tests/cdi_v2
git commit -m "test: execute CDI v2 normative acceptance"
```

---

## Task 20: Implement the real Playwright end-to-end journey

**Plan coverage:** original Tasks 15–17 and 19.

**Files:**
- Rewrite:
  - `app/frontend/e2e/cdi-v2-document-intelligence.spec.ts`
  - `app/frontend/e2e/fixtures/api-mocks.ts`
- Modify:
  - `app/frontend/playwright.config.ts`
  - `.github/workflows/ci.yml`
- Create fixture data/scripts only where required.

**Interfaces:**
- no empty helper functions.
- test uses a running backend and database, or a contract-faithful mock server only for a separately named frontend-contract suite.
- two distinct users perform edit and approval.
- exact evidence navigation validates revision/page/region identity.

- [ ] **Step 1: Delete empty helper bodies and make the test fail at the first real action**

- [ ] **Step 2: Provide CI services**

Start backend, PostgreSQL, Redis, storage test adapter, and worker process or synchronous test queue.

- [ ] **Step 3: Execute journey**

1. log in as editor;
2. create direct upload session;
3. PUT synthetic scan with required headers;
4. finalize and wait for review-required extraction;
5. edit page with `If-Match`;
6. submit;
7. log in as different approver;
8. approve;
9. wait for active generation;
10. open graph and timeline provenance;
11. ask grounded question;
12. verify ordered validated tokens;
13. open exact evidence and assert revision/page/region.

- [ ] **Step 4: Add negative browser checks**

- stale editor conflict;
- self-approval unavailable;
- failed generation leaves prior evidence visible;
- invalid stream order shows safe error state.

- [ ] **Step 5: Verify**

```bash
cd app/frontend
bun run test:e2e -- cdi-v2-document-intelligence.spec.ts
```

- [ ] **Step 6: Commit**

```bash
git add app/frontend/e2e app/frontend/playwright.config.ts .github/workflows/ci.yml
git commit -m "test: run the complete CDI v2 browser journey"
```

---

## Task 21: Close GitHub Advanced Security findings with regression tests

**Plan coverage:** security quality required across original Tasks 4, 10, and 17.

**Files:**
- Modify:
  - `app/backend/src/hospital_ai/services/graph_rag.py`
  - `app/backend/src/hospital_ai/services/storage.py`
  - `app/frontend/src/components/hms/ChatMessage.tsx`
- Add focused security tests.

- [ ] **Step 1: Remove clear-text entity/patient logging**

- [ ] **Step 2: Add canonical storage-key validation before filesystem sinks**

Retain resolved-path containment as defense in depth.

- [ ] **Step 3: Replace regex markup sanitizer**

Use plain text or a maintained parser/sanitizer with raw HTML disabled.

- [ ] **Step 4: Run backend/frontend security regression tests and CodeQL**

Do not dismiss findings merely because unit tests pass.

- [ ] **Step 5: Commit**

```bash
git add app/backend/src/hospital_ai/services/graph_rag.py \
  app/backend/src/hospital_ai/services/storage.py \
  app/frontend/src/components/hms/ChatMessage.tsx \
  app/backend/tests app/frontend/src
git commit -m "fix: close CDI v2 security review findings"
```

---

## Task 22: Run the full same-SHA verification and correct PR claims

**Plan coverage:** final disposition for original Tasks 1–19.

**Files:**
- Modify: PR description/checklist only after evidence exists.
- Create/update:
  - `docs/09-testing/pr-89-final-verification.md`
  - generated evidence artifacts.

- [ ] **Step 1: Freeze the candidate SHA**

```bash
git rev-parse HEAD
git status --short
```

Require clean working tree.

- [ ] **Step 2: Backend quality and tests**

```bash
cd app/backend
python -m ruff check .
python -m ruff format --check .
python -m pytest -q
python scripts/verify_contracts.py
```

- [ ] **Step 3: Migration validation on fresh and populated databases**

```bash
alembic upgrade head
alembic check
```

Run repository downgrade/upgrade and populated-fixture migration tests.

- [ ] **Step 4: Evaluation and release gates**

Run the synthetic smoke corpus, produce hashed artifacts, then:

```bash
python scripts/verify_cdi_v2_release.py \
  --mode artifact \
  --evidence-dir artifacts/cdi-v2 \
  --expected-git-sha "$(git rev-parse HEAD)"
```

- [ ] **Step 5: Frontend**

```bash
cd ../frontend
bun run lint
bun run typecheck
bun run test
bun run build
bun run test:e2e -- cdi-v2-document-intelligence.spec.ts
```

- [ ] **Step 6: GitHub checks**

Push once, then verify on the same SHA:

- backend;
- migration;
- frontend/E2E;
- evaluation;
- CodeQL;
- final CI summary.

Do not reuse evidence from an older SHA.

- [ ] **Step 7: Correct PR description**

Only then replace “completes all 19 tasks” with an evidence table linking each gate, command, artifact, and SHA.

- [ ] **Step 8: Final review disposition**

- `APPROVE` only if every required check passes on the frozen SHA and no blocking review thread remains.
- otherwise keep `REQUEST CHANGES` and list the exact failed gate.

---

## Original 19-task coverage map

| Original task | Closure tasks in this plan |
|---|---|
| 1 ORM contracts | 3 |
| 2 forward migration | 3 |
| 3 capabilities/idempotency | 5, 6 |
| 4 immutable upload | 4 |
| 5 revision workflow | 7 |
| 6 OCR/extraction | 8 |
| 7 generations | 9 |
| 8 backfill/parity | 10 |
| 9 active-generation retrieval | 11 |
| 10 graph provenance | 3, 12 |
| 11 graph/timeline APIs | 5, 11, 16 |
| 12 planner/claim validation | 13 |
| 13 validated SSE | 3, 13 |
| 14 frontend contracts | 14 |
| 15 direct upload UI | 15, 20 |
| 16 OCR workspace | 15, 20 |
| 17 graph/timeline/evidence UI | 14, 16, 20 |
| 18 corpus/threshold/metrics | 17 |
| 19 acceptance/CI/release | 1, 18, 19, 20, 21, 22 |

## Plan self-review

### Review checklist

- [x] Every original task maps to at least one closure task.
- [x] Every blocking code-review finding has a production fix task and a regression test.
- [x] Migration work precedes acceptance and release verification.
- [x] Authorization includes both patient permission and capability enforcement.
- [x] Path-resource identifier binding is explicitly tested.
- [x] Upload, OCR, revision, generation, retrieval, graph, timeline, chat, frontend, evaluation, and CI are covered.
- [x] No task accepts placeholder, constant, mocked-success, skipped, or advisory evidence.
- [x] Each implementation task contains RED, GREEN/implementation, verification command, and commit boundary.
- [x] Final completion requires fresh same-SHA evidence.
- [x] GitHub Advanced Security findings are included rather than treated as unrelated.

### Defects found during plan review and corrected

1. **Initial ordering risk:** fixing CI alone could expose acceptance failures late.  
   **Correction:** baseline and lint are first, but schema, security, and authority invariants are repaired before acceptance.

2. **Authority ambiguity:** “approval” could still be interpreted as publishing the revision pointer.  
   **Correction:** Task 7 explicitly makes approval build authorization only; Task 9 publishes revision/generation authority together during successful CAS activation.

3. **Idempotency transaction gap:** route handlers could complete domain commits before recording replay data.  
   **Correction:** Task 6 defines route-owned transaction boundaries and domain-service flush semantics.

4. **Cross-patient confused-deputy gap:** capability checks alone do not bind nested IDs.  
   **Correction:** Task 5 adds aggregate loaders and adversarial mixed-ID tests.

5. **False release confidence:** source-presence verification could still return `GO`.  
   **Correction:** Task 18 prohibits source mode from returning release `GO` and requires artifact mode with expected SHA.

6. **Frontend-only E2E risk:** contract mocks could pass without backend behavior.  
   **Correction:** Task 20 requires a running backend for the normative journey and separates any mock-based suite.

7. **Graph error swallowing:** a generated hash could hide missing graph rows.  
   **Correction:** Task 9/12 require stage failure visibility and row/hash completeness.

8. **Security findings could be deferred after functional green.**  
   **Correction:** Task 21 is a blocking closure task before final same-SHA verification.

### Final plan assessment

The plan is implementation-ready and covers all 19 original tasks plus the newly discovered defect-closure work. It intentionally does **not** estimate completion or claim any fix has passed; execution must produce fresh command output and artifacts before status changes.
