# Unified Clinical Document Intelligence V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the complete CDI-RAG-V2 contract so finalized source objects become immutable OCR revisions, approved revision sets produce atomically activated retrieval/graph generations, and authorized users can review, explore, chat, and benchmark against exact source evidence.

**Architecture:** Add revision, upload, geometry, generation, graph-provenance, claim-validation, and idempotency records beside the current `DocumentPage`/`DocumentChunk` read model. Keep legacy reads available behind compatibility flags while backfill and parity gates run; switch lexical, vector, graph, timeline, and chat reads to one shared active-generation scope only after migration evidence passes. Extraction creates immutable machine drafts, approval queues a generation, and one compare-and-swap transaction activates all derived projections without deleting the prior serving generation.

**Tech Stack:** Python 3.12, FastAPI 0.95/Pydantic 1.x, SQLAlchemy 2 async, Alembic, PostgreSQL 16 + pgvector, Redis/RQ, boto3/Cloudflare R2, PyMuPDF, PaddleOCR, optional VietOCR/TrOCR workers, TanStack Start, React 19, TanStack Query/Router, TypeScript 5.8, Bun, Vitest, Playwright, GitHub Actions.

## Global Constraints

- Normative source: `docs/superpowers/specs/2026-08-04-unified-clinical-document-intelligence-v2-design.md`; V1 remains authoritative for roles, accepted formats, observability, and deployment where V2 does not replace it.
- Full integrated target: no MVP shortcuts, no multi-tenancy, no `tenant_id`, and no new role such as `clinical_reviewer`.
- Every PHI-bearing read or write requires both patient permission and the relevant existing-role capability.
- Raw source bytes, raw machine OCR, immutable page revisions, frozen revision sets, audit events, and completed generations are never overwritten by ordinary edit, retry, approval, activation, restore, or rollback.
- R2 buckets stay private; object keys are unique and immutable; browser PUT uses `If-None-Match: *`; only verified and atomically finalized uploads may enter OCR.
- Every write API requires `Idempotency-Key`; draft-page save and draft submit also require `If-Match: <lock_version>`.
- Approval and rollback update revision/generation authority atomically; a failed build leaves the previous active generation serving.
- Lexical, vector, graph, timeline, and grounded-chat paths apply the same patient, lifecycle, and per-document active-generation predicate before ranking or serialization.
- Production self-approval is forbidden. `ALLOW_SELF_APPROVAL_FOR_SYNTHETIC_DATA=true` works only with `demo_mode=true` and an explicitly synthetic document.
- OCR worker concurrency is `1` for the 4 GB profile; model identity, revision, artifact hash, latency, and peak RSS are recorded; OOM and fallback are explicit.
- Unvalidated model tokens never reach the client. Successful SSE order is `status → metadata → token(sequence=1..n) → citations → graph_explanation → done`.
- Test and demo data is synthetic or explicitly de-identified; no real PHI is sent to external providers.
- Use RED → GREEN → REFACTOR for every task. Run GitNexus impact before editing existing symbols and `detect_changes({scope: "compare", base_ref: "main"})` before each commit.
- `DocumentPage` currently has CRITICAL blast radius (44 upstream references). Do not remove it or change its meaning until the migration parity gate passes.
- On Windows, create and activate the backend environment with Python 3.12 (`py -3.12 -m venv .venv`); every `python` and `alembic` command below assumes that environment is active.

---

## File Structure and Responsibility Map

### Database and migration

- Create `app/backend/src/hospital_ai/db/clinical_documents.py` — upload sessions, extraction runs, immutable page revisions, draft heads, revision sets/pages/events, OCR geometry, index generations, generation stage results, idempotency records, claim validation records, and clinical timeline rows.
- Create `app/backend/src/hospital_ai/db/clinical_graph.py` — patient-scoped canonical entities/assertions and source-scoped mentions/evidence.
- Modify `app/backend/src/hospital_ai/db/models.py:210` — add document authority pointers/retention metadata and generation lineage columns on chunks/facts/evidence while retaining legacy fields during compatibility mode.
- Create `app/backend/alembic/versions/cdi_v2_0001_add_revision_generation_schema.py` — expand schema without deleting legacy rows.
- Create `app/backend/alembic/versions/cdi_v2_0002_add_graph_provenance_schema.py` — convert legacy graph tables into provenance-preserving V2 tables.
- Create `app/backend/alembic/versions/cdi_v2_0003_add_validated_stream_state.py` — persist validated-stream mode, sequence, and interruption state.
- Create `app/backend/src/hospital_ai/migrations/cdi_v2_backfill.py` — resumable, auditable machine-v1/revision-set/legacy-generation backfill.
- Create `app/backend/scripts/backfill_cdi_v2.py` — dry-run/apply/parity CLI.

### Backend application contracts

- Create `app/backend/src/hospital_ai/services/capabilities.py` — existing-role capability grants plus patient-scope enforcement.
- Create `app/backend/src/hospital_ai/services/idempotency.py` — payload hash, replay, conflict, and response persistence.
- Create `app/backend/src/hospital_ai/services/upload_sessions.py` — upload state machine, presigned PUT, verification, quarantine, and atomic finalization.
- Create `app/backend/src/hospital_ai/services/revisions.py` — immutable page save, submit, approve, reject, restore, and draft locking.
- Create `app/backend/src/hospital_ai/services/generations.py` — build/retry/activate/rollback transactions and stage hashes.
- Create `app/backend/src/hospital_ai/services/evidence_scope.py` — one active-generation authorization predicate shared by all retrieval stores.
- Create `app/backend/src/hospital_ai/services/graph_index.py` — canonicalization and generation-scoped provenance writes.
- Create `app/backend/src/hospital_ai/services/graph_query.py` — filtered graph, explanation paths, and audit-only superseded reads.
- Create `app/backend/src/hospital_ai/services/clinical_timeline.py` — generation-scoped timeline derivation and conflict preservation.
- Create `app/backend/src/hospital_ai/services/query_planner.py` — deterministic retrieval-strategy selection.
- Create `app/backend/src/hospital_ai/services/claim_validation.py` — sentence claims, evidence allow-list, numeric/unit/date/negation checks, and optional auxiliary judge.
- Create `app/backend/src/hospital_ai/services/validated_stream.py` — private sentence buffer and validated SSE chunks.
- Modify `app/backend/src/hospital_ai/services/storage.py:21` — immutable object operations, HEAD, conditional PUT metadata, presigned URLs, and delete-by-retention contract.
- Modify `app/backend/src/hospital_ai/services/ocr.py:9` — rich page/line geometry and adaptive routing result types.
- Modify `app/backend/src/hospital_ai/workers/jobs.py:18` — extraction job delegates to focused services and no longer deletes/recreates serving rows.
- Create `app/backend/src/hospital_ai/workers/extraction_jobs.py` — extraction-only worker entrypoint; `jobs.py` remains a compatibility façade during cutover.
- Create `app/backend/src/hospital_ai/workers/generation_jobs.py` — generation build and retry worker entrypoints.
- Create `app/backend/src/hospital_ai/workers/ocr_models.py` — lazy load, pinned artifact verification, idle unload, RSS/OOM controls.
- Modify `app/backend/src/hospital_ai/services/retrieval.py:70` — active-generation lexical/vector filters and generation metadata.
- Modify `app/backend/src/hospital_ai/services/graph_rag.py:40` — use V2 graph models/query service while preserving the offline extractor contract.
- Modify `app/backend/src/hospital_ai/api/routes/documents.py:41` — preserve existing reads and mount focused upload/revision/generation routers.
- Create `app/backend/src/hospital_ai/api/routes/document_uploads.py` — upload-session endpoints.
- Create `app/backend/src/hospital_ai/api/routes/document_revisions.py` — revision-set/draft/approval/rejection/restore endpoints.
- Create `app/backend/src/hospital_ai/api/routes/document_generations.py` — generation retry and synchronous rollback endpoints.
- Create `app/backend/src/hospital_ai/api/routes/document_graph.py` — document-scoped graph and timeline endpoints.
- Modify `app/backend/src/hospital_ai/api/router.py:34` — register the new `/api/v1` routers.
- Create `app/backend/src/hospital_ai/schemas/document_uploads.py`, `document_revisions.py`, `document_generations.py`, `document_graph.py`, and `idempotency.py` — focused Pydantic 1 request/response contracts.
- Modify `app/backend/src/hospital_ai/api/routes/chat_stream.py:693` and `services/chat.py` — shared active evidence, claim validation, and sentence-buffered transport.

### Frontend

- Create `app/frontend/src/lib/api/document-revisions.ts`, `document-graph.ts`, and `document-timeline.ts` — typed V2 API clients with idempotency and ETag support.
- Modify `app/frontend/src/lib/api/documents.ts:3` — upload-session flow and generation-aware evidence fields while retaining current list/detail types.
- Modify `app/frontend/src/lib/stream-client.ts:13` — sequence validation, graph explanation, terminal contract, and interruption handling.
- Modify `app/frontend/src/routes/_app.documents.upload.tsx` and create `app/frontend/src/components/hms/document-upload/` — browser-direct R2 upload and verification state machine.
- Create focused components under `app/frontend/src/components/hms/document-workspace/` — toolbar, revision selector, page navigator, OCR editor, diff, geometry overlay, structured facts, and history drawer.
- Modify `app/frontend/src/routes/_app.documents.$documentId.tsx:25` — compose the revision-aware workspace.
- Modify `app/frontend/src/routes/_app.documents.$documentId.review.tsx:26` — keep structured-fact review as the second review layer.
- Create `app/frontend/src/components/hms/GraphFilters.tsx`, `GraphExplanationPanel.tsx`, and `ClinicalTimelinePanel.tsx`.
- Modify `app/frontend/src/components/hms/EvidenceRail.tsx:15`, `ChatMessage.tsx`, and graph/timeline routes — stable evidence identity, exact page/region navigation, safe Markdown, and provenance.

### Tests, corpus, and gates

- Add focused backend tests under `app/backend/tests/cdi_v2/` for schema, capabilities, idempotency, upload, revisions, OCR, generations, retrieval, graph, timeline, claim validation, SSE, migration, and acceptance scenarios.
- Add frontend unit tests beside each new API client/component and Playwright flow `app/frontend/e2e/cdi-v2-document-intelligence.spec.ts`.
- Create `app/backend/src/hospital_ai/evaluation/corpus_v3.py`, `threshold_artifact.py`, and `unified_metrics.py`.
- Create `app/backend/data/evaluation/corpus-v3.schema.json`, `thresholds-v3.schema.json`, and a synthetic smoke manifest bound to `hospital-ai-unified-clinical-corpus-v3`.
- Modify `app/backend/src/hospital_ai/evaluation/runner.py:487`, `scripts/run_ai_evaluation.py`, and `.github/workflows/ci.yml` — frozen-threshold and full release gates.

---

### Task 1: Add Immutable Revision, Upload, Geometry, and Generation ORM Contracts

**Files:**
- Create: `app/backend/src/hospital_ai/db/clinical_documents.py`
- Modify: `app/backend/src/hospital_ai/db/models.py:210-315`
- Test: `app/backend/tests/cdi_v2/test_model_contracts.py`

**Interfaces:**
- Consumes: existing `Base`, `TimestampMixin`, `EncryptedText`, `Document`, `DocumentPage`, `DocumentChunk`, `User`.
- Produces: `DocumentUpload`, `DocumentExtractionRun`, `DocumentPageRevision`, `DocumentDraftHead`, `DocumentRevisionSet`, `DocumentRevisionPage`, `DocumentRevisionEvent`, `DocumentIndexGeneration`, `GenerationStageResult`, `OcrBlock`, `OcrLine`, `OcrSpan`, `IdempotencyRecord`, `ClaimValidationResult`, `ClinicalTimelineEvent`.
- Produces document pointers: `approved_revision_set_id: UUID | None`, `active_index_generation_id: UUID | None`, `finalized_upload_id: UUID | None`, `is_synthetic: bool`, `retention_state: str`.
- Produces chunk lineage: `generation_id`, `revision_set_id`, `page_revision_id`, `text_start_offset`, `text_end_offset`, `source_text_sha256`, `approval_state`, `bounding_boxes`, `access_tags`.

- [ ] **Step 1: Write failing metadata contract tests**

```python
def test_v2_lineage_tables_and_document_pointers_are_registered() -> None:
    expected = {
        "document_uploads",
        "document_extraction_runs",
        "document_page_revisions",
        "document_draft_heads",
        "document_revision_sets",
        "document_revision_pages",
        "document_revision_events",
        "document_index_generations",
        "generation_stage_results",
        "ocr_blocks",
        "ocr_lines",
        "ocr_spans",
        "idempotency_records",
        "claim_validation_results",
        "clinical_timeline_events",
    }
    assert expected <= set(Base.metadata.tables)
    assert "approved_revision_set_id" in Document.__table__.c
    assert "active_index_generation_id" in Document.__table__.c
    assert "generation_id" in DocumentChunk.__table__.c


def test_v2_status_checks_are_exact() -> None:
    assert DOCUMENT_UPLOAD_STATES == frozenset(
        {"pending_upload", "uploaded_unverified", "quarantined", "verified", "finalized", "rejected"}
    )
    assert GENERATION_STATES == frozenset({"building", "active", "failed", "superseded"})
    assert ALIGNMENT_STATES == frozenset({"aligned", "partially_aligned", "stale"})
```

- [ ] **Step 2: Run the tests and verify RED**

Run: `cd app/backend; python -m pytest tests/cdi_v2/test_model_contracts.py -q`

Expected: FAIL because `hospital_ai.db.clinical_documents` and the V2 columns do not exist.

- [ ] **Step 3: Define immutable state constants and core ORM records**

```python
DOCUMENT_UPLOAD_STATES = frozenset(
    {"pending_upload", "uploaded_unverified", "quarantined", "verified", "finalized", "rejected"}
)
PAGE_REVISION_STATES = frozenset(
    {"machine_draft", "human_draft", "approved", "rejected", "superseded"}
)
REVISION_SET_STATES = frozenset({"submitted", "approved", "rejected", "superseded"})
GENERATION_STATES = frozenset({"building", "active", "failed", "superseded"})
ALIGNMENT_STATES = frozenset({"aligned", "partially_aligned", "stale"})


class DocumentDraftHead(TimestampMixin, Base):
    __tablename__ = "document_draft_heads"
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), primary_key=True)
    selected_pages: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)
    lock_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    updated_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)


class DocumentIndexGeneration(Base):
    __tablename__ = "document_index_generations"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=False, index=True)
    revision_set_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("document_revision_sets.id"), nullable=False, index=True
    )
    retry_of_generation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("document_index_generations.id"), nullable=True
    )
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="building")
    revision_set_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    generation_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failure_code: Mapped[str | None] = mapped_column(String(64))
    failure_detail: Mapped[str | None] = mapped_column(Text)
```

Define every remaining record listed in **Produces** with the exact fields and enum checks from spec sections 6.3, 7.2, 7.4, 10.2, 11.1, and 12.4. Mark revision/event/generation source columns non-null for newly created rows; use nullable lineage only on legacy `DocumentChunk`, `ClinicalFact`, and `RetrievedEvidence` columns during backfill.

- [ ] **Step 4: Register sidecar models and add compatibility columns**

```python
class Document(TimestampMixin, SoftDeleteMixin, Base):
    # existing columns remain unchanged
    approved_revision_set_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("document_revision_sets.id", use_alter=True), nullable=True
    )
    active_index_generation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("document_index_generations.id", use_alter=True), nullable=True
    )
    finalized_upload_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("document_uploads.id", use_alter=True), nullable=True
    )
    is_synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    retention_state: Mapped[str] = mapped_column(String(32), nullable=False, default="active")


# At the bottom of models.py, after Base and legacy models exist:
from hospital_ai.db import clinical_documents as _clinical_documents  # noqa: E402,F401
```

- [ ] **Step 5: Run metadata and existing model tests**

Run: `cd app/backend; python -m pytest tests/cdi_v2/test_model_contracts.py tests/test_migrations.py -q`

Expected: PASS; existing `DocumentPage.ocr_text` and current relationships remain available.

- [ ] **Step 6: Commit**

```bash
git add app/backend/src/hospital_ai/db/clinical_documents.py app/backend/src/hospital_ai/db/models.py app/backend/tests/cdi_v2/test_model_contracts.py
git commit -m "backend: add CDI v2 lineage models"
```

### Task 2: Add the Forward Revision/Generation Migration

**Files:**
- Create: `app/backend/alembic/versions/cdi_v2_0001_add_revision_generation_schema.py`
- Modify: `app/backend/alembic/env.py:7`
- Create: `app/backend/tests/cdi_v2/test_revision_generation_migration.py`
- Modify: `app/backend/tests/test_migrations.py`

**Interfaces:**
- Consumes: Task 1 metadata and current Alembic head `5a950640275c` (`5a950640275c ← 13dde695c97d ← 8d6cedbd7e08`).
- Produces: revision `cdi_v2_0001`, all core V2 tables/constraints/indexes, nullable compatibility columns, and a reversible downgrade that removes only V2 schema.

- [ ] **Step 1: Write failing migration-chain and constraint tests**

```python
def test_cdi_v2_revision_has_one_forward_parent() -> None:
    module = load_revision("cdi_v2_0001_add_revision_generation_schema.py")
    assert module.revision == "cdi_v2_0001"
    assert module.down_revision == "5a950640275c"


def test_cdi_v2_migration_contains_atomic_authority_schema() -> None:
    text = migration_text("cdi_v2_0001_add_revision_generation_schema.py")
    for fragment in (
        "document_uploads",
        "document_page_revisions",
        "document_revision_sets",
        "document_index_generations",
        "approved_revision_set_id",
        "active_index_generation_id",
        "idempotency_records",
    ):
        assert fragment in text
    assert "tenant_id" not in text
```

- [ ] **Step 2: Run migration tests and verify RED**

Run: `cd app/backend; python -m pytest tests/cdi_v2/test_revision_generation_migration.py tests/test_migrations.py -q`

Expected: FAIL because revision `cdi_v2_0001` is absent.

- [ ] **Step 3: Write the migration with explicit checks and indexes**

```python
revision = "cdi_v2_0001"
down_revision = "5a950640275c"


def upgrade() -> None:
    op.create_table(
        "document_revision_sets",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("document_id", sa.Uuid(), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_by_user_id", sa.Uuid(), sa.ForeignKey("users.id")),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            "status in ('submitted','approved','rejected','superseded')",
            name="ck_document_revision_sets_status",
        ),
        sa.UniqueConstraint("document_id", "revision_number", name="uq_document_revision_set_number"),
    )
    # Create the remaining Task 1 tables before adding cyclic document pointers.
    with op.batch_alter_table("documents") as batch:
        batch.add_column(sa.Column("approved_revision_set_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("active_index_generation_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("finalized_upload_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("is_synthetic", sa.Boolean(), server_default=sa.false(), nullable=False))
        batch.add_column(sa.Column("retention_state", sa.String(32), server_default="active", nullable=False))
```

Create indexes for every foreign key used by patient/document/generation filtering and unique constraints for `(document_id, revision_number)`, `(revision_set_id, page_number)`, `(actor_user_id, scope, idempotency_key_hash)`, and `(generation_id, stage)`. Add cyclic foreign keys only after both sides exist. Register sidecar metadata from `app/backend/alembic/env.py` so `alembic check` sees the new tables.

- [ ] **Step 4: Prove upgrade, downgrade, and re-upgrade on PostgreSQL**

Run against an ephemeral PostgreSQL database: `cd app/backend; alembic upgrade head; alembic downgrade 5a950640275c; alembic upgrade head`

Expected: all three commands exit `0`; no duplicate Alembic head is created.

- [ ] **Step 5: Run migration-model alignment as a blocking check**

Run: `cd app/backend; alembic check`

Expected: `No new upgrade operations detected.` Do not accept the current CI advisory `|| true` for this feature branch.

- [ ] **Step 6: Commit**

```bash
git add app/backend/alembic/versions/cdi_v2_0001_add_revision_generation_schema.py app/backend/alembic/env.py app/backend/tests/cdi_v2/test_revision_generation_migration.py app/backend/tests/test_migrations.py
git commit -m "backend: migrate CDI v2 revision schema"
```

### Task 3: Add Existing-Role Capabilities and Idempotent Write Infrastructure

**Files:**
- Create: `app/backend/src/hospital_ai/services/capabilities.py`
- Create: `app/backend/src/hospital_ai/services/idempotency.py`
- Create: `app/backend/src/hospital_ai/schemas/idempotency.py`
- Modify: `app/backend/src/hospital_ai/core/errors.py:4-29`
- Modify: `app/backend/src/hospital_ai/services/permissions.py:68-268`
- Test: `app/backend/tests/cdi_v2/test_capabilities.py`
- Test: `app/backend/tests/cdi_v2/test_idempotency.py`

**Interfaces:**
- Produces: `DocumentCapability` literal values from spec section 16.1.
- Produces: `CapabilityService.require(user, patient_id, capability, ...) -> None` with capability-specific accepted patient scopes; authoring capabilities accept active read or upload/admin scope, while product evidence reads require read/admin scope.
- Produces: `IdempotencyService.begin(scope, key, payload) -> IdempotencyDecision` and `complete(record_id, status_code, response_body) -> None`.
- Rule: a matching replay returns the stored response with no duplicate domain or audit side effect; a reused key with a different SHA-256 payload raises HTTP 409.
- Produces: `ConflictError(AppError)` with `status_code = 409` and `code = "CONFLICT"`, covered through the normal API error envelope.

- [ ] **Step 1: Write failing role-matrix and replay tests**

```python
@pytest.mark.parametrize(
    ("role", "capability", "allowed"),
    [
        ("doctor", "document_revision.edit", True),
        ("doctor", "document_revision.approve", False),
        ("records_staff", "document_revision.restore", True),
        ("admin", "document_revision.edit", False),
        ("admin", "document_revision.approve", True),
        ("security", "document_revision.view_raw", False),
    ],
)
def test_default_capability_matrix(role: str, capability: str, allowed: bool) -> None:
    assert role_has_capability(role, capability) is allowed


async def test_same_idempotency_key_replays_once(session) -> None:
    service = IdempotencyService(session)
    first = await service.begin("draft.save", "key-1", {"text": "A"})
    await service.complete(first.record_id, 201, {"revision_id": "r1"})
    replay = await service.begin("draft.save", "key-1", {"text": "A"})
    assert replay.is_replay is True
    assert replay.response_body == {"revision_id": "r1"}
```

- [ ] **Step 2: Run focused tests and verify RED**

Run: `cd app/backend; python -m pytest tests/cdi_v2/test_capabilities.py tests/cdi_v2/test_idempotency.py -q`

Expected: FAIL because the two services do not exist.

- [ ] **Step 3: Implement the exact role-capability map and patient gate**

```python
ROLE_CAPABILITIES: Final[dict[str, frozenset[str]]] = {
    "doctor": frozenset({"document_revision.view_raw", "document_revision.edit"}),
    "records_staff": frozenset(
        {
            "document_revision.view_raw",
            "document_revision.edit",
            "document_revision.reject",
            "document_revision.restore",
            "superseded_evidence.read",
        }
    ),
    "admin": frozenset(
        {
            "document_revision.reject",
            "document_revision.approve",
            "document_revision.restore",
            "ocr_engine.override",
            "superseded_evidence.read",
        }
    ),
    "nurse": frozenset({"document_revision.view_raw"}),
    "pharmacist": frozenset({"document_revision.view_raw"}),
    "lab_staff": frozenset({"document_revision.view_raw"}),
    "security": frozenset(),
}

AUTHORING_PATIENT_SCOPES = frozenset(set(PATIENT_READ_SCOPES) | set(PATIENT_UPLOAD_SCOPES))
CAPABILITY_PATIENT_SCOPES: Final[dict[str, frozenset[str]]] = {
    "document_revision.view_raw": AUTHORING_PATIENT_SCOPES,
    "document_revision.edit": AUTHORING_PATIENT_SCOPES,
    "document_revision.reject": AUTHORING_PATIENT_SCOPES,
    "document_revision.approve": AUTHORING_PATIENT_SCOPES,
    "document_revision.restore": AUTHORING_PATIENT_SCOPES,
    "ocr_engine.override": AUTHORING_PATIENT_SCOPES,
    "superseded_evidence.read": frozenset(PATIENT_READ_SCOPES),
}


class ConflictError(AppError):
    status_code = 409
    code = "CONFLICT"


async def require(
    self,
    *,
    user: User,
    patient_id: uuid.UUID,
    capability: str,
    action: str,
    trace_id: str,
    object_id: uuid.UUID | None = None,
) -> None:
    if not role_has_capability(user.role, capability):
        await self._deny(user, patient_id, capability, action, trace_id, object_id)
    accepted_scopes = CAPABILITY_PATIENT_SCOPES[capability]
    await PermissionService(self.session).require_patient_scope(
        user=user,
        patient_id=patient_id,
        accepted_scopes=accepted_scopes,
        action=action,
        trace_id=trace_id,
        object_type="document",
        object_id=object_id,
    )
```

- [ ] **Step 4: Implement transactional idempotency**

```python
@dataclass(frozen=True)
class IdempotencyDecision:
    record_id: uuid.UUID
    is_replay: bool
    status_code: int | None = None
    response_body: dict[str, Any] | None = None


def canonical_json(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


class IdempotencyService:
    def __init__(self, session: AsyncSession, actor_user_id: uuid.UUID) -> None:
        self.session = session
        self.actor_user_id = actor_user_id

    async def begin(self, scope: str, key: str, payload: Mapping[str, Any]) -> IdempotencyDecision:
        key_hash = sha256(key.encode()).hexdigest()
        payload_hash = sha256(canonical_json(payload)).hexdigest()
        record = await self._lock(self.actor_user_id, scope, key_hash)
        if record is not None:
            if record.payload_sha256 != payload_hash:
                raise ConflictError("Idempotency-Key was already used with a different payload.")
            return IdempotencyDecision(record.id, True, record.status_code, record.response_body)
        created = IdempotencyRecord(
            actor_user_id=self.actor_user_id,
            scope=scope,
            key_hash=key_hash,
            payload_sha256=payload_hash,
            state="started",
        )
        self.session.add(created)
        await self.session.flush()
        return IdempotencyDecision(created.id, False)
```

Hash the key before persistence, never store the raw key, encrypt or minimize replay bodies that contain patient data, and store no PHI in audit metadata. Define concurrent `started`, failed-response replay, and expiry behavior explicitly; commit the domain mutation, idempotency completion, and allowed/failed audit outcome atomically.

- [ ] **Step 5: Run permission, idempotency, and audit regression tests**

Run: `cd app/backend; python -m pytest tests/cdi_v2/test_capabilities.py tests/cdi_v2/test_idempotency.py tests/test_permissions.py tests/test_audit_2026_05.py -q`

Expected: PASS with denied capability attempts audited once.

- [ ] **Step 6: Commit**

```bash
git add app/backend/src/hospital_ai/services/capabilities.py app/backend/src/hospital_ai/services/idempotency.py app/backend/src/hospital_ai/schemas/idempotency.py app/backend/src/hospital_ai/core/errors.py app/backend/src/hospital_ai/services/permissions.py app/backend/tests/cdi_v2/test_capabilities.py app/backend/tests/cdi_v2/test_idempotency.py
git commit -m "backend: enforce CDI v2 write capabilities"
```

### Task 4: Implement Immutable R2 Upload Sessions and Atomic Finalization

**Files:**
- Modify: `app/backend/src/hospital_ai/services/storage.py:21-299`
- Create: `app/backend/src/hospital_ai/services/upload_sessions.py`
- Create: `app/backend/src/hospital_ai/api/routes/document_uploads.py`
- Create: `app/backend/src/hospital_ai/schemas/document_uploads.py`
- Modify: `app/backend/src/hospital_ai/api/router.py:34`
- Test: `app/backend/tests/cdi_v2/test_upload_sessions.py`
- Test: `app/backend/tests/cdi_v2/test_upload_api.py`
- Modify: `app/backend/tests/test_r2_storage.py`
- Modify: `app/backend/tests/test_storage_api_integration.py`

**Interfaces:**
- Produces: `POST /api/v1/documents/upload-sessions` and `POST /api/v1/documents/{document_id}/uploads/{upload_id}/finalize`.
- Produces: `StorageObjectHead(key, byte_size, etag, content_type)` and `StorageService.create_presigned_put`, `head_object`, `read_stream`, `delete_object`.
- Object key: `source/{patient_id}/{document_id}/{source_sha256}/original.<ext>`; duplicate key is HTTP 409.
- Finalization checks: HEAD, expected bytes, application SHA-256, magic-byte MIME, malware result, actor, and one atomic document/source pointer transaction.

- [ ] **Step 1: Write failing upload state-machine tests**

```python
async def test_unverified_upload_cannot_be_finalized_or_queued(session, r2_client) -> None:
    created = await UploadSessionService(session, r2_client).create(
        actor=records_user,
        patient_id=patient_id,
        filename="scan.pdf",
        expected_size=12,
        expected_sha256="a" * 64,
        claimed_mime_type="application/pdf",
        idempotency_key="upload-1",
    )
    r2_client.head_object.return_value = {"ContentLength": 11, "ETag": '"etag"'}
    with pytest.raises(ValidationAppError):
        await UploadSessionService(session, r2_client).finalize(created.document_id, created.upload_id)
    assert (await session.get(DocumentUpload, created.upload_id)).state == "rejected"


async def test_duplicate_immutable_key_is_a_conflict(session, r2_client) -> None:
    r2_client.head_object.return_value = {
        "ContentLength": 12,
        "ETag": '"existing"',
        "ContentType": "application/pdf",
    }
    with pytest.raises(ConflictError):
        await create_upload_session(session, request)


def test_presigned_put_requires_conditional_create(r2_storage) -> None:
    result = r2_storage.create_presigned_put(
        key="source/patient/document/hash/original.pdf",
        content_type="application/pdf",
        expires_seconds=300,
    )
    assert result.required_headers == {
        "Content-Type": "application/pdf",
        "If-None-Match": "*",
    }
```

- [ ] **Step 2: Run upload tests and verify RED**

Run: `cd app/backend; python -m pytest tests/cdi_v2/test_upload_sessions.py tests/cdi_v2/test_upload_api.py -q`

Expected: FAIL because upload-session services/routes are absent.

- [ ] **Step 3: Extend storage without exposing credentials**

```python
@dataclass(frozen=True)
class StorageObjectHead:
    key: str
    byte_size: int
    etag: str
    content_type: str | None


@dataclass(frozen=True)
class PresignedPut:
    url: str
    required_headers: dict[str, str]


def create_presigned_put(self, *, key: str, content_type: str, expires_seconds: int) -> PresignedPut:
    url = self.client.generate_presigned_url(
        "put_object",
        Params={"Bucket": self.bucket, "Key": key, "ContentType": content_type},
        ExpiresIn=expires_seconds,
    )
    return PresignedPut(
        url=url,
        required_headers={"Content-Type": content_type, "If-None-Match": "*"},
    )


def head_object(self, key: str) -> StorageObjectHead:
    row = self.client.head_object(Bucket=self.bucket, Key=key)
    return StorageObjectHead(key, int(row["ContentLength"]), str(row["ETag"]), row.get("ContentType"))
```

Keep `LocalStorageService` behavior-equivalent for tests, with unique paths and atomic `open(..., "xb")` semantics.

- [ ] **Step 4: Implement finalization as one locked transaction**

```python
async def finalize(self, *, document_id: uuid.UUID, upload_id: uuid.UUID, actor: User) -> UploadFinalizeResult:
    upload = await self._lock_upload(document_id, upload_id)
    if upload.state == "finalized":
        return UploadFinalizeResult.from_row(upload)
    head = await asyncio.to_thread(self.storage.head_object, upload.object_key)
    actual = await asyncio.to_thread(hash_stream, self.storage.read_stream(upload.object_key))
    mime = sniff_magic_mime(actual.prefix)
    malware = await self.scanner.scan(actual.temp_path)
    decision = verify_upload(upload, head, actual, mime, malware)
    upload.apply_verification(decision)
    if decision.state != "verified":
        await self._audit_and_commit(upload, actor, decision)
        raise ValidationAppError(decision.public_reason)
    document = await self._lock_document(document_id)
    upload.state = "finalized"
    document.finalized_upload_id = upload.id
    document.storage_uri = f"r2://{upload.object_key}"
    document.status = "uploaded"
    await self._record_finalization(document, upload, actor)
    await self.session.commit()
    return UploadFinalizeResult.from_row(upload)
```

- [ ] **Step 5: Add API headers/status codes and idempotent replay**

```python
@router.post("/upload-sessions", response_model=UploadSessionRead, status_code=201)
async def create_upload_session(
    payload: UploadSessionCreate,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> UploadSessionRead:
    return await UploadSessionService.from_request(session, request).create(
        actor=current_user, payload=payload, idempotency_key=idempotency_key
    )
```

- [ ] **Step 6: Run storage and API integration tests**

Run: `cd app/backend; python -m pytest tests/cdi_v2/test_upload_sessions.py tests/cdi_v2/test_upload_api.py tests/test_r2_storage.py tests/test_storage_contracts.py tests/test_storage_api_integration.py -q`

Expected: PASS; wrong size/hash/MIME, positive malware result, duplicate key, and unfinalized upload never enqueue OCR.

- [ ] **Step 7: Commit**

```bash
git add app/backend/src/hospital_ai/services/storage.py app/backend/src/hospital_ai/services/upload_sessions.py app/backend/src/hospital_ai/api/routes/document_uploads.py app/backend/src/hospital_ai/schemas/document_uploads.py app/backend/src/hospital_ai/api/router.py app/backend/tests/cdi_v2/test_upload_sessions.py app/backend/tests/cdi_v2/test_upload_api.py app/backend/tests/test_r2_storage.py app/backend/tests/test_storage_api_integration.py
git commit -m "backend: finalize immutable R2 uploads"
```

### Task 5: Implement Draft Save, Submit, Approval, Rejection, and Restore

**Files:**
- Create: `app/backend/src/hospital_ai/services/revisions.py`
- Create: `app/backend/src/hospital_ai/api/routes/document_revisions.py`
- Modify: `app/backend/src/hospital_ai/schemas/document_revisions.py`
- Modify: `app/backend/src/hospital_ai/api/router.py:34`
- Test: `app/backend/tests/cdi_v2/test_revision_service.py`
- Test: `app/backend/tests/cdi_v2/test_revision_api.py`

**Interfaces:**
- `RevisionService.save_page(document_id, page_number, command) -> DraftMutationResult` creates one immutable page revision and conditionally updates the draft head.
- `RevisionService.submit(document_id, command) -> RevisionSetResult` freezes one page revision per page.
- `RevisionService.approve(revision_set_id, command) -> GenerationAccepted` advances `approved_revision_set_id`, marks the set approved, and creates one `building` generation without changing the active generation.
- Reject mutates only `submitted → rejected`; restore creates a new `restored` child revision and draft selection.
- List/detail APIs work before an active generation exists and return `ETag: <lock_version>` for the current draft.

- [ ] **Step 1: Write failing immutability and optimistic-concurrency tests**

```python
async def test_stale_draft_save_returns_conflict_without_revision(session, seeded_document) -> None:
    service = RevisionService(session)
    first = await service.save_page(
        seeded_document.id,
        1,
        SavePageCommand(text="first", parent_revision_id=machine_id, lock_version=1, actor_id=doctor_id),
    )
    with pytest.raises(ConflictError):
        await service.save_page(
            seeded_document.id,
            1,
            SavePageCommand(text="stale", parent_revision_id=machine_id, lock_version=1, actor_id=records_id),
        )
    rows = list(await session.scalars(select(DocumentPageRevision).where(
        DocumentPageRevision.document_id == seeded_document.id,
        DocumentPageRevision.revision_type == "human_edit",
    )))
    assert [row.id for row in rows] == [first.page_revision_id]


async def test_production_editor_cannot_approve_own_submission(session, submitted_set) -> None:
    with pytest.raises(ConflictError):
        await RevisionService(session).approve(
            submitted_set.id,
            ApproveRevisionCommand(actor_id=submitted_set.created_by_user_id, demo_mode=False),
        )
```

- [ ] **Step 2: Run revision tests and verify RED**

Run: `cd app/backend; python -m pytest tests/cdi_v2/test_revision_service.py tests/cdi_v2/test_revision_api.py -q`

Expected: FAIL because `RevisionService` and V2 revision routes are absent.

- [ ] **Step 3: Implement immutable save with lock compare-and-swap**

```python
@dataclass(frozen=True)
class SavePageCommand:
    text: str
    parent_revision_id: uuid.UUID
    lock_version: int
    actor_id: uuid.UUID
    edit_reason: str


async def save_page(
    self, document_id: uuid.UUID, page_number: int, command: SavePageCommand
) -> DraftMutationResult:
    head = await self._lock_draft_head(document_id)
    if head.lock_version != command.lock_version:
        raise ConflictError("Draft changed; compare the latest revision before retrying.")
    parent = await self._require_selected_parent(document_id, page_number, command.parent_revision_id, head)
    content_sha256 = sha256(command.text.encode("utf-8")).hexdigest()
    revision = DocumentPageRevision(
        document_id=document_id,
        page_number=page_number,
        parent_revision_id=parent.id,
        extraction_run_id=parent.extraction_run_id,
        revision_number=await self._next_page_revision_number(document_id, page_number),
        revision_type="human_edit",
        raw_text_snapshot=parent.raw_text_snapshot,
        corrected_text=command.text,
        confidence=parent.confidence,
        status="human_draft",
        created_by_user_id=command.actor_id,
        edit_reason=command.edit_reason,
        content_sha256=content_sha256,
        version=1,
    )
    self.session.add(revision)
    await self.session.flush()
    head.selected_pages = {**head.selected_pages, str(page_number): str(revision.id)}
    head.lock_version += 1
    head.updated_by_user_id = command.actor_id
    await self._mark_geometry_after_edit(parent.id, revision.id, command.text)
    await self._append_event(document_id, command.actor_id, "page_saved", [revision.id])
    return DraftMutationResult(revision.id, head.lock_version)
```

- [ ] **Step 4: Implement frozen submit and approval without serving-pointer movement**

```python
async def approve(
    self, revision_set_id: uuid.UUID, command: ApproveRevisionCommand
) -> GenerationAccepted:
    revision_set = await self._lock_submitted_set(revision_set_id)
    document = await self._lock_document(revision_set.document_id)
    if not self_approval_allowed(document, revision_set.created_by_user_id, command):
        if revision_set.created_by_user_id == command.actor_id:
            raise ConflictError("The editor cannot approve this production revision set.")
    revision_set.status = "approved"
    revision_set.approved_by_user_id = command.actor_id
    revision_set.approved_at = utcnow()
    document.approved_revision_set_id = revision_set.id
    generation = DocumentIndexGeneration(
        document_id=document.id,
        revision_set_id=revision_set.id,
        state="building",
        revision_set_sha256=await self._revision_set_hash(revision_set.id),
    )
    self.session.add(generation)
    await self._append_event(document.id, command.actor_id, "revision_set_approved", [])
    await self.session.commit()
    return GenerationAccepted(generation.id, "building")
```

Submit verifies that the draft contains exactly one selected revision for every source page; page-level statuses remain independent. Approval enqueues `generation_jobs.build_generation_job` only after commit.

- [ ] **Step 5: Add exact routes, headers, and status codes**

```python
@router.patch("/{document_id}/draft/pages/{page_number}", response_model=DraftPageRead, status_code=201)
async def save_draft_page(
    document_id: uuid.UUID,
    page_number: int,
    payload: DraftPageWrite,
    if_match: int = Header(..., alias="If-Match"),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DraftPageRead:
    document = await get_document_or_404(session, document_id)
    await CapabilityService(session).require(
        user=current_user,
        patient_id=document.patient_id,
        capability="document_revision.edit",
        action="document_revision.page.save",
        trace_id=new_trace_id(),
        object_id=document_id,
    )
    return await revision_endpoint_service(session).save_page(
        document_id, page_number, payload, if_match, idempotency_key, current_user
    )
```

Implement the exact paths and `201/202/200/403/409/422` meanings from spec section 12.1 for revision-set list/detail, submit, approve, reject, and restore. Restore creates a new draft child and returns `201`; it does not auto-approve real data or queue a generation. Generation retry and rollback are owned by Task 7.

- [ ] **Step 6: Run revision API, permission, and audit tests**

Run: `cd app/backend; python -m pytest tests/cdi_v2/test_revision_service.py tests/cdi_v2/test_revision_api.py tests/api/test_documents.py tests/test_permissions.py -q`

Expected: PASS; every allowed, denied, failed, and replayed write has exactly one non-PHI audit outcome.

- [ ] **Step 7: Commit**

```bash
git add app/backend/src/hospital_ai/services/revisions.py app/backend/src/hospital_ai/api/routes/document_revisions.py app/backend/src/hospital_ai/schemas/document_revisions.py app/backend/src/hospital_ai/api/router.py app/backend/tests/cdi_v2/test_revision_service.py app/backend/tests/cdi_v2/test_revision_api.py
git commit -m "backend: add immutable OCR revision workflow"
```

### Task 6: Split Extraction from Indexing and Add Adaptive OCR Geometry

**Files:**
- Modify: `app/backend/src/hospital_ai/services/ocr.py:9-123`
- Create: `app/backend/src/hospital_ai/services/ocr_routing.py`
- Create: `app/backend/src/hospital_ai/workers/ocr_models.py`
- Create: `app/backend/src/hospital_ai/workers/extraction_jobs.py`
- Modify: `app/backend/src/hospital_ai/workers/jobs.py:18-184`
- Modify: `app/backend/src/hospital_ai/workers/pipeline.py:13-22`
- Modify: `app/backend/src/hospital_ai/services/loaders/composite.py:18-76`
- Modify: `app/backend/src/hospital_ai/core/config.py`
- Modify: `app/backend/pyproject.toml`
- Test: `app/backend/tests/cdi_v2/test_ocr_routing.py`
- Test: `app/backend/tests/cdi_v2/test_extraction_worker.py`
- Modify: `app/backend/tests/test_ocr_service.py`
- Modify: `app/backend/tests/workers/test_documents_pipeline.py`

**Interfaces:**
- Produces: `PagePreflight(native_credible, handwriting_probability, mixed_regions)` and routes `native | paddle_printed | vietocr_handwritten | trocr_handwritten | mixed`.
- Produces: `OcrPageResult(page_number, raw_text, confidence, route, blocks, latency_ms, peak_rss_mb)` with block/line/span polygons and offsets.
- `extraction_jobs.extract_document` is the focused entrypoint: finalized source → extraction run → machine page revisions/geometry → draft head → `review_required`; it creates no active chunks, embeddings, graph rows, or ready status.
- `jobs.process_document` and `pipeline.process_document_pipeline` remain compatibility façades that delegate to `extract_document` while old call sites are cut over. `CompositeLoader` uses the same rich OCR result contract and cannot call the removed scalar fallback signature.

- [ ] **Step 1: Write failing routing, geometry, and extraction-boundary tests**

```python
def test_router_selects_handwriting_only_above_qualified_threshold() -> None:
    decision = OcrRouter(handwriting_threshold=0.72).route(
        PagePreflight(native_credible=False, handwriting_probability=0.81, mixed_regions=())
    )
    assert decision.engine_family == "vietocr_handwritten"
    assert decision.confidence == pytest.approx(0.81)


async def test_extraction_creates_machine_revisions_but_no_chunks(session, finalized_document, settings) -> None:
    await extract_document(session, finalized_document.id, settings)
    revisions = list(await session.scalars(select(DocumentPageRevision)))
    chunks = list(await session.scalars(select(DocumentChunk)))
    assert revisions and all(row.revision_type == "machine_ocr" for row in revisions)
    assert chunks == []
    assert (await session.get(Document, finalized_document.id)).status == "review_required"
```

- [ ] **Step 2: Run OCR tests and verify RED**

Run: `cd app/backend; python -m pytest tests/cdi_v2/test_ocr_routing.py tests/cdi_v2/test_extraction_worker.py -q`

Expected: FAIL because routing/geometry contracts do not exist and the current worker creates chunks immediately.

- [ ] **Step 3: Introduce rich immutable OCR result types**

```python
@dataclass(frozen=True)
class OcrSpanResult:
    text: str
    start_offset: int
    end_offset: int
    polygon: tuple[tuple[float, float], ...]
    confidence: float
    reading_order: int
    engine_family: str
    engine_model: str
    engine_revision: str


@dataclass(frozen=True)
class OcrPageResult:
    page_number: int
    raw_text: str
    confidence: float
    route: str
    spans: tuple[OcrSpanResult, ...]
    latency_ms: int
    peak_rss_mb: int
```

Native extraction and PaddleOCR adapters populate the same result contract. Mixed pages use detector regions and reconstruct reading order before offsets are assigned.

- [ ] **Step 4: Enforce pinned model artifacts and 4 GB controls**

```python
@asynccontextmanager
async def acquire_model(self, route: str) -> AsyncIterator[Recognizer]:
    async with self._single_worker:
        artifact = self.registry.require_approved(route)
        verify_sha256(artifact.path, artifact.sha256)
        try:
            model = await self._lazy_load(artifact)
            yield model
        except MemoryError as exc:
            await self.telemetry.record_oom(route, artifact.revision, current_rss_mb())
            await self.unload(route)
            raise OcrResourceError("OCR model exceeded the configured memory budget.") from exc
        finally:
            self._schedule_idle_unload(route)
```

Add optional dependency groups for the pinned VietOCR/TrOCR runtime selected by qualification; weights remain outside Git and runtime never pulls `latest`.

- [ ] **Step 5: Implement extraction-only entrypoint and compatibility façades**

```python
async def extract_document(session: AsyncSession, document_id: uuid.UUID, settings: Settings) -> None:
    document = await require_finalized_document_for_extraction(session, document_id)
    run = await extraction_runs.start(session, document, settings)
    try:
        pages = await ocr_pipeline.extract(document, run, settings)
        await revision_ingest.persist_machine_drafts(session, document, run, pages)
        document.status = "review_required"
        await processing_events.complete_extraction(session, document.id, run.id, len(pages))
        await session.commit()
    except PageExtractionError as exc:
        await extraction_runs.fail_pagewise(session, document, run, exc)
        await session.commit()
```

Preserve successful pages, mark unresolved pages for review, record explicit route/model/OOM data, and never claim `ready` without an active generation. Make `jobs.process_document`, `process_document_job`, and `pipeline.process_document_pipeline` delegate to this function. Update or retire `CompositeLoader`'s outdated OCR fallback so both native and OCR paths return `OcrPageResult` with geometry.

- [ ] **Step 6: Run OCR, extraction, R2-worker, and old-index-preservation tests**

Run: `cd app/backend; python -m pytest tests/cdi_v2/test_ocr_routing.py tests/cdi_v2/test_extraction_worker.py tests/test_ocr_service.py tests/test_r2_worker_integration.py tests/workers/test_documents_pipeline.py -q`

Expected: PASS with one-worker concurrency and no serving-row deletion.

- [ ] **Step 7: Commit**

```bash
git add app/backend/src/hospital_ai/services/ocr.py app/backend/src/hospital_ai/services/ocr_routing.py app/backend/src/hospital_ai/services/loaders/composite.py app/backend/src/hospital_ai/workers/ocr_models.py app/backend/src/hospital_ai/workers/extraction_jobs.py app/backend/src/hospital_ai/workers/jobs.py app/backend/src/hospital_ai/workers/pipeline.py app/backend/src/hospital_ai/core/config.py app/backend/pyproject.toml app/backend/tests/cdi_v2/test_ocr_routing.py app/backend/tests/cdi_v2/test_extraction_worker.py app/backend/tests/test_ocr_service.py app/backend/tests/workers/test_documents_pipeline.py
git commit -m "backend: create review-gated OCR extraction"
```

### Task 7: Build, Activate, Retry, and Roll Back Index Generations

**Files:**
- Create: `app/backend/src/hospital_ai/services/generations.py`
- Create: `app/backend/src/hospital_ai/workers/generation_jobs.py`
- Modify: `app/backend/src/hospital_ai/workers/queue.py`
- Modify: `app/backend/src/hospital_ai/workers/run_worker.py`
- Create: `app/backend/src/hospital_ai/api/routes/document_generations.py`
- Create: `app/backend/src/hospital_ai/schemas/document_generations.py`
- Modify: `app/backend/src/hospital_ai/api/router.py`
- Modify: `app/backend/src/hospital_ai/services/hms_sync.py:190-261`
- Modify: `app/backend/src/hospital_ai/services/hms_appointments.py:51-114`
- Test: `app/backend/tests/cdi_v2/test_generation_service.py`
- Test: `app/backend/tests/cdi_v2/test_generation_worker.py`
- Test: `app/backend/tests/cdi_v2/test_generation_api.py`
- Modify: `app/backend/tests/test_hms_sync.py`
- Modify: `app/backend/tests/test_hms_appointments.py`

**Interfaces:**
- `GenerationBuilder.build(generation_id) -> GenerationBuildResult` writes facts, chunks, embeddings, lexical vectors, graph provenance, and timeline rows tagged to one generation.
- `GenerationService.activate(generation_id, expected_active_generation_id) -> ActivationResult` atomically swaps the serving pointer and statuses.
- Retry creates a new `building` row with `retry_of_generation_id`; rollback reactivates a complete prior generation and its revision set without rebuild or deletion.
- Exact rollback contract: `POST /api/v1/documents/{document_id}/index-generations/{generation_id}/rollback`, `Idempotency-Key` required, capability `document_revision.restore`, and request `{expected_active_generation_id: UUID, reason: str}`. It returns `200` with both authority pointers and displaced/target states; stale pointer, self-target, foreign-document target, incomplete target, or missing retained rows returns `409`.

- [ ] **Step 1: Write failing activation/failure/rollback tests**

```python
async def test_failed_generation_b_keeps_generation_a_active(session, generation_a, generation_b) -> None:
    document = await session.get(Document, generation_a.document_id)
    document.active_index_generation_id = generation_a.id
    await GenerationService(session).fail(generation_b.id, "EMBEDDING_COUNT_MISMATCH")
    await session.refresh(document)
    assert document.active_index_generation_id == generation_a.id
    assert generation_a.state == "active"
    assert generation_b.state == "failed"


async def test_rollback_swaps_both_authority_pointers_atomically(session, generation_a, generation_b) -> None:
    result = await GenerationService(session).rollback(
        document_id=generation_b.document_id,
        target_generation_id=generation_a.id,
        actor_id=admin_id,
    )
    assert result.active_generation_id == generation_a.id
    assert result.approved_revision_set_id == generation_a.revision_set_id
    assert generation_b.state == "superseded"


async def test_rollback_api_rejects_stale_active_pointer(client, generation_a, generation_b, auth_headers) -> None:
    response = await client.post(
        f"/api/v1/documents/{generation_b.document_id}/index-generations/{generation_a.id}/rollback",
        headers={**auth_headers, "Idempotency-Key": "rollback-1"},
        json={"expected_active_generation_id": str(uuid.uuid4()), "reason": "Operational rollback"},
    )
    assert response.status_code == 409
```

- [ ] **Step 2: Run generation tests and verify RED**

Run: `cd app/backend; python -m pytest tests/cdi_v2/test_generation_service.py tests/cdi_v2/test_generation_worker.py -q`

Expected: FAIL because generation services/workers are absent.

- [ ] **Step 3: Implement stage-isolated generation building**

```python
GENERATION_STAGES = (
    "ocr_normalization",
    "facts",
    "chunks",
    "embeddings",
    "lexical_index",
    "graph",
    "timeline",
)


async def build(self, generation_id: uuid.UUID) -> GenerationBuildResult:
    generation = await self._lock_building_generation(generation_id)
    revision_set = await self.revisions.load_frozen_set(generation.revision_set_id)
    for stage in GENERATION_STAGES:
        output = await self.stage_runner.run(stage, generation, revision_set)
        await self._record_stage(generation.id, stage, output.sha256, output.row_count, "completed")
        await self.session.commit()
    generation.generation_sha256 = await self._generation_hash(generation.id)
    return await GenerationService(self.session).activate(
        generation.id, expected_active_generation_id=(await self._document(generation.document_id)).active_index_generation_id
    )
```

Stage failures mark only the building generation failed; never delete or update rows belonging to another generation.

- [ ] **Step 4: Implement compare-and-swap activation and pointer/state rollback**

```python
async def activate(
    self, generation_id: uuid.UUID, expected_active_generation_id: uuid.UUID | None
) -> ActivationResult:
    generation = await self._require_complete_build(generation_id)
    document = await self._lock_document(generation.document_id)
    if document.active_index_generation_id != expected_active_generation_id:
        raise ConflictError("Serving generation changed while this build was running.")
    previous = await self._generation_or_none(document.active_index_generation_id)
    document.active_index_generation_id = generation.id
    generation.state = "active"
    generation.activated_at = utcnow()
    if previous is not None:
        previous.state = "superseded"
        previous.superseded_at = utcnow()
        await self._supersede_displaced_revision_set(previous.revision_set_id, generation.revision_set_id)
    document.status = "ready"
    await self.session.commit()
    return ActivationResult(generation.id, generation.revision_set_id)
```

Rollback validates same document, complete stage set, intact frozen revision set, and retained derived rows before performing the symmetric transaction.

- [ ] **Step 5: Add exact retry and rollback routes**

```python
class GenerationRollbackRequest(BaseModel):
    expected_active_generation_id: uuid.UUID
    reason: constr(strip_whitespace=True, min_length=3, max_length=500)


class GenerationRollbackRead(BaseModel):
    document_id: uuid.UUID
    active_index_generation_id: uuid.UUID
    approved_revision_set_id: uuid.UUID
    displaced_generation_id: uuid.UUID
    target_generation_state: Literal["active"]
    displaced_generation_state: Literal["superseded"]
```

The rollback endpoint loads the document first, authorizes against `document.patient_id`, compares `expected_active_generation_id` while holding the document row lock, and records domain changes, idempotency result, and non-PHI audit outcome in one transaction. A same-key/same-payload replay returns the original `200` response. The retry endpoint is the spec path `POST /api/v1/documents/{document_id}/index-generations/{generation_id}/retry`; it returns `202` and always creates a distinct generation linked through `retry_of_generation_id`.

- [ ] **Step 6: Wire RQ build/retry jobs and cut every importer over to generations**

```python
def build_generation_job(generation_id: str) -> None:
    async def run() -> None:
        async with get_session_factory()() as session:
            await GenerationBuilder.from_settings(session, get_settings()).build(uuid.UUID(generation_id))
    asyncio.run(run())
```

Register build/retry queues in `queue.py` and `run_worker.py`. Replace direct `DocumentPage`/`DocumentChunk` deletion and scalar `index_generation` mutation in `hms_sync.py` and `hms_appointments.py` with synthetic source revision-set creation followed by `GenerationBuilder`; import failures preserve the prior active generation.

- [ ] **Step 7: Run worker, API, importer, stale-generation, retry, and rollback tests**

Run: `cd app/backend; python -m pytest tests/cdi_v2/test_generation_service.py tests/cdi_v2/test_generation_worker.py tests/cdi_v2/test_generation_api.py tests/test_hms_sync.py tests/test_hms_appointments.py tests/test_documents.py -q`

Expected: PASS; stale builders cannot overwrite a newer pointer and failed replacements produce actionable `ready_with_warnings` state.

- [ ] **Step 8: Commit**

```bash
git add app/backend/src/hospital_ai/services/generations.py app/backend/src/hospital_ai/workers/generation_jobs.py app/backend/src/hospital_ai/workers/queue.py app/backend/src/hospital_ai/workers/run_worker.py app/backend/src/hospital_ai/api/routes/document_generations.py app/backend/src/hospital_ai/schemas/document_generations.py app/backend/src/hospital_ai/api/router.py app/backend/src/hospital_ai/services/hms_sync.py app/backend/src/hospital_ai/services/hms_appointments.py app/backend/tests/cdi_v2/test_generation_service.py app/backend/tests/cdi_v2/test_generation_worker.py app/backend/tests/cdi_v2/test_generation_api.py app/backend/tests/test_hms_sync.py app/backend/tests/test_hms_appointments.py
git commit -m "backend: activate immutable index generations"
```

### Task 8: Backfill Legacy Documents and Prove Compatibility Parity

**Files:**
- Create: `app/backend/src/hospital_ai/migrations/__init__.py`
- Create: `app/backend/src/hospital_ai/migrations/cdi_v2_backfill.py`
- Create: `app/backend/scripts/backfill_cdi_v2.py`
- Create: `app/backend/tests/cdi_v2/test_backfill.py`
- Create: `app/backend/tests/cdi_v2/test_legacy_parity.py`
- Modify: `app/backend/src/hospital_ai/core/config.py`

**Interfaces:**
- Produces resumable phases: `machine_revisions`, `draft_heads`, `submitted_sets`, `legacy_generations`, `parity`.
- Real documents are never auto-approved. Only explicitly synthetic/demo documents satisfying policy may receive approved revision sets and active legacy generations.
- Legacy chunks/graph rows attach to a legacy generation only after source SHA, document→patient, page→document, and chunk→page lineage verification.
- Feature flags: `cdi_v2_dual_read`, `cdi_v2_active_generation_reads`, `cdi_v2_authoring_enabled` default false until evidence gates pass.

- [ ] **Step 1: Write failing resumability and real-data safety tests**

```python
async def test_backfill_is_resumable_and_does_not_autoapprove_real_data(session, legacy_real_document) -> None:
    runner = CdiV2Backfill(session, policy=BackfillPolicy(autoapprove_synthetic=True))
    first = await runner.run_document(legacy_real_document.id)
    second = await runner.run_document(legacy_real_document.id)
    assert first.machine_revision_ids == second.machine_revision_ids
    document = await session.get(Document, legacy_real_document.id)
    assert document.approved_revision_set_id is None
    assert document.active_index_generation_id is None


async def test_legacy_generation_rejects_wrong_patient_chunk(session, legacy_document, wrong_patient_chunk) -> None:
    result = await CdiV2Backfill(session, BackfillPolicy()).verify_legacy_lineage(legacy_document.id)
    assert result.passed is False
    assert "wrong_patient_chunk" in result.failure_codes
```

- [ ] **Step 2: Run backfill tests and verify RED**

Run: `cd app/backend; python -m pytest tests/cdi_v2/test_backfill.py tests/cdi_v2/test_legacy_parity.py -q`

Expected: FAIL because backfill code and compatibility flags do not exist.

- [ ] **Step 3: Implement idempotent per-document backfill**

```python
async def run_document(self, document_id: uuid.UUID) -> BackfillResult:
    document = await self._lock_document(document_id)
    page_revisions = await self._machine_v1_from_document_pages(document)
    head = await self._upsert_draft_head(document, page_revisions)
    submitted = await self._upsert_submitted_revision_set(document, head)
    generation = None
    if self.policy.may_autoapprove(document):
        lineage = await self.verify_legacy_lineage(document.id)
        if not lineage.passed:
            raise BackfillBlocked(lineage.failure_codes)
        generation = await self._attach_verified_legacy_generation(document, submitted)
    await self._record_checkpoint(document.id, "complete")
    await self.session.commit()
    return BackfillResult.from_rows(page_revisions, head, submitted, generation)
```

- [ ] **Step 4: Add dry-run/apply/parity CLI with machine-readable output**

```python
parser.add_argument("--mode", choices=("dry-run", "apply", "parity"), required=True)
parser.add_argument("--document-id", action="append", default=[])
parser.add_argument("--output", type=Path, required=True)

exit_code = asyncio.run(run_backfill(args))
raise SystemExit(exit_code)
```

Parity output includes document IDs, source/revision/generation hashes, citation locators, lexical/vector result IDs, graph source IDs, wrong-patient count, superseded-generation count, and run Git SHA. It contains no PHI.

- [ ] **Step 5: Run synthetic parity and assert feature flags remain off on failure**

Run: `cd app/backend; python scripts/backfill_cdi_v2.py --mode parity --output evaluation-artifacts/cdi-v2/backfill-parity.json`

Expected: exit `0` only when legacy synthetic citation/retrieval parity holds and both wrong-patient and superseded-generation counts are zero.

- [ ] **Step 6: Run backfill and migration tests**

Run: `cd app/backend; python -m pytest tests/cdi_v2/test_backfill.py tests/cdi_v2/test_legacy_parity.py tests/test_migrations.py -q`

Expected: PASS; rerunning the backfill creates no duplicate revisions, sets, generations, or audit events.

- [ ] **Step 7: Commit**

```bash
git add app/backend/src/hospital_ai/migrations app/backend/scripts/backfill_cdi_v2.py app/backend/tests/cdi_v2/test_backfill.py app/backend/tests/cdi_v2/test_legacy_parity.py app/backend/src/hospital_ai/core/config.py
git commit -m "backend: backfill CDI v2 lineage safely"
```

### Task 9: Enforce One Active-Generation Predicate Across Lexical and Vector Retrieval

**Files:**
- Create: `app/backend/src/hospital_ai/services/evidence_scope.py`
- Modify: `app/backend/src/hospital_ai/services/retrieval.py:70-566`
- Modify: `app/backend/src/hospital_ai/services/bm25.py`
- Modify: `app/backend/src/hospital_ai/schemas/documents.py:54-63`
- Modify: `app/backend/src/hospital_ai/api/routes/documents.py:348-402`
- Test: `app/backend/tests/cdi_v2/test_evidence_scope.py`
- Test: `app/backend/tests/cdi_v2/test_revision_aware_retrieval.py`
- Modify: `app/backend/tests/test_retrieval_sql.py`
- Modify: `app/backend/tests/test_retrieval_postgres_integration.py`

**Interfaces:**
- Produces: `ActiveEvidenceScope.authorized_chunk_ids(user_id, patient_id, document_ids=None)` and reusable SQL predicates.
- `RetrievedChunk` gains `generation_id`, `revision_set_id`, `page_revision_id`, offsets, aligned polygons, approval state, retrieval method, and source hash.
- Filtering occurs before vector scoring, BM25 ranking, graph fusion, serialization, and prompt construction.

- [ ] **Step 1: Write failing adversarial retrieval tests**

```python
@pytest.mark.parametrize("mode", ["vector", "bm25", "hybrid"])
async def test_retrieval_excludes_wrong_patient_and_superseded_generation(
    session, seeded_generations, mode
) -> None:
    results = await RetrievalService(session).hybrid_search(
        user_id=doctor_id,
        patient_id=patient_a,
        query="metformin dose",
        query_embedding=[0.1] * 1024,
        top_k=20,
        mode=mode,
    )
    assert results
    assert all(row.patient_id == patient_a for row in results)
    assert all(row.generation_id == row.active_index_generation_id for row in results)
    assert all(row.approval_state == "approved" for row in results)
```

- [ ] **Step 2: Run retrieval tests and verify RED**

Run: `cd app/backend; python -m pytest tests/cdi_v2/test_evidence_scope.py tests/cdi_v2/test_revision_aware_retrieval.py -q`

Expected: FAIL because the current query uses document readiness rather than per-document active generation.

- [ ] **Step 3: Implement the shared authorized active-chunk subquery**

```python
def authorized_chunk_ids(
    self,
    *,
    user_id: uuid.UUID,
    patient_id: uuid.UUID,
    document_ids: Collection[uuid.UUID] | None = None,
):
    stmt = (
        select(DocumentChunk.id)
        .join(Document, Document.id == DocumentChunk.document_id)
        .join(DocumentIndexGeneration, DocumentIndexGeneration.id == DocumentChunk.generation_id)
        .join(DocumentRevisionSet, DocumentRevisionSet.id == DocumentChunk.revision_set_id)
        .join(DocumentPageRevision, DocumentPageRevision.id == DocumentChunk.page_revision_id)
        .where(
            Document.patient_id == patient_id,
            DocumentChunk.patient_id == patient_id,
            Document.active_index_generation_id == DocumentChunk.generation_id,
            DocumentIndexGeneration.state == "active",
            DocumentIndexGeneration.revision_set_id == DocumentChunk.revision_set_id,
            DocumentRevisionSet.status == "approved",
            Document.deleted_at.is_(None),
            DocumentChunk.deleted_at.is_(None),
            active_patient_permission_exists(
                user_id=user_id,
                patient_id=Document.patient_id,
                accepted_scopes=PATIENT_READ_SCOPES,
            ),
        )
    )
    if document_ids is not None:
        stmt = stmt.where(Document.id.in_(tuple(document_ids)))
    return stmt.scalar_subquery()
```

- [ ] **Step 4: Apply the same scope before every ranking implementation**

```python
allowed = ActiveEvidenceScope(self.session).authorized_chunk_ids(
    user_id=user_id, patient_id=patient_id, document_ids=document_ids
)
stmt = select(DocumentChunk).where(DocumentChunk.id.in_(allowed))
```

Use this base statement for PostgreSQL vector, portable cosine, PostgreSQL lexical, portable BM25, `get_chunks_by_ids`, graph candidate fusion, and document search. Keep score thresholds mode-aware.

- [ ] **Step 5: Return exact evidence lineage**

```python
metadata={
    **chunk.meta,
    "generation_id": str(chunk.generation_id),
    "revision_set_id": str(chunk.revision_set_id),
    "page_revision_id": str(chunk.page_revision_id),
    "start_offset": chunk.text_start_offset,
    "end_offset": chunk.text_end_offset,
    "bounding_boxes": aligned_boxes_only(chunk.bounding_boxes),
    "source_text_sha256": chunk.source_text_sha256,
    "approval_state": chunk.approval_state,
    "retrieval_method": method,
}
```

- [ ] **Step 6: Run SQL, PostgreSQL, and release-gate retrieval tests**

Run: `cd app/backend; python -m pytest tests/cdi_v2/test_evidence_scope.py tests/cdi_v2/test_revision_aware_retrieval.py tests/test_retrieval_sql.py tests/test_retrieval_postgres_integration.py tests/test_graph_rag_chat_release_gates.py -q`

Expected: PASS with zero wrong-patient and zero superseded-generation evidence.

- [ ] **Step 7: Commit**

```bash
git add app/backend/src/hospital_ai/services/evidence_scope.py app/backend/src/hospital_ai/services/retrieval.py app/backend/src/hospital_ai/services/bm25.py app/backend/src/hospital_ai/schemas/documents.py app/backend/src/hospital_ai/api/routes/documents.py app/backend/tests/cdi_v2/test_evidence_scope.py app/backend/tests/cdi_v2/test_revision_aware_retrieval.py app/backend/tests/test_retrieval_sql.py app/backend/tests/test_retrieval_postgres_integration.py
git commit -m "backend: scope retrieval to active generations"
```

### Task 10: Migrate Graph Data to Canonical Entities, Assertions, Mentions, and Evidence

**Files:**
- Create: `app/backend/src/hospital_ai/db/clinical_graph.py`
- Create: `app/backend/alembic/versions/cdi_v2_0002_add_graph_provenance_schema.py`
- Create: `app/backend/src/hospital_ai/services/graph_index.py`
- Modify: `app/backend/src/hospital_ai/services/graph_rag.py:40-304`
- Modify: `app/backend/src/hospital_ai/workers/generation_jobs.py`
- Modify: `app/backend/src/hospital_ai/workers/cdss.py`
- Modify: `app/backend/src/hospital_ai/services/drug_check.py`
- Test: `app/backend/tests/cdi_v2/test_graph_migration.py`
- Test: `app/backend/tests/cdi_v2/test_graph_index.py`
- Modify: `app/backend/tests/test_graph_rag_integration.py`

**Interfaces:**
- Migration revision is exactly `cdi_v2_0002` with `down_revision = "cdi_v2_0001"`; it preserves the old tables as `legacy_graph_entities` and `legacy_graph_relations` until parity and rollback windows close.
- Canonical identity: `GraphEntity(patient_id, entity_type, normalized_label)`; no single source pointer.
- Source lineage: `GraphMention(... generation_id, document_id, revision_set_id, page_revision_id, chunk_id, offsets, polygon, alignment_status ...)`.
- Canonical relation: `GraphRelationAssertion(patient_id, subject_entity_id, object_entity_id, relation_type, normalized_value, ...)`.
- Per-source relation lineage: `GraphRelationEvidence(... generation_id, evidence_locator, independent_source_identity ...)`.
- `GraphIndexService.index_chunk(generation_id, chunk, extraction) -> GraphIndexResult` upserts canonical records and appends source records without deleting another generation.

- [ ] **Step 1: Write failing multi-source provenance tests**

```python
async def test_one_canonical_entity_keeps_independent_source_mentions(session, active_sources) -> None:
    service = GraphIndexService(session)
    await service.index_chunk(active_sources[0].generation_id, active_sources[0], metformin_extraction())
    await service.index_chunk(active_sources[1].generation_id, active_sources[1], metformin_extraction())
    entities = list(await session.scalars(select(GraphEntity)))
    mentions = list(await session.scalars(select(GraphMention).where(GraphMention.entity_id == entities[0].id)))
    assert len(entities) == 1
    assert {row.document_id for row in mentions} == {active_sources[0].document_id, active_sources[1].document_id}
    assert len({row.independent_source_identity for row in mentions}) == 2


async def test_cross_patient_relation_is_rejected(session, patient_a_entity, patient_b_entity) -> None:
    with pytest.raises(IntegrityError):
        await persist_assertion(session, patient_a_entity, patient_b_entity, "treated_by")
```

- [ ] **Step 2: Run graph schema/index tests and verify RED**

Run: `cd app/backend; python -m pytest tests/cdi_v2/test_graph_migration.py tests/cdi_v2/test_graph_index.py -q`

Expected: FAIL because current graph rows combine canonical identity with one source chunk.

- [ ] **Step 3: Add the graph provenance models and migration**

```python
revision = "cdi_v2_0002"
down_revision = "cdi_v2_0001"


class GraphEntity(TimestampMixin, Base):
    __tablename__ = "graph_entities"
    __table_args__ = (
        UniqueConstraint("patient_id", "entity_type", "normalized_label", name="uq_graph_entity_identity"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    normalized_label: Mapped[str] = mapped_column(String(255), nullable=False)
    lifecycle_status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")


class GraphMention(Base):
    __tablename__ = "graph_mentions"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("graph_entities.id"), nullable=False)
    generation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_index_generations.id"), nullable=False)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=False)
    revision_set_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_revision_sets.id"), nullable=False)
    page_revision_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_page_revisions.id"), nullable=False)
    chunk_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_chunks.id"), nullable=False)
    independent_source_identity: Mapped[str] = mapped_column(String(128), nullable=False)
```

Migration sequence: rename current `graph_entities`/`graph_relations` to `legacy_graph_entities`/`legacy_graph_relations`, create the four normative tables, verify/backfill only lineage-valid rows, and retain legacy tables through parity and rollback windows.

- [ ] **Step 4: Implement provenance-preserving canonical upsert**

```python
async def index_chunk(
    self,
    generation_id: uuid.UUID,
    chunk: DocumentChunk,
    extraction: GraphExtraction,
) -> GraphIndexResult:
    for item in extraction.entities:
        entity = await self._upsert_entity(chunk.patient_id, item.entity_type, item.normalized_label)
        self.session.add(GraphMention.from_extraction(entity, generation_id, chunk, item))
    for item in extraction.relations:
        assertion = await self._upsert_assertion(chunk.patient_id, item)
        self.session.add(GraphRelationEvidence.from_extraction(assertion, generation_id, chunk, item))
    await self.session.flush()
    return await self._result_for_chunk(generation_id, chunk.id)
```

- [ ] **Step 5: Keep offline extraction stable and switch runtime imports**

`ExtractedEntity`, `ExtractedRelation`, `extract_entities_and_relations_offline`, and deterministic fallback grammar remain available from `services/graph_rag.py`; storage/query responsibilities move to `graph_index.py` and Task 11's query service.

- [ ] **Step 6: Run migration, graph, CDSS, and drug-check regression tests**

Run: `cd app/backend; python -m pytest tests/cdi_v2/test_graph_migration.py tests/cdi_v2/test_graph_index.py tests/test_graph_rag_integration.py tests/test_graph_rag_chat_release_gates.py tests/test_drug_check.py -q`

Expected: PASS; canonicalization never erases source evidence and cross-patient links fail.

- [ ] **Step 7: Commit**

```bash
git add app/backend/src/hospital_ai/db/clinical_graph.py app/backend/alembic/versions/cdi_v2_0002_add_graph_provenance_schema.py app/backend/src/hospital_ai/services/graph_index.py app/backend/src/hospital_ai/services/graph_rag.py app/backend/src/hospital_ai/workers/generation_jobs.py app/backend/src/hospital_ai/workers/cdss.py app/backend/src/hospital_ai/services/drug_check.py app/backend/tests/cdi_v2/test_graph_migration.py app/backend/tests/cdi_v2/test_graph_index.py app/backend/tests/test_graph_rag_integration.py
git commit -m "backend: preserve Graph RAG source provenance"
```

### Task 11: Add Filtered Document Graph, Explanation, and Clinical Timeline APIs

**Files:**
- Create: `app/backend/src/hospital_ai/services/graph_query.py`
- Create: `app/backend/src/hospital_ai/services/clinical_timeline.py`
- Create: `app/backend/src/hospital_ai/api/routes/document_graph.py`
- Create: `app/backend/src/hospital_ai/schemas/document_graph.py`
- Modify: `app/backend/src/hospital_ai/api/router.py:46-48`
- Modify: `app/backend/src/hospital_ai/api/routes/graph.py:116-348`
- Modify: `app/backend/src/hospital_ai/api/routes/timeline.py:17-126`
- Test: `app/backend/tests/cdi_v2/test_graph_query.py`
- Test: `app/backend/tests/cdi_v2/test_document_graph_api.py`
- Test: `app/backend/tests/cdi_v2/test_clinical_timeline.py`

**Interfaces:**
- Produces `GET /api/v1/documents/{document_id}/graph` with node/edge/hop/type/relation/confidence/document/revision/date/layout/superseded filters and hard caps 200 nodes/500 edges.
- Produces `GET /api/v1/documents/{document_id}/timeline` with revision/date/type/superseded filters.
- Normal reads require active per-source evidence; `include_superseded=true` additionally requires `superseded_evidence.read` and labels results `audit_only`.
- Explanation paths carry evidence IDs; graph edges never replace source citations.

- [ ] **Step 1: Write failing filter and provenance tests**

```python
async def test_document_graph_filters_each_source_by_its_own_active_generation(client, graph_fixture) -> None:
    response = await client.get(
        f"/api/v1/documents/{graph_fixture.document_a}/graph?hop_depth=2&min_confidence=0.8",
        headers=doctor_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert all(item["generation_id"] == item["source_active_generation_id"] for item in body["mentions"])
    assert all(item["evidence_ids"] for item in body["assertions"])


async def test_superseded_graph_requires_capability(client, graph_fixture) -> None:
    response = await client.get(
        f"/api/v1/documents/{graph_fixture.document_a}/graph?include_superseded=true",
        headers=doctor_headers,
    )
    assert response.status_code == 403
```

- [ ] **Step 2: Run graph/timeline tests and verify RED**

Run: `cd app/backend; python -m pytest tests/cdi_v2/test_graph_query.py tests/cdi_v2/test_document_graph_api.py tests/cdi_v2/test_clinical_timeline.py -q`

Expected: FAIL because only `/graph/patients/{patient_id}` and a global activity timeline exist.

- [ ] **Step 3: Implement bounded graph filters and per-source scope**

```python
class GraphFilters(BaseModel):
    node_limit: Literal[25, 50, 100] = 50
    edge_limit: Literal[50, 100, 250] = 100
    hop_depth: int = Field(2, ge=1, le=3)
    entity_types: tuple[str, ...] = ()
    relation_types: tuple[str, ...] = ()
    min_confidence: float = Field(0.0, ge=0.0, le=1.0)
    document_scope: tuple[UUID, ...] = ()
    approved_revision_set_id: UUID | None = None
    date_from: date | None = None
    date_to: date | None = None
    layout: Literal["force", "timeline", "hierarchical"] = "force"
    include_superseded: bool = False
```

The query joins every mention/evidence row to `Document.active_index_generation_id` for that row's own `document_id` before canonical entities/assertions are selected.

- [ ] **Step 4: Derive timeline events with explicit conflicts**

```python
@dataclass(frozen=True)
class TimelineEventProjection:
    event_type: str
    clinical_date: date | None
    recorded_at: datetime
    evidence_ids: tuple[uuid.UUID, ...]
    confidence: float
    reviewer_state: str
    conflict_state: Literal["none", "date_conflict", "value_conflict"]
    supersession_lineage: tuple[uuid.UUID, ...]
```

Group equivalent facts only when normalized identity and value/date agree; otherwise emit separate events linked by `conflict_state`.

- [ ] **Step 5: Add document-scoped routes and preserve legacy patient/global routes**

```python
@router.get("/{document_id}/graph", response_model=DocumentGraphRead)
async def get_document_graph(document_id: UUID, filters: GraphFilters = Depends(), ...) -> DocumentGraphRead:
    document = await require_document_read(...)
    if filters.include_superseded:
        await CapabilityService(session).require(
            user=current_user,
            patient_id=document.patient_id,
            capability="superseded_evidence.read",
            action="document.graph.superseded.read",
            trace_id=trace_id,
            object_id=document.id,
        )
    return await GraphQueryService(session).document_graph(document, current_user, filters)
```

- [ ] **Step 6: Run graph endpoint, timeline, permission, and serialization tests**

Run: `cd app/backend; python -m pytest tests/cdi_v2/test_graph_query.py tests/cdi_v2/test_document_graph_api.py tests/cdi_v2/test_clinical_timeline.py tests/test_graph_endpoint.py tests/test_graph_rag_chat_release_gates.py -q`

Expected: PASS; wrong-patient/superseded rows are excluded before serialization.

- [ ] **Step 7: Commit**

```bash
git add app/backend/src/hospital_ai/services/graph_query.py app/backend/src/hospital_ai/services/clinical_timeline.py app/backend/src/hospital_ai/api/routes/document_graph.py app/backend/src/hospital_ai/schemas/document_graph.py app/backend/src/hospital_ai/api/router.py app/backend/src/hospital_ai/api/routes/graph.py app/backend/src/hospital_ai/api/routes/timeline.py app/backend/tests/cdi_v2/test_graph_query.py app/backend/tests/cdi_v2/test_document_graph_api.py app/backend/tests/cdi_v2/test_clinical_timeline.py
git commit -m "backend: expose filtered clinical graph and timeline"
```

### Task 12: Add Retrieval Planning and Claim-to-Evidence Validation

**Files:**
- Create: `app/backend/src/hospital_ai/services/query_planner.py`
- Create: `app/backend/src/hospital_ai/services/claim_validation.py`
- Create: `app/backend/src/hospital_ai/schemas/claim_validation.py`
- Modify: `app/backend/src/hospital_ai/services/chat.py`
- Modify: `app/backend/src/hospital_ai/services/chat_utils.py`
- Test: `app/backend/tests/cdi_v2/test_query_planner.py`
- Test: `app/backend/tests/cdi_v2/test_claim_validation.py`
- Modify: `app/backend/tests/test_chat_citations.py`

**Interfaces:**
- Planner strategies: exact value/code/date → lexical; narrative → hybrid; relation/interaction → graph+hybrid; temporal → temporal+graph+lexical; multi-document → hybrid+rerank; no evidence → refusal.
- `ClaimValidator.validate_sentence(sentence, authorized_evidence, context) -> SentenceValidation` checks attached evidence IDs, entities, dates, doses, units, values, and negation; deterministic contradiction failure blocks output.
- Every factual sentence persists one or more `ClaimValidationResult` rows. Auxiliary judge output is supplemental and cannot override deterministic failure.

- [ ] **Step 1: Write failing deterministic validation tests**

```python
@pytest.mark.parametrize(
    ("sentence", "evidence", "expected"),
    [
        ("Metformin dose is 500 mg [E1].", "Metformin 500 mg twice daily", True),
        ("Metformin dose is 5,000 mg [E1].", "Metformin 500 mg twice daily", False),
        ("The patient has no allergy [E1].", "Allergy: penicillin", False),
        ("HbA1c was 7.1% on 2026-08-01 [E1].", "HbA1c 7.1% collected 2026-08-01", True),
    ],
)
def test_numeric_unit_date_and_negation_validation(sentence, evidence, expected) -> None:
    result = ClaimValidator().validate_sentence(sentence, {"E1": evidence}, validation_context())
    assert result.passed is expected
```

- [ ] **Step 2: Run planner/validator tests and verify RED**

Run: `cd app/backend; python -m pytest tests/cdi_v2/test_query_planner.py tests/cdi_v2/test_claim_validation.py -q`

Expected: FAIL because current citation checks validate only evidence-ID membership.

- [ ] **Step 3: Implement deterministic strategy selection**

```python
def plan(self, question: str, scope: ChatScope) -> RetrievalPlan:
    features = classify_query(question)
    if features.no_patient_evidence:
        return RetrievalPlan(("refusal",), scope, requires_graph=False)
    if features.temporal:
        return RetrievalPlan(("temporal", "graph", "lexical"), scope, requires_graph=True)
    if features.relation_or_interaction:
        return RetrievalPlan(("graph", "hybrid"), scope, requires_graph=True)
    if features.exact_value_or_code:
        return RetrievalPlan(("lexical",), scope, requires_graph=False)
    if features.multi_document:
        return RetrievalPlan(("hybrid", "rerank"), scope, requires_graph=False)
    return RetrievalPlan(("hybrid",), scope, requires_graph=False)
```

- [ ] **Step 4: Implement claim validation and persistence**

```python
def validate_sentence(
    self,
    sentence: str,
    evidence_by_id: Mapping[str, EvidenceText],
    context: ValidationContext,
) -> SentenceValidation:
    claims = self.claim_parser.parse(sentence)
    results = tuple(self._validate_claim(claim, evidence_by_id, context) for claim in claims)
    passed = all(result.passed for result in results)
    return SentenceValidation(sentence=sentence, claims=results, passed=passed)


def _validate_claim(self, claim: Claim, evidence_by_id, context) -> ClaimResult:
    if not claim.evidence_ids or not set(claim.evidence_ids) <= set(evidence_by_id):
        return ClaimResult.failed(claim, "AUTHORIZED_EVIDENCE_REQUIRED")
    evidence = combine(evidence_by_id[eid] for eid in claim.evidence_ids)
    return deterministic_entailment(claim, evidence, strict_fields={"number", "unit", "date", "negation"})
```

- [ ] **Step 5: Run citation, safe-refusal, and usefulness tests**

Run: `cd app/backend; python -m pytest tests/cdi_v2/test_query_planner.py tests/cdi_v2/test_claim_validation.py tests/test_chat_citations.py tests/test_chat_endpoint.py -q`

Expected: PASS; supported facts remain useful and unsupported claims are regenerated or safely replaced.

- [ ] **Step 6: Commit**

```bash
git add app/backend/src/hospital_ai/services/query_planner.py app/backend/src/hospital_ai/services/claim_validation.py app/backend/src/hospital_ai/schemas/claim_validation.py app/backend/src/hospital_ai/services/chat.py app/backend/src/hospital_ai/services/chat_utils.py app/backend/tests/cdi_v2/test_query_planner.py app/backend/tests/cdi_v2/test_claim_validation.py app/backend/tests/test_chat_citations.py
git commit -m "backend: validate chat claims against evidence"
```

### Task 13: Stream Only Validated Sentences and Persist Interruptions

**Files:**
- Create: `app/backend/alembic/versions/cdi_v2_0003_add_validated_stream_state.py`
- Create: `app/backend/src/hospital_ai/services/validated_stream.py`
- Modify: `app/backend/src/hospital_ai/api/routes/chat_stream.py:693-1029`
- Modify: `app/backend/src/hospital_ai/schemas/chat.py`
- Modify: `app/backend/src/hospital_ai/db/models.py:335-367`
- Test: `app/backend/tests/cdi_v2/test_validated_stream.py`
- Test: `app/backend/tests/cdi_v2/test_validated_stream_migration.py`
- Modify: `app/backend/tests/test_chat_stream_endpoint.py`
- Modify: `app/backend/tests/test_graph_rag_chat_release_gates.py`

**Interfaces:**
- `ValidatedSentenceStreamer.events(token_stream, evidence, context) -> AsyncIterator[SseEvent]` buffers provider tokens privately until sentence validation passes.
- `token` payload: `{type, sequence, content, validation_mode: "sentence_buffered"}` with sequence starting at 1.
- Fixed success order; empty citations and graph explanation still emit. Disconnect persists partial validated text as `interrupted` plus last sequence and emits no more data.
- Migration `cdi_v2_0003` follows `cdi_v2_0002` and adds `ai_queries.validation_mode`, `ai_queries.last_emitted_sequence`, and the `interrupted` status allowance without rewriting historical answers.

- [ ] **Step 1: Write failing event-order and disconnect tests**

```python
async def test_sse_never_emits_unvalidated_provider_tokens() -> None:
    provider = async_tokens("Unsupported 5000 mg. Supported 500 mg [E1].")
    events = [event async for event in streamer(provider, evidence={"E1": "Dose 500 mg"})]
    tokens = [event for event in events if event.type == "token"]
    assert "5000" not in "".join(event.content for event in tokens)
    assert [event.sequence for event in tokens] == list(range(1, len(tokens) + 1))
    assert [event.type for event in events if event.type != "token"] == [
        "status", "metadata", "citations", "graph_explanation", "done"
    ]


async def test_disconnect_persists_interrupted_answer(session, disconnecting_request) -> None:
    await consume_stream(chat_stream_request(disconnecting_request))
    query = await latest_query(session)
    assert query.status == "interrupted"
    assert query.last_emitted_sequence >= 1


def test_validated_stream_migration_follows_graph_schema() -> None:
    module = load_revision("cdi_v2_0003_add_validated_stream_state.py")
    assert module.revision == "cdi_v2_0003"
    assert module.down_revision == "cdi_v2_0002"
```

- [ ] **Step 2: Run SSE tests and verify RED**

Run: `cd app/backend; python -m pytest tests/cdi_v2/test_validated_stream_migration.py tests/cdi_v2/test_validated_stream.py tests/test_chat_stream_endpoint.py -q`

Expected: FAIL because current grounded generation buffers a complete answer and token events lack sequence/validation mode.

- [ ] **Step 3: Add interruption persistence schema and the private sentence buffer**

Set `revision = "cdi_v2_0003"` and `down_revision = "cdi_v2_0002"`. Extend the SQLAlchemy/Pydantic state with `validation_mode: str | None`, `last_emitted_sequence: int = 0`, and query status `interrupted`; persist only validated emitted text, never the provider's private buffer.

```python
async def validated_chunks(
    self,
    provider_tokens: AsyncIterator[str],
    evidence: Mapping[str, EvidenceText],
    context: ValidationContext,
) -> AsyncIterator[ValidatedChunk]:
    buffer = ""
    sequence = 0
    async for raw_token in provider_tokens:
        buffer += raw_token
        complete, buffer = split_complete_sentences(buffer)
        for sentence in complete:
            validation = self.validator.validate_sentence(sentence, evidence, context)
            safe_sentence = sentence if validation.passed else await self.repair_or_refuse(sentence, validation)
            await self.persist_validation(validation, safe_sentence)
            for text in visual_chunks(safe_sentence):
                sequence += 1
                yield ValidatedChunk(sequence, text, "sentence_buffered")
    if buffer.strip():
        async for chunk in self._validate_final_fragment(buffer, sequence, evidence, context):
            yield chunk
```

- [ ] **Step 4: Emit the exact terminal contract and stop on disconnect**

```python
async def event_stream() -> AsyncIterator[str]:
    yield encode_sse(StatusEvent(stage="retrieving"))
    yield encode_sse(MetadataEvent(validation_mode="sentence_buffered", model=model_name))
    try:
        async for chunk in validated_stream.validated_chunks(provider_tokens, evidence, context):
            if await request.is_disconnected():
                await finalize_interrupted(query_id, chunk.sequence)
                return
            yield encode_sse(TokenEvent(sequence=chunk.sequence, content=chunk.content))
        yield encode_sse(CitationsEvent(data=citations))
        yield encode_sse(GraphExplanationEvent(data=graph_explanation))
        yield encode_sse(DoneEvent(query_id=query_id, persistence_status="completed"))
    except Exception:
        await finalize_failed(query_id)
        yield encode_sse(ErrorEvent(message="The validated stream could not be completed."))
```

- [ ] **Step 5: Run sync/SSE parity, guardrail, cancellation, and no-leak tests**

Run: `cd app/backend; python -m pytest tests/cdi_v2/test_validated_stream_migration.py tests/cdi_v2/test_validated_stream.py tests/test_chat_stream_endpoint.py tests/test_graph_rag_chat_release_gates.py tests/test_chat_endpoint.py -q`

Expected: PASS; no raw provider output appears in errors or token events.

- [ ] **Step 6: Commit**

```bash
git add app/backend/alembic/versions/cdi_v2_0003_add_validated_stream_state.py app/backend/src/hospital_ai/services/validated_stream.py app/backend/src/hospital_ai/api/routes/chat_stream.py app/backend/src/hospital_ai/schemas/chat.py app/backend/src/hospital_ai/db/models.py app/backend/tests/cdi_v2/test_validated_stream_migration.py app/backend/tests/cdi_v2/test_validated_stream.py app/backend/tests/test_chat_stream_endpoint.py app/backend/tests/test_graph_rag_chat_release_gates.py
git commit -m "backend: stream validated sentence chunks"
```

### Task 14: Add Typed Frontend Contracts for Uploads, Revisions, Graph, Timeline, and SSE

**Files:**
- Create: `app/frontend/src/lib/api/document-revisions.ts`
- Create: `app/frontend/src/lib/api/document-graph.ts`
- Create: `app/frontend/src/lib/api/document-timeline.ts`
- Create: `app/frontend/src/lib/idempotency.ts`
- Modify: `app/frontend/src/lib/api/documents.ts:3-211`
- Modify: `app/frontend/src/lib/stream-client.ts:13-209`
- Test: `app/frontend/src/lib/api/document-revisions.test.ts`
- Test: `app/frontend/src/lib/api/document-graph.test.ts`
- Test: `app/frontend/src/lib/api/document-timeline.test.ts`
- Modify: `app/frontend/src/lib/api/documents.test.ts`
- Modify: `app/frontend/src/lib/stream-client.test.ts`

**Interfaces:**
- Produces exact TypeScript types matching Pydantic responses from Tasks 4, 5, 7, 11, and 13, including distinct graph and timeline filter/response types.
- Write client calls accept explicit `{ idempotencyKey, lockVersion? }`; no component fabricates `version: 1`.
- SSE client rejects missing/duplicate/out-of-order sequence, captures graph explanation, and distinguishes completed/interrupted/error.

- [ ] **Step 1: Write failing API-header and SSE sequence tests**

```typescript
it("sends Idempotency-Key and If-Match on draft save", async () => {
  await saveDraftPage("doc-1", 2, payload, { idempotencyKey: "draft-1", lockVersion: 7 });
  expect(fetchMock).toHaveBeenCalledWith(
    expect.stringContaining("/documents/doc-1/draft/pages/2"),
    expect.objectContaining({
      method: "PATCH",
      headers: expect.objectContaining({ "Idempotency-Key": "draft-1", "If-Match": "7" }),
    }),
  );
});

it("rejects out-of-order validated chunks", async () => {
  mockSse([{ type: "token", sequence: 2, content: "bad", validation_mode: "sentence_buffered" }]);
  await expect(streamChat(baseUrl, null, body)).rejects.toThrow("Invalid SSE token sequence");
});
```

- [ ] **Step 2: Run frontend client tests and verify RED**

Run: `cd app/frontend; bun run test -- src/lib/api/document-revisions.test.ts src/lib/api/document-graph.test.ts src/lib/api/document-timeline.test.ts src/lib/stream-client.test.ts`

Expected: FAIL because V2 clients and sequence validation are absent.

- [ ] **Step 3: Define exact revision and generation DTOs**

```typescript
export interface RevisionSetRead {
  id: string;
  document_id: string;
  revision_number: number;
  status: "submitted" | "approved" | "rejected" | "superseded";
  created_by_user_id: string;
  created_at: string;
  submitted_at: string;
  approved_by_user_id: string | null;
  approved_at: string | null;
  generation: GenerationLineage | null;
  pages: PageRevisionRead[];
}

export interface PageRevisionRead {
  id: string;
  page_number: number;
  parent_revision_id: string | null;
  revision_number: number;
  revision_type: "machine_ocr" | "human_edit" | "restored";
  raw_text_snapshot: string;
  corrected_text: string | null;
  confidence: number | null;
  status: "machine_draft" | "human_draft" | "approved" | "rejected" | "superseded";
  content_sha256: string;
  created_by_user_id: string;
  created_at: string;
  geometry_alignment: "aligned" | "partially_aligned" | "stale";
}
```

- [ ] **Step 4: Centralize write headers and idempotency keys**

```typescript
export function mutationHeaders(options: {
  idempotencyKey: string;
  lockVersion?: number;
}): Record<string, string> {
  return {
    "Idempotency-Key": options.idempotencyKey,
    ...(options.lockVersion === undefined ? {} : { "If-Match": String(options.lockVersion) }),
  };
}

export function newIdempotencyKey(scope: string): string {
  return `${scope}:${crypto.randomUUID()}`;
}
```

Keep the same key for a user retry of the same payload; create a new key after payload changes or a generation retry is explicitly requested.

- [ ] **Step 5: Parse and validate the full SSE contract**

```typescript
case "token": {
  if (data.validation_mode !== "sentence_buffered" || data.sequence !== lastSequence + 1) {
    throw new Error("Invalid SSE token sequence");
  }
  lastSequence = data.sequence;
  result.answer += data.content;
  onEvent?.({ type: "token", sequence: data.sequence, content: data.content });
  break;
}
case "graph_explanation":
  result.graphExplanation = data.data;
  onEvent?.({ type: "graph_explanation", graphExplanation: data.data });
  break;
```

- [ ] **Step 6: Run unit, typecheck, and lint**

Run: `cd app/frontend; bun run test -- src/lib/api/document-revisions.test.ts src/lib/api/document-graph.test.ts src/lib/api/document-timeline.test.ts src/lib/api/documents.test.ts src/lib/stream-client.test.ts; bun run typecheck; bun run lint`

Expected: PASS with no `any` in the new V2 DTOs.

- [ ] **Step 7: Commit**

```bash
git add app/frontend/src/lib/api/document-revisions.ts app/frontend/src/lib/api/document-graph.ts app/frontend/src/lib/api/document-timeline.ts app/frontend/src/lib/idempotency.ts app/frontend/src/lib/api/documents.ts app/frontend/src/lib/stream-client.ts app/frontend/src/lib/api/document-revisions.test.ts app/frontend/src/lib/api/document-graph.test.ts app/frontend/src/lib/api/document-timeline.test.ts app/frontend/src/lib/api/documents.test.ts app/frontend/src/lib/stream-client.test.ts
git commit -m "frontend: add CDI v2 API contracts"
```

### Task 15: Replace Multipart Upload with the Direct Immutable R2 Flow

**Files:**
- Modify: `app/frontend/src/routes/_app.documents.upload.tsx`
- Create: `app/frontend/src/components/hms/document-upload/DocumentUploadFlow.tsx`
- Create: `app/frontend/src/components/hms/document-upload/UploadStatePanel.tsx`
- Modify: `app/frontend/src/lib/api/documents.ts`
- Modify: `app/frontend/src/lib/api/documents.test.ts`
- Test: `app/frontend/src/components/hms/document-upload/DocumentUploadFlow.test.tsx`

**Interfaces:**
- Browser flow is exactly create session `201` → conditional PUT to the returned short-lived URL → finalize `201 | 202`; the frontend never receives bucket credentials or constructs an object key.
- The PUT copies every server-returned required header, including `If-None-Match: *` and the bound `Content-Type`; HTTP `412` is rendered as immutable-key conflict and is never retried with overwrite semantics.
- UI states map to `pending_upload | uploaded_unverified | quarantined | verified | finalized | rejected`; only `finalized` transitions to OCR progress. Local files are cleared from component state after terminal success/cancel.

- [ ] **Step 1: Write failing direct-upload and failure-state tests**

```tsx
it("uploads directly with every server-required header before finalization", async () => {
  render(<DocumentUploadFlow patientId="patient-1" />);
  await user.upload(screen.getByLabelText("Clinical document"), syntheticPdf);
  await user.click(screen.getByRole("button", { name: "Upload document" }));
  expect(createUploadSession).toHaveBeenCalledTimes(1);
  expect(putPresignedObject).toHaveBeenCalledWith(
    expect.objectContaining({
      required_headers: { "Content-Type": "application/pdf", "If-None-Match": "*" },
    }),
    syntheticPdf,
    expect.any(Function),
  );
  expect(putPresignedObject.mock.invocationCallOrder[0]).toBeLessThan(finalizeUpload.mock.invocationCallOrder[0]);
});

it.each(["quarantined", "rejected"])("never presents %s as ready for OCR", async (state) => {
  finalizeUpload.mockResolvedValue({ ...finalizeResult, state });
  render(<DocumentUploadFlow patientId="patient-1" />);
  await completeUpload(user, syntheticPdf);
  expect(screen.queryByText("OCR started")).not.toBeInTheDocument();
  expect(screen.getByText(state === "quarantined" ? "Upload quarantined" : "Upload rejected")).toBeVisible();
});
```

- [ ] **Step 2: Run upload UI tests and verify RED**

Run: `cd app/frontend; bun run test -- src/components/hms/document-upload/DocumentUploadFlow.test.tsx src/lib/api/documents.test.ts`

Expected: FAIL because the current route submits multipart bytes to the backend and has no session/finalization state model.

- [ ] **Step 3: Implement typed session, PUT, and finalization clients**

```typescript
export function putPresignedObject(
  upload: UploadSessionRead,
  file: File,
  onProgress: (percent: number) => void,
): Promise<void> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("PUT", upload.upload_url, true);
    for (const [name, value] of Object.entries(upload.required_headers)) xhr.setRequestHeader(name, value);
    xhr.upload.onprogress = ({ loaded, total }) => total > 0 && onProgress(Math.round((loaded / total) * 100));
    xhr.onload = () => xhr.status >= 200 && xhr.status < 300
      ? resolve()
      : reject(new ApiError(xhr.status, xhr.status === 412 ? "Immutable object key already exists" : "Object upload failed"));
    xhr.onerror = () => reject(new ApiError(0, "Object upload failed"));
    xhr.send(file);
  });
}
```

Hash the local file with Web Crypto before creating the session, pass expected bytes/SHA-256/MIME in the request, retain the same idempotency key for a same-payload retry, and use a new key only after file metadata changes.

- [ ] **Step 4: Compose observable upload and verification states**

```tsx
const runUpload = async (file: File) => {
  setState({ kind: "creating_session" });
  const session = await createUploadSession(await uploadPayload(file), { idempotencyKey: key.current });
  setState({ kind: "uploading", percent: 0 });
  await putPresignedObject(session, file, (percent) => setState({ kind: "uploading", percent }));
  setState({ kind: "uploaded_unverified" });
  const result = await finalizeUpload(session.document_id, session.upload_id, { idempotencyKey: key.current });
  setState(uploadResultToUiState(result));
};
```

For `202`, show verification queued and navigate only after the document projection reports `review_required` or another terminal failure. For `201 finalized`, navigate to document progress. Show sanitized checksum/MIME/quarantine reasons without echoing source text or signed URLs.

- [ ] **Step 5: Run upload unit, accessibility, type, lint, and build checks**

Run: `cd app/frontend; bun run test -- src/components/hms/document-upload/DocumentUploadFlow.test.tsx src/lib/api/documents.test.ts; bun run typecheck; bun run lint; $env:VITE_API_URL='http://127.0.0.1:8000/api/v1'; bun run build`

Expected: PASS; no multipart source upload remains in the route and no R2 URL appears in logs or rendered errors.

- [ ] **Step 6: Commit**

```bash
git add app/frontend/src/routes/_app.documents.upload.tsx app/frontend/src/components/hms/document-upload app/frontend/src/lib/api/documents.ts app/frontend/src/lib/api/documents.test.ts
git commit -m "frontend: upload immutable source objects directly"
```

### Task 16: Build the Revision-Aware OCR Review Workspace

**Files:**
- Create: `app/frontend/src/components/hms/document-workspace/DocumentWorkspace.tsx`
- Create: `app/frontend/src/components/hms/document-workspace/WorkspaceToolbar.tsx`
- Create: `app/frontend/src/components/hms/document-workspace/RevisionSelector.tsx`
- Create: `app/frontend/src/components/hms/document-workspace/PageNavigator.tsx`
- Create: `app/frontend/src/components/hms/document-workspace/OcrEditor.tsx`
- Create: `app/frontend/src/components/hms/document-workspace/RevisionDiff.tsx`
- Create: `app/frontend/src/components/hms/document-workspace/GeometryOverlay.tsx`
- Create: `app/frontend/src/components/hms/document-workspace/RevisionHistoryDrawer.tsx`
- Modify: `app/frontend/src/components/hms/DocumentPreview.tsx:8-115`
- Modify: `app/frontend/src/routes/_app.documents.$documentId.tsx:25-194`
- Modify: `app/frontend/src/routes/_app.documents.$documentId.review.tsx:26-235`
- Test: `app/frontend/src/components/hms/document-workspace/DocumentWorkspace.test.tsx`
- Test: `app/frontend/src/components/hms/document-workspace/OcrEditor.test.tsx`

**Interfaces:**
- Workspace displays source, thumbnails, page text, Corrected/Raw/Diff tabs, confidence, engine, revision selector, author/time/status, geometry, and history.
- Old revisions are read-only; restore creates a new child. Save shows unsaved state and uses server ETag. `409` opens compare/reload UI without discarding local text.
- Approval confirmation queues generation and displays progress; chat remains disabled for unapproved drafts.
- Structured-fact review remains a second layer on the existing review route and links each fact to page revision and aligned geometry.

- [ ] **Step 1: Write failing workspace behavior tests**

```tsx
it("keeps a historical revision read-only and restores as a new child", async () => {
  render(<DocumentWorkspace documentId="doc-1" />);
  await user.selectOptions(screen.getByLabelText("Revision"), "rev-1");
  expect(screen.getByRole("textbox", { name: "Corrected page text" })).toHaveAttribute("readonly");
  await user.click(screen.getByRole("button", { name: "Restore as new revision" }));
  expect(restoreRevision).toHaveBeenCalledWith("doc-1", "rev-1", expect.any(Object));
});

it("shows a compare action on stale If-Match without losing local text", async () => {
  saveDraftPage.mockRejectedValue(new ApiError(409, "Draft changed"));
  render(<OcrEditor initialText="local correction" lockVersion={3} />);
  await user.click(screen.getByRole("button", { name: "Save draft" }));
  expect(screen.getByDisplayValue("local correction")).toBeVisible();
  expect(screen.getByRole("button", { name: "Compare with latest" })).toBeVisible();
});
```

- [ ] **Step 2: Run workspace tests and verify RED**

Run: `cd app/frontend; bun run test -- src/components/hms/document-workspace/DocumentWorkspace.test.tsx src/components/hms/document-workspace/OcrEditor.test.tsx`

Expected: FAIL because workspace components do not exist and the current text panel is read-only typewriter output.

- [ ] **Step 3: Compose a focused workspace state model**

```tsx
export function DocumentWorkspace({ documentId }: { documentId: string }) {
  const documentQuery = useQuery({ queryKey: ["document", documentId], queryFn: () => getDocument(documentId) });
  const revisionsQuery = useQuery({
    queryKey: ["document-revision-sets", documentId],
    queryFn: () => listRevisionSets(documentId),
  });
  const [selectedRevisionId, setSelectedRevisionId] = useState<string | null>(null);
  const [selectedPage, setSelectedPage] = useState(1);
  return (
    <WorkspaceLayout
      toolbar={<WorkspaceToolbar document={documentQuery.data} revision={selectedRevision} />}
      source={<DocumentPreview documentId={documentId} mimeType={documentQuery.data?.mime_type ?? ""} />}
      editor={<OcrEditor documentId={documentId} page={selectedPage} revision={selectedRevision} />}
      history={<RevisionHistoryDrawer revisionSets={revisionsQuery.data?.items ?? []} />}
    />
  );
}
```

- [ ] **Step 4: Implement editor save/compare/approve state transitions**

```tsx
const saveMutation = useMutation({
  mutationFn: () =>
    saveDraftPage(documentId, page.page_number, {
      parent_revision_id: page.id,
      corrected_text: text,
      edit_reason: reason,
    }, { idempotencyKey: mutationKey.current, lockVersion }),
  onSuccess: (saved) => {
    setDirty(false);
    setLockVersion(saved.lock_version);
    mutationKey.current = newIdempotencyKey("draft-page");
  },
  onError: (error) => {
    if (error instanceof ApiError && error.status === 409) setConflict(error);
  },
});
```

Require an edit reason when critical number/unit/date/negation fields change. Never overwrite `raw_text_snapshot`.

- [ ] **Step 5: Render geometry only when alignment permits exact evidence**

```tsx
const exactBoxes = geometry.filter((item) => item.alignment_status === "aligned");
return <GeometryOverlay boxes={exactBoxes} staleCount={geometry.length - exactBoxes.length} />;
```

- [ ] **Step 6: Replace detail composition and link structured facts to revision regions**

The detail route renders `DocumentWorkspace`; the existing review route uses `page_revision_id` and bounding-box locators, preserves field-level review, and removes hardcoded `version: 1`.

- [ ] **Step 7: Run component, route, accessibility, type, and lint checks**

Run: `cd app/frontend; bun run test -- src/components/hms/document-workspace src/lib/api/document-revisions.test.ts; bun run typecheck; bun run lint`

Expected: PASS; buttons have accessible names and stale geometry is never presented as exact evidence.

- [ ] **Step 8: Commit**

```bash
git add app/frontend/src/components/hms/document-workspace app/frontend/src/components/hms/DocumentPreview.tsx app/frontend/src/routes/_app.documents.$documentId.tsx app/frontend/src/routes/_app.documents.$documentId.review.tsx
git commit -m "frontend: build revision-aware OCR workspace"
```

### Task 17: Add Graph/Timeline Exploration and Correct Evidence/Chat Presentation

**Files:**
- Create: `app/frontend/src/components/hms/GraphFilters.tsx`
- Create: `app/frontend/src/components/hms/GraphExplanationPanel.tsx`
- Create: `app/frontend/src/components/hms/ClinicalTimelinePanel.tsx`
- Modify: `app/frontend/src/components/hms/GraphCanvas.tsx:252`
- Modify: `app/frontend/src/components/hms/EvidenceRail.tsx:15-146`
- Modify: `app/frontend/src/components/hms/ChatMessage.tsx`
- Modify: `app/frontend/src/routes/_app.graph.patients.$patientId.tsx`
- Modify: `app/frontend/src/routes/_app.patients.$patientId.timeline.tsx`
- Modify: `app/frontend/src/routes/_app.documents.$documentId.tsx`
- Test: `app/frontend/src/components/hms/GraphFilters.test.tsx`
- Test: `app/frontend/src/components/hms/EvidenceRail.test.tsx`
- Modify: `app/frontend/src/components/hms/ChatMessage.test.tsx`

**Interfaces:**
- Graph controls expose only spec-supported values and show source-backed paths separately from final citations.
- Timeline shows clinical/recorded dates, evidence, confidence, reviewer/conflict state, and supersession lineage.
- Evidence identity is stable per message; rail numbering matches selected message; exact navigation uses `document_id`, page, revision, and aligned bounding box.
- Assistant Markdown is sanitized and executable HTML is disabled. UI says “validated sentence streaming,” never raw token streaming.

- [ ] **Step 1: Write failing evidence identity, navigation, and sanitization tests**

```tsx
it("routes a citation to its document, page, revision, and aligned region", async () => {
  render(<EvidenceRail messageId="m1" items={[evidence]} />);
  const link = screen.getByRole("link", { name: "Open exact evidence" });
  expect(link).toHaveAttribute(
    "href",
    expect.stringContaining(`/documents/${evidence.document_id}?page=2&revision=${evidence.revision_set_id}`),
  );
});

it("does not execute HTML embedded in assistant markdown", () => {
  render(<ChatMessage content={'Safe **text** <img src=x onerror="alert(1)">'} citations={[]} />);
  expect(screen.getByText("Safe", { exact: false })).toBeVisible();
  expect(document.querySelector("img")).toBeNull();
});
```

- [ ] **Step 2: Run graph/evidence/chat tests and verify RED**

Run: `cd app/frontend; bun run test -- src/components/hms/GraphFilters.test.tsx src/components/hms/EvidenceRail.test.tsx src/components/hms/ChatMessage.test.tsx`

Expected: FAIL because current evidence lacks revision/region identity and chat renders plain text.

- [ ] **Step 3: Implement typed graph filters and query serialization**

```tsx
export const DEFAULT_GRAPH_FILTERS: DocumentGraphFilters = {
  node_limit: 50,
  edge_limit: 100,
  hop_depth: 2,
  entity_types: [],
  relation_types: [],
  min_confidence: 0,
  document_scope: [],
  layout: "force",
  include_superseded: false,
};
```

Show `include_superseded` only when the API capability payload grants `superseded_evidence.read`; label returned rows “Audit-only superseded evidence.”

- [ ] **Step 4: Make evidence labels message-stable**

```typescript
export function evidenceLabel(messageId: string, evidenceId: string, index: number): EvidenceLabel {
  return { stableId: `${messageId}:${evidenceId}`, inlineNumber: index + 1, display: `[${index + 1}]` };
}
```

Use the same ordered evidence array for inline citation rendering and the selected-message rail. Display real document date, page, revision, approval state, score, retrieval method, offsets, and aligned geometry status.

- [ ] **Step 5: Render safe Markdown and graph explanation separately**

```tsx
<MarkdownRenderer
  content={message.content}
  allowHtml={false}
  allowedProtocols={["http", "https"]}
  renderCitation={(id) => <CitationChip evidence={evidenceById[id]} />}
/>
<GraphExplanationPanel explanation={message.graphExplanation} />
```

Use a project-approved Markdown parser/sanitizer dependency and add it to `package.json`/`bun.lock`; never use `dangerouslySetInnerHTML`.

- [ ] **Step 6: Run frontend unit, E2E graph/chat, type, lint, and build checks**

Run: `cd app/frontend; bun run test; bun run typecheck; bun run lint; $env:VITE_API_URL='http://127.0.0.1:8000/api/v1'; bun run build`

Expected: PASS; existing graph/chat tests remain green.

- [ ] **Step 7: Commit**

```bash
git add app/frontend/package.json app/frontend/bun.lock app/frontend/src/components/hms/GraphFilters.tsx app/frontend/src/components/hms/GraphExplanationPanel.tsx app/frontend/src/components/hms/ClinicalTimelinePanel.tsx app/frontend/src/components/hms/GraphCanvas.tsx app/frontend/src/components/hms/EvidenceRail.tsx app/frontend/src/components/hms/ChatMessage.tsx app/frontend/src/routes/_app.graph.patients.$patientId.tsx app/frontend/src/routes/_app.patients.$patientId.timeline.tsx app/frontend/src/routes/_app.documents.$documentId.tsx app/frontend/src/components/hms/GraphFilters.test.tsx app/frontend/src/components/hms/EvidenceRail.test.tsx app/frontend/src/components/hms/ChatMessage.test.tsx
git commit -m "frontend: trace graph and chat evidence exactly"
```

### Task 18: Implement Unified Corpus V3, Frozen Threshold Artifacts, and Complete Metrics

**Files:**
- Create: `app/backend/src/hospital_ai/evaluation/corpus_v3.py`
- Create: `app/backend/src/hospital_ai/evaluation/threshold_artifact.py`
- Create: `app/backend/src/hospital_ai/evaluation/unified_metrics.py`
- Create: `app/backend/src/hospital_ai/evaluation/product_timeline_adapter.py`
- Create: `app/backend/src/hospital_ai/evaluation/product_stream_adapter.py`
- Create: `app/backend/data/evaluation/corpus-v3.schema.json`
- Create: `app/backend/data/evaluation/thresholds-v3.schema.json`
- Create: `app/backend/data/evaluation/corpus-v3-smoke-manifest.json`
- Modify: `app/backend/src/hospital_ai/evaluation/contracts.py`
- Modify: `app/backend/src/hospital_ai/evaluation/corpus_manifest.py`
- Modify: `app/backend/src/hospital_ai/evaluation/runner.py:487-676`
- Modify: `app/backend/scripts/run_ai_evaluation.py`
- Test: `app/backend/tests/evaluation/test_corpus_v3.py`
- Test: `app/backend/tests/evaluation/test_threshold_artifact.py`
- Test: `app/backend/tests/evaluation/test_unified_metrics.py`
- Test: `app/backend/tests/evaluation/test_product_timeline_adapter.py`
- Test: `app/backend/tests/evaluation/test_product_stream_adapter.py`
- Modify: `app/backend/tests/evaluation/test_evaluation_runner.py`

**Interfaces:**
- Corpus ID is exactly `hospital-ai-unified-clinical-corpus-v3`; every representation shares `corpus_item_id` and approved revision IDs.
- Split isolation applies to patient IDs, document families, and near-duplicate renderings.
- Threshold artifact fields: corpus version, qualification run ID, metric implementation version, values, calibration date, Git SHA, artifact hash; immutable before holdout.
- Metrics include all OCR, retrieval, graph, timeline, and chat metrics in spec sections 14.2–14.5. `product_timeline_adapter.py` calls the real filtered timeline service, and `product_stream_adapter.py` parses the real SSE endpoint including interrupted/error outcomes; local judge results remain supplemental.

- [ ] **Step 1: Write failing corpus-isolation and threshold-freeze tests**

```python
def test_corpus_v3_rejects_patient_family_or_near_duplicate_split_leakage() -> None:
    manifest = corpus_manifest_with_cross_split_near_duplicate()
    with pytest.raises(CorpusV3ValidationError, match="split leakage"):
        validate_corpus_v3(manifest)


def test_holdout_requires_frozen_threshold_artifact_before_results(tmp_path: Path) -> None:
    artifact = threshold_artifact(qualification_run_id="q-1", frozen=False)
    with pytest.raises(ReleaseGateError, match="frozen threshold artifact"):
        run_holdout(config(tmp_path), artifact)


def test_threshold_hash_detects_post_qualification_mutation() -> None:
    artifact = freeze_thresholds(valid_threshold_input())
    mutated = artifact.copy(update={"values": {**artifact.values, "citation_precision": 0.1}})
    assert verify_threshold_artifact(mutated) is False
```

- [ ] **Step 2: Run evaluation tests and verify RED**

Run: `cd app/backend; python -m pytest tests/evaluation/test_corpus_v3.py tests/evaluation/test_threshold_artifact.py tests/evaluation/test_unified_metrics.py -q`

Expected: FAIL because corpus v3 and frozen threshold contracts are absent.

- [ ] **Step 3: Define one item contract across all product stages**

```python
class UnifiedCorpusItemV3(BaseModel):
    corpus_item_id: str
    patient_surrogate_id: str
    document_family_id: str
    split: Literal["train", "qualification", "development", "sentinel", "holdout"]
    source_objects: tuple[SourceObjectRef, ...]
    canonical_transcript: ArtifactRef
    ocr_outputs: tuple[ArtifactRef, ...]
    approved_revision_ids: tuple[UUID, ...]
    structured_facts: tuple[ExpectedFact, ...]
    graph: ExpectedGraph
    timeline: tuple[ExpectedTimelineEvent, ...]
    questions: tuple[EvalCaseV3, ...]
    permissions: tuple[PermissionScenario, ...]
```

Smoke data is a fixed manifest slice of this corpus version, not a second dataset. Git contains schemas, cases, provenance/license registry, hashes, and only synthetic smoke artifacts; private R2 contains full bytes.

- [ ] **Step 4: Freeze and verify threshold artifacts**

```python
def freeze_thresholds(input: ThresholdCalibrationInput) -> ThresholdArtifact:
    payload = {
        "corpus_version": input.corpus_version,
        "qualification_run_id": input.qualification_run_id,
        "metric_implementation_version": input.metric_version,
        "values": dict(sorted(input.values.items())),
        "calibration_date": input.calibration_date.isoformat(),
        "git_sha": input.git_sha,
    }
    artifact_hash = sha256(canonical_json(payload)).hexdigest()
    return ThresholdArtifact(**payload, artifact_hash=artifact_hash, frozen=True)
```

- [ ] **Step 5: Bind every result to raw evidence and implement release gates**

Each run persists corpus/source hashes, approved revisions, model/embedding/graph/prompt/evaluator versions, Git SHA, run ID, timestamp, raw outputs, metric version, and limitations. Hard gates include zero unauthorized evidence, zero wrong-patient citations, zero superseded retrieval, two independent sentinel reviewers, reproducible hashes, 100% displayed graph provenance, factual claim validation/refusal, timeline evidence identity, and validated-SSE sequence/interrupt correctness. Every run writes `summary.json`; unavailable real OCR or incomplete review is a blocking state, not a fabricated score.

- [ ] **Step 6: Run deterministic smoke and release contract tests**

Run: `cd app/backend; python -m pytest tests/evaluation/test_corpus_v3.py tests/evaluation/test_threshold_artifact.py tests/evaluation/test_unified_metrics.py tests/evaluation/test_evaluation_runner.py -q`

Expected: PASS; unavailable image OCR or incomplete independent review is reported as a blocking gate, never as a score of zero or a pass.

- [ ] **Step 7: Commit**

```bash
git add app/backend/src/hospital_ai/evaluation/corpus_v3.py app/backend/src/hospital_ai/evaluation/threshold_artifact.py app/backend/src/hospital_ai/evaluation/unified_metrics.py app/backend/src/hospital_ai/evaluation/product_timeline_adapter.py app/backend/src/hospital_ai/evaluation/product_stream_adapter.py app/backend/data/evaluation/corpus-v3.schema.json app/backend/data/evaluation/thresholds-v3.schema.json app/backend/data/evaluation/corpus-v3-smoke-manifest.json app/backend/src/hospital_ai/evaluation/contracts.py app/backend/src/hospital_ai/evaluation/corpus_manifest.py app/backend/src/hospital_ai/evaluation/runner.py app/backend/scripts/run_ai_evaluation.py app/backend/tests/evaluation/test_corpus_v3.py app/backend/tests/evaluation/test_threshold_artifact.py app/backend/tests/evaluation/test_unified_metrics.py app/backend/tests/evaluation/test_product_timeline_adapter.py app/backend/tests/evaluation/test_product_stream_adapter.py app/backend/tests/evaluation/test_evaluation_runner.py
git commit -m "test: add unified clinical corpus v3 gates"
```

### Task 19: Add End-to-End Acceptance, Migration, CI, and Release Gates

**Files:**
- Create: `app/backend/tests/cdi_v2/test_normative_acceptance.py`
- Create: `app/frontend/e2e/cdi-v2-document-intelligence.spec.ts`
- Modify: `app/frontend/e2e/fixtures/api-mocks.ts`
- Modify: `.github/workflows/ci.yml`
- Create: `app/backend/tests/test_ci_workflow.py`
- Modify: `app/backend/scripts/verify_contracts.py`
- Create: `app/backend/scripts/verify_cdi_v2_release.py`
- Create: `docs/09-testing/cdi-v2-release-gates.md`

**Interfaces:**
- Acceptance covers all nine scenarios in spec section 19.1 and the complete user journey in section 17.3.
- CI blocks on migration-model alignment, backend/front-end tests, exact API contracts, deterministic corpus v3, active-generation safety, and the Playwright E2E journey; Playwright is not an advisory/deferred job for this feature.
- Real image/handwriting qualification and two-reviewer sentinel gates may run in a controlled release workflow, but absence/failure must produce `NO-GO`, never an automatic pass.

- [ ] **Step 1: Write the failing normative backend acceptance matrix**

```python
@pytest.mark.parametrize(
    "scenario",
    [
        "stale_if_match",
        "production_self_approval",
        "failed_generation_preserves_active",
        "stale_geometry_not_exact_evidence",
        "canonical_entity_multiple_sources",
        "wrong_patient_and_superseded_filtered",
        "upload_integrity_before_ocr",
        "validated_sse_sequence_and_interrupt",
        "legacy_synthetic_parity",
    ],
)
async def test_normative_acceptance_scenario(scenario, cdi_v2_harness) -> None:
    result = await cdi_v2_harness.run(scenario)
    assert result.passed, result.evidence
```

- [ ] **Step 2: Write the failing Playwright journey**

```typescript
test("upload, correct, approve, explore, chat, and open exact evidence", async ({ page }) => {
  await uploadSyntheticScan(page);
  await expect(page.getByText("Review required")).toBeVisible();
  await editPageAndSave(page, "Corrected 500 mg dose", "Correct numeric dose");
  await submitAndApproveWithDifferentUsers(page);
  await expect(page.getByText("Generation active")).toBeVisible();
  await page.getByRole("link", { name: "Open graph" }).click();
  await expect(page.getByText("Source evidence")).toBeVisible();
  await askPatientQuestion(page, "What is the approved metformin dose?");
  await expect(page.getByText("Validated sentence streaming")).toBeVisible();
  await page.getByRole("link", { name: "Open exact evidence" }).click();
  await expect(page.getByText("Revision v2")).toBeVisible();
});
```

- [ ] **Step 3: Run focused acceptance and E2E tests and verify RED**

Run: `cd app/backend; python -m pytest tests/cdi_v2/test_normative_acceptance.py -q`

Run: `cd app/frontend; bun run test:e2e -- cdi-v2-document-intelligence.spec.ts`

Expected: both fail until all tasks are integrated and mocks/contracts are updated.

- [ ] **Step 4: Make migration and contract checks blocking in CI**

```yaml
- name: Check migration-model alignment
  run: alembic check

- name: Verify CDI V2 release contracts
  run: python scripts/verify_cdi_v2_release.py --mode source

- name: Run CDI V2 normative acceptance
  run: python -m pytest tests/cdi_v2/test_normative_acceptance.py -q
```

Remove `|| true` from `alembic check`, make the CDI V2 Playwright job required, and assert the workflow YAML contains all blocking steps. Add backend/frontend path filters for corpus schemas, benchmark cases, and release scripts.

- [ ] **Step 5: Implement a machine-readable release verifier**

```python
REQUIRED_GATES = {
    "migration_chain",
    "legacy_parity",
    "zero_unauthorized_evidence",
    "zero_wrong_patient_citations",
    "zero_superseded_retrieval",
    "graph_provenance_coverage",
    "claim_validation",
    "sentinel_two_reviewers",
    "threshold_artifact_frozen",
    "hash_reproducibility",
    "ocr_strata_reported",
}

def release_decision(evidence: Mapping[str, GateEvidence]) -> str:
    missing = REQUIRED_GATES - set(evidence)
    failed = {name for name, gate in evidence.items() if name in REQUIRED_GATES and not gate.passed}
    return "GO" if not missing and not failed else "NO-GO"
```

The verifier prints missing/failed gates, artifact paths/hashes, Git SHA, and no PHI. It never infers runtime deployment from source checks.

- [ ] **Step 6: Run the complete local verification set**

Run: `cd app/backend; python -m ruff check src tests; python -m ruff format --check src tests; python -m pytest tests -q --cov=hospital_ai --cov-fail-under=80; python scripts/verify_contracts.py; alembic check`

Run: `cd app/frontend; bun run test; bun run typecheck; bun run lint; $env:VITE_API_URL='http://127.0.0.1:8000/api/v1'; bun run build; bun run test:e2e -- cdi-v2-document-intelligence.spec.ts`

Run: `cd app/backend; python scripts/run_ai_evaluation.py --suite smoke --lane deterministic --components corpus,ocr,retrieval,graph,timeline,chat,stream --retrieval-mode hybrid --output-dir evaluation-artifacts/cdi-v2/smoke`

Expected: code/tests/build pass; evaluation exits non-zero with explicit `NO-GO` if image OCR, threshold, sentinel review, or another required release artifact is incomplete.

- [ ] **Step 7: Verify diff scope and perform independent reviews**

Run GitNexus `detect_changes({scope: "compare", base_ref: "main"})`, then request separate spec-compliance, security/PHI, database/migration, Python, TypeScript, and release-evidence reviews. Resolve every P1/Critical finding before delivery.

- [ ] **Step 8: Commit**

```bash
git add app/backend/tests/cdi_v2/test_normative_acceptance.py app/frontend/e2e/cdi-v2-document-intelligence.spec.ts app/frontend/e2e/fixtures/api-mocks.ts .github/workflows/ci.yml app/backend/tests/test_ci_workflow.py app/backend/scripts/verify_contracts.py app/backend/scripts/verify_cdi_v2_release.py docs/09-testing/cdi-v2-release-gates.md
git commit -m "test: gate CDI v2 end-to-end release"
```

---

## Execution Order and Parallelism

1. Execute Tasks 1–5 sequentially because they define shared persistence, authorization, and write contracts.
2. After Task 5, Tasks 6 and 14 may proceed in parallel only if frontend uses committed API schemas and does not invent fields.
3. Execute Tasks 7–9 sequentially: generation rows must exist before backfill, and parity must pass before active-generation reads are enabled.
4. Execute Tasks 10–13 sequentially across graph/retrieval/chat because they share evidence lineage and release gates.
5. Tasks 15–18 may run in parallel after Tasks 11–14 land; file ownership must remain disjoint.
6. Task 19 is the integration gate and must run on one frozen candidate SHA.

## Completion Evidence

- One clean branch/worktree with unrelated dirty files preserved.
- Alembic upgrade/downgrade/re-upgrade and `alembic check` pass on PostgreSQL 16.
- Backend lint/format/tests pass with at least 80% coverage for the final branch.
- Frontend unit/type/lint/build and the CDI V2 Playwright journey pass.
- Backfill parity artifact proves zero wrong-patient and zero superseded-generation serving evidence for legacy synthetic records.
- Corpus v3 smoke/release artifacts are SHA-bound; missing image OCR, threshold, sentinel, or holdout evidence yields explicit `NO-GO`.
- Evaluation output contains `summary.json` with timeline and validated-stream metrics plus explicit unavailable/blocking gates.
- Independent reviews contain no unresolved P1/Critical finding.
- PR summary separates implemented source behavior, local tests, remote CI, benchmark evidence, deployment, and production readiness.
