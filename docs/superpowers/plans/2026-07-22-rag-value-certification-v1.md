# RAG Value Certification v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reproducible certification system that proves patient RAG and Graph RAG improve chat quality while enforcing claim-level evidence support and zero unauthorized model context.

**Architecture:** Add a focused `hospital_ai.evaluation` package for corpus governance, benchmark contracts, scoring, ablation execution, and reporting. Instrument the existing chat orchestration through explicit internal-only certification controls and immutable trace snapshots, keeping authorization before ranking/generation and preserving sync/SSE/thread/trace parity. Deterministic CI blocks merge; live-provider evaluation remains a separately reported manual/nightly lane.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy async, PostgreSQL/pgvector, Pydantic v2, pytest/pytest-asyncio, GitHub Actions, Bun/Vitest/TypeScript.

## Global Constraints

- Work only in `D:\projects\chatbot-hospital-system-rag-value-cert-v1` on `feat/rag-value-certification-v1`.
- Preserve exactly 100 synthetic patients and 200 canonical patient records; do not add Synthea or real PHI.
- Remove corpus copies only after byte-for-byte SHA-256 pairing proves they are duplicates.
- Keep public guideline/drug knowledge runtime-excluded until provenance and license review passes.
- The benchmark contains at least 300 cases with category minima `70/50/35/45/30/45/25`; 50 sentinel cases receive explicit independent source-to-annotation review and are labeled agent-reviewed, not clinician-validated.
- Evaluate identical questions in `rag_off`, `hybrid_graph_off`, and `hybrid_graph_on` modes with all non-ablation settings pinned.
- RAG lift is at least 20 percentage points; Graph lift is at least 15 points on graph-only cases; Graph semantic regression is no worse than 2 points.
- Recall@5 is at least 90%; MRR@5 is at least 85%; answer fact/slot F1 is at least 90%.
- Citation precision is at least 98%; citation recall is at least 95%; critical-fact support is 100%.
- Unauthorized selected model-context chunks are zero; revoked, expired, soft-deleted, and mismatched join denial is 100%.
- Safe-refusal recall is 100%; false-refusal rate is at most 5%; severe hallucinations are zero.
- Sync/SSE/thread/RAG-trace parity is 100% for applicable fixtures.
- Live-provider evaluation is 30 stratified cases times 3 runs with pinned provider/model/prompt/corpus and p95 latency at most 30 seconds.
- Deterministic CI never reads expected answers as generator input, never defaults an empty denominator or metric to `1.0`, and never uses `continue-on-error` for certification.
- Before changing any function, class, or method, run GitNexus upstream impact analysis and warn before HIGH or CRITICAL edits. Before every commit, run GitNexus `detect_changes` for the worktree.
- Follow strict RED-GREEN-REFACTOR TDD. Every task receives spec-compliance and code-quality review before the next task starts.

## Execution Preflight

No production-code task starts until the clean backend baseline runs under Python 3.12. Drive C exhaustion previously blocked `uv`; use a D-drive cache without changing tracked files:

```powershell
$env:UV_CACHE_DIR = 'D:\projects\.uv-cache-rag-cert'
uv sync --python 3.12 --frozen
uv run --python 3.12 pytest tests/ -q --tb=short
```

Expected: dependency sync succeeds and the existing backend suite passes. If provisioning or tests fail, stop and report the exact blocker; do not attribute it to this branch or begin Task 1. Record the baseline command and result in `.superpowers/sdd/progress.md`.

## File and Responsibility Map

| File | Responsibility |
| --- | --- |
| `app/backend/src/hospital_ai/evaluation/models.py` | Immutable benchmark, trace, result, metric, and gate contracts |
| `app/backend/src/hospital_ai/evaluation/corpus.py` | Corpus hashing, manifest validation, duplicate pairing, quarantine rules |
| `app/backend/src/hospital_ai/evaluation/benchmark.py` | Deterministic 300-case generation and benchmark validation |
| `app/backend/src/hospital_ai/evaluation/scoring.py` | Retrieval, answer, citation, refusal, leakage, lift, and latency metrics |
| `app/backend/src/hospital_ai/evaluation/claims.py` | Deterministic atomic-claim extraction and source-span support checks |
| `app/backend/src/hospital_ai/evaluation/runner.py` | A/B/C execution through the actual chat orchestration boundary |
| `app/backend/src/hospital_ai/evaluation/reporting.py` | JSONL, aggregate JSON, JUnit, and Markdown artifacts |
| `app/backend/src/hospital_ai/services/chat.py` | Internal certification controls and exact context/graph trace capture |
| `app/backend/src/hospital_ai/services/retrieval.py` | Full join-chain and role/document authorization invariants |
| `app/backend/src/hospital_ai/api/routes/chat_stream.py` | Shared orchestration and parity, without a second safety implementation |
| `app/backend/src/hospital_ai/api/routes/rag_trace.py` | Read-time reauthorization of persisted evidence |
| `app/backend/scripts/build_rag_benchmark.py` | Regenerate/validate benchmark data deterministically |
| `app/backend/scripts/validate_rag_corpus.py` | Build/validate the corpus manifest and duplicate-pair artifact |
| `app/backend/scripts/run_rag_eval.py` | Certification CLI, replacing the six-case smoke evaluator |
| `app/backend/scripts/ingest_synthetic_dataset.py` | Durable ingest accounting, source fingerprints, and idempotency |
| `app/backend/data/hosp_ai_synthetic_dataset/MANIFEST.json` | Versioned per-file corpus release manifest |
| `app/backend/data/rag_value_benchmark_v1.jsonl` | 300+ controlled benchmark cases |
| `app/backend/data/rag_value_sentinel_v1.jsonl` | Frozen 50-case independently reviewed subset |
| `.github/workflows/ci.yml` | Mandatory deterministic certification job |
| `.github/workflows/rag-live-evaluation.yml` | Manual/nightly live-provider lane |

---

### Task 1: Govern the Canonical 100-Patient Corpus

**Files:**
- Create: `app/backend/src/hospital_ai/evaluation/__init__.py`
- Create: `app/backend/src/hospital_ai/evaluation/models.py`
- Create: `app/backend/src/hospital_ai/evaluation/corpus.py`
- Create: `app/backend/scripts/validate_rag_corpus.py`
- Create: `app/backend/tests/evaluation/test_corpus.py`
- Modify: `app/backend/data/hosp_ai_synthetic_dataset/MANIFEST.json`
- Modify: `app/backend/data/hosp_ai_synthetic_dataset/README.md`
- Delete after verified pairing: `app/backend/data/hosp_ai_synthetic_dataset/app/`

**Interfaces:**
- Produces: `CorpusFile`, `CorpusManifest`, `CorpusValidationResult` frozen Pydantic models.
- Produces: `sha256_file(path: Path) -> str`.
- Produces: `build_manifest(data_root: Path, duplicate_root: Path | None) -> CorpusManifest`.
- Produces: `validate_manifest(manifest: CorpusManifest, data_root: Path) -> CorpusValidationResult`.
- Produces: `pair_verified_duplicates(canonical_root: Path, duplicate_root: Path) -> dict[Path, Path]`.

- [ ] **Step 1: Run CodeGraph/GitNexus impact checks**

Run GitNexus queries for `ingest_synthetic_dataset`, dataset paths, and manifest consumers. Because the new evaluation models have no callers, no impact call is required until an existing symbol is edited. Record findings in the task report.

- [ ] **Step 2: Write failing corpus contract tests**

```python
def test_manifest_requires_one_hashed_record_per_patient_file(corpus_root: Path) -> None:
    manifest = build_manifest(corpus_root, None)
    patient_files = [item for item in manifest.files if item.classification == "patient_record"]
    assert len({item.patient_id for item in patient_files}) == 100
    assert len(patient_files) == 200
    assert all(len(item.sha256) == 64 for item in patient_files)


def test_duplicate_pairing_rejects_same_name_with_different_bytes(tmp_path: Path) -> None:
    canonical = tmp_path / "canonical"
    duplicate = tmp_path / "duplicate"
    canonical.mkdir()
    duplicate.mkdir()
    (canonical / "record.csv").write_text("canonical", encoding="utf-8")
    (duplicate / "record.csv").write_text("changed", encoding="utf-8")
    with pytest.raises(CorpusValidationError, match="SHA-256 mismatch"):
        pair_verified_duplicates(canonical, duplicate)


def test_unreviewed_public_knowledge_is_quarantined(corpus_root: Path) -> None:
    manifest = build_manifest(corpus_root, None)
    public_files = [item for item in manifest.files if item.classification == "public_knowledge"]
    assert public_files
    assert all(item.quarantine_state == "excluded_pending_review" for item in public_files)
    assert all(item.runtime_approved is False for item in public_files)
```

- [ ] **Step 3: Run tests and verify RED**

Run: `uv run pytest tests/evaluation/test_corpus.py -q`

Expected: collection fails because `hospital_ai.evaluation.corpus` and its models do not exist.

- [ ] **Step 4: Implement immutable corpus contracts and validation**

```python
class CorpusFile(BaseModel):
    model_config = ConfigDict(frozen=True)
    relative_path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    byte_size: int = Field(gt=0)
    patient_id: UUID | None
    document_id: str
    document_type: str
    mime_type: str
    generator: str
    generator_version: str
    source: str
    synthetic: bool
    license_state: Literal["synthetic-approved", "pending-review"]
    classification: Literal["patient_record", "public_knowledge", "audit_fixture", "metadata"]
    quarantine_state: Literal["active", "excluded_pending_review"]
    runtime_approved: bool


class CorpusManifest(BaseModel):
    model_config = ConfigDict(frozen=True)
    schema_version: Literal["1.0"]
    corpus_version: str
    patient_count: int
    patient_record_count: int
    files: tuple[CorpusFile, ...]
```

Implement path normalization with `Path.resolve()` containment checks, streaming SHA-256 reads, MRN-to-patient-ID lookup from `metadata/generated_patients_seed.csv`, MIME allowlisting, and explicit public-knowledge quarantine. Return all validation errors instead of stopping at the first error.

- [ ] **Step 5: Generate the manifest and verified duplicate map**

Run: `uv run python scripts/validate_rag_corpus.py --data-root data --duplicate-root data/hosp_ai_synthetic_dataset/app/backend/data --write-manifest data/hosp_ai_synthetic_dataset/MANIFEST.json --write-duplicate-report history/rag-eval/corpus-duplicate-pairs.json`

Expected: JSON artifact lists exactly 210 duplicate pairings for the nested `app/backend/data` copy and zero mismatches. Inspect pair counts by directory before removal.

- [ ] **Step 6: Remove only the verified nested copy and revalidate**

Delete the exact directory `app/backend/data/hosp_ai_synthetic_dataset/app/` only after Step 5 succeeds. Run the validator twice and assert identical manifest bytes.

Run: `uv run pytest tests/evaluation/test_corpus.py -q`

Expected: all corpus tests pass; manifest reports 100 patients, 200 patient records, zero duplicate digests, zero orphan/mismatch/null ownership errors.

- [ ] **Step 7: Review and commit**

Run GitNexus `detect_changes(scope="all", base_ref="main", worktree="D:\\projects\\chatbot-hospital-system-rag-value-cert-v1")`, request spec/quality review, fix all Critical/Important findings, then commit:

```powershell
git add app/backend/src/hospital_ai/evaluation app/backend/tests/evaluation app/backend/scripts/validate_rag_corpus.py app/backend/data/hosp_ai_synthetic_dataset
git commit -m "data: govern canonical RAG corpus"
```

### Task 2: Make Synthetic Ingestion Accountable and Idempotent

**Files:**
- Create: `app/backend/src/hospital_ai/evaluation/ingestion.py`
- Create: `app/backend/tests/evaluation/test_ingestion_certification.py`
- Modify: `app/backend/scripts/ingest_synthetic_dataset.py`
- Modify: `app/backend/src/hospital_ai/workers/jobs.py`

**Interfaces:**
- Consumes: `CorpusManifest` from Task 1.
- Produces: `IngestFileResult(path, fingerprint, state, document_id, page_ids, chunk_ids, generation, attempts, error_code)`.
- Produces: `IngestCertificationReport` with complete accounting and idempotency comparisons.
- Produces: `certify_ingestion(manifest, first_run, second_run) -> IngestCertificationReport`.

- [ ] **Step 1: Run impact analysis before editing existing symbols**

Run upstream impact for the importer entry point and the exact worker function that indexes a document. Warn and pause if risk is HIGH/CRITICAL; otherwise record callers/processes in the task report.

- [ ] **Step 2: Write failing durability and idempotency tests**

```python
@pytest.mark.asyncio
async def test_failed_existing_document_is_retried_not_skipped(session, manifest_file) -> None:
    first = await ingest_one(session, manifest_file, processor=FailingProcessor("ocr_failed"))
    second = await ingest_one(session, manifest_file, processor=SuccessfulProcessor())
    assert first.state == "failed"
    assert second.state == "indexed"
    assert second.attempts == 2


def test_unchanged_second_run_has_no_duplicate_derived_rows(first_run, second_run) -> None:
    report = certify_ingestion(first_run.manifest, first_run, second_run)
    assert report.missing_files == ()
    assert report.duplicate_documents == ()
    assert report.duplicate_pages == ()
    assert report.duplicate_chunks == ()
    assert report.source_fingerprint_mismatches == ()
```

- [ ] **Step 3: Verify RED**

Run: `uv run pytest tests/evaluation/test_ingestion_certification.py -q`

Expected: failures show the importer skips failed existing documents and has no durable certification result.

- [ ] **Step 4: Implement source/generation contracts**

Compute the source fingerprint from the manifest SHA-256. Reuse derived records only when fingerprint and completed generation match. Retry failed or partial records; fail closed on unknown fingerprints, embedding-count mismatch, or stale generation. Convert swallowed processing exceptions into durable `failed` results while keeping sanitized error codes.

- [ ] **Step 5: Verify production-shaped PostgreSQL behavior**

Run the focused test against PostgreSQL:

```powershell
$env:HOSPITAL_AI_DATABASE_URL='postgresql+asyncpg://hospital_ai:hospital_ai@localhost:5432/hospital_ai_test'
uv run pytest tests/evaluation/test_ingestion_certification.py -q
```

Expected: first-run complete accounting and second-run idempotency pass with zero duplicates.

- [ ] **Step 6: Review and commit**

Run change detection, per-task review, fixes, and re-review. Commit:

```powershell
git add app/backend/src/hospital_ai/evaluation/ingestion.py app/backend/tests/evaluation/test_ingestion_certification.py app/backend/scripts/ingest_synthetic_dataset.py app/backend/src/hospital_ai/workers/jobs.py
git commit -m "backend: certify corpus ingestion"
```

### Task 3: Build the 300-Case Ground-Truth Benchmark

**Files:**
- Create: `app/backend/src/hospital_ai/evaluation/benchmark.py`
- Create: `app/backend/scripts/build_rag_benchmark.py`
- Create: `app/backend/tests/evaluation/test_benchmark.py`
- Create: `app/backend/data/rag_value_benchmark_v1.jsonl`
- Create: `app/backend/data/rag_value_sentinel_v1.jsonl`
- Remove: `app/backend/tests/eval_dataset.json`
- Deprecate: `app/backend/data/golden_dataset.json`

**Interfaces:**
- Produces: frozen `BenchmarkCase`, `ExpectedFact`, `ExpectedCitation`, `PermissionFixture`, and `GraphExpectation` models.
- Produces: `generate_benchmark(manifest: CorpusManifest, seed: int = 20260722) -> tuple[BenchmarkCase, ...]`.
- Produces: `validate_benchmark(cases) -> BenchmarkValidationResult`.

- [ ] **Step 1: Write failing schema and composition tests**

```python
def test_benchmark_has_required_category_minima(benchmark_cases) -> None:
    counts = Counter(case.category for case in benchmark_cases)
    assert counts == {
        "single_hop": 70,
        "multi_document": 50,
        "temporal_conflict": 35,
        "graph_only": 45,
        "overlapping_patient": 30,
        "permission_adversarial": 45,
        "safe_refusal": 25,
    }


def test_case_contains_independent_ground_truth(case: BenchmarkCase) -> None:
    assert case.expected_facts
    assert case.allowed_chunk_ids or case.answer_policy != "answer"
    assert set(case.allowed_chunk_ids).isdisjoint(case.forbidden_chunk_ids)
    assert case.expected_answer_text is None


def test_sentinel_has_fifty_independently_reviewed_cases(sentinel_cases) -> None:
    assert len(sentinel_cases) == 50
    assert all(case.review.status == "agent-reviewed" for case in sentinel_cases)
    assert all(len(case.review.reviewers) >= 2 for case in sentinel_cases)
```

- [ ] **Step 2: Verify RED**

Run: `uv run pytest tests/evaluation/test_benchmark.py -q`

Expected: benchmark module and v1 datasets are absent.

- [ ] **Step 3: Implement deterministic case generation**

Generate facts from the canonical CSV values and structured ingestion metadata, never from an LLM response. Use stable UUIDv5 IDs derived from corpus version, category, patient, question template, and source row. For graph-only cases, derive required relations from the seeded graph facts and reject any case whose required path is not present after indexing.

The case contract must exclude full expected prose:

```python
class BenchmarkCase(BaseModel):
    model_config = ConfigDict(frozen=True)
    case_id: str
    schema_version: Literal["1.0"]
    corpus_version: str
    patient_id: UUID
    actor: ActorFixture
    question: str
    category: CaseCategory
    expected_facts: tuple[ExpectedFact, ...]
    allowed_chunk_ids: tuple[UUID, ...]
    forbidden_chunk_ids: tuple[UUID, ...]
    expected_citations: tuple[ExpectedCitation, ...]
    graph: GraphExpectation | None
    answer_policy: Literal["answer", "scoped_refusal", "safe_no_evidence"]
    expected_answer_text: None = None
    review: ReviewRecord
```

- [ ] **Step 4: Generate and validate all cases**

Run: `uv run python scripts/build_rag_benchmark.py --seed 20260722 --write`

Expected: exactly 300 cases with the required distribution, stable bytes on a second run, valid source IDs, zero cross-patient allowed evidence, and no expected answer prose.

- [ ] **Step 5: Independently review the 50-case sentinel**

Dispatch two fresh reviewer agents. Each reads source files, manifest records, and proposed annotations for all 50 sentinel cases and writes a signed review artifact with per-case `approved` or finding. Resolve every finding, regenerate only non-frozen candidate data, then set `review.status="agent-reviewed"` with both reviewer identifiers and source hashes. Do not label this clinician-reviewed or human-validated.

- [ ] **Step 6: Verify and commit**

Run: `uv run pytest tests/evaluation/test_benchmark.py tests/test_golden_dataset.py -q`

Update `test_golden_dataset.py` to reject use of the deprecated five-case file as a certification input. Run change detection and per-task reviews. Commit:

```powershell
git add app/backend/src/hospital_ai/evaluation/benchmark.py app/backend/scripts/build_rag_benchmark.py app/backend/tests/evaluation app/backend/tests/test_golden_dataset.py app/backend/data
git commit -m "test: add RAG value benchmark v1"
```

### Task 4: Replace Fake Scores with Deterministic Claim-Level Metrics

**Files:**
- Create: `app/backend/src/hospital_ai/evaluation/claims.py`
- Create: `app/backend/src/hospital_ai/evaluation/scoring.py`
- Create: `app/backend/tests/evaluation/test_claim_support.py`
- Create: `app/backend/tests/evaluation/test_scoring.py`
- Delete: `app/backend/scripts/evaluate_rag.py`
- Modify: `app/backend/tests/test_rag_eval.py`

**Interfaces:**
- Produces: `score_case(case: BenchmarkCase, trace: EvaluationTrace) -> CaseScore`.
- Produces: `aggregate_scores(scores: Sequence[CaseScore]) -> CertificationMetrics`.
- Produces: `evaluate_claim_support(claim, cited_chunks) -> SupportVerdict`.
- Produces: `safe_ratio(numerator: int, denominator: int, metric: str) -> MetricValue`.
- Produces: `evaluate_gates(metrics) -> tuple[GateResult, ...]`.

- [ ] **Step 1: Run upstream impact for `evaluate_stub_response` and `test_rag_eval` consumers**

Record the current low blast radius and confirm no runtime route imports `evaluate_rag.py`.

- [ ] **Step 2: Write adversarial failing tests**

```python
def test_valid_evidence_id_does_not_credit_unsupported_claim(case, trace) -> None:
    trace = trace.model_copy(update={"answer": "HbA1c is 4.2% [E1]."})
    score = score_case(case, trace)
    assert score.citation_precision == 0.0
    assert score.unsupported_claim_count == 1


def test_empty_denominator_fails_instead_of_returning_one() -> None:
    with pytest.raises(InvalidMetricError, match="empty denominator"):
        safe_ratio(0, 0, metric="citation_precision")


def test_expected_output_substitution_is_detected(case, trace) -> None:
    leaked = trace.model_copy(update={"answer": serialize_expected_facts(case.expected_facts)})
    with pytest.raises(GroundTruthLeakageError):
        assert_no_ground_truth_leakage(case, leaked.generator_inputs)


def test_graph_display_without_selected_cited_evidence_gets_no_graph_credit(case, trace) -> None:
    trace = trace.model_copy(update={"graph_ran": True, "graph_selected_chunk_ids": (), "cited_chunk_ids": ()})
    assert score_case(case, trace).graph_value_credit is False
```

- [ ] **Step 3: Verify RED**

Run: `uv run pytest tests/evaluation/test_claim_support.py tests/evaluation/test_scoring.py tests/test_rag_eval.py -q`

Expected: tests fail because deterministic scoring and claim support do not exist; the existing constant-`1.0` evaluator fails the adversarial assertions.

- [ ] **Step 4: Implement deterministic metrics**

Normalize answer text and match typed atomic facts by exact value/unit/date rules plus bounded aliases stored in the case. Calculate Recall@5, MRR@5, fact precision/recall/F1, citation precision/recall, critical support, refusal metrics, leakage counts, lift, regression, and latency. Every result includes numerator and denominator; exclusions require an enumerated reason.

- [ ] **Step 5: Remove the fake evaluator and verify wrong answers fail**

Delete `evaluate_rag.py`. Rewrite `test_rag_eval.py` so actual chat output is never assigned from expected output and deliberately corrupted traces fail the correct gate.

Run: `uv run pytest tests/evaluation/test_claim_support.py tests/evaluation/test_scoring.py tests/test_rag_eval.py -q`

Expected: all tests pass, including wrong-answer, unsupported-citation, empty-denominator, graph-no-op, and ground-truth-leakage regressions.

- [ ] **Step 6: Review and commit**

Run change detection and review. Commit:

```powershell
git add app/backend/src/hospital_ai/evaluation app/backend/tests/evaluation app/backend/tests/test_rag_eval.py app/backend/scripts/evaluate_rag.py
git commit -m "test: enforce evidence-grounded RAG scoring"
```

### Task 5: Add Explicit Ablation Controls and Exact Context Tracing

**Files:**
- Modify: `app/backend/src/hospital_ai/services/chat.py`
- Modify: `app/backend/src/hospital_ai/services/retrieval.py`
- Modify: `app/backend/src/hospital_ai/services/reasoning.py`
- Create: `app/backend/src/hospital_ai/evaluation/observer.py`
- Create: `app/backend/tests/evaluation/test_chat_observer.py`
- Modify: `app/backend/tests/test_graph_rag_chat_release_gates.py`

**Interfaces:**
- Produces: frozen `EvaluationControls(mode, graph_required, run_id)` with modes `rag_off`, `hybrid_graph_off`, `hybrid_graph_on`.
- Adds internal-only optional parameters to `ChatService.answer`: `evaluation_controls: EvaluationControls | None = None`, `evaluation_observer: EvaluationObserver | None = None`.
- Produces observer events for candidates, authorized candidates, selected context, graph execution, graph-expanded chunks, and cited chunks.

- [ ] **Step 1: Run mandatory impact analysis**

Run GitNexus upstream impact on `ChatService.answer`, `RetrievalService.hybrid_search`, the pipeline `run` methods, and Graph traversal entry points. Because `ChatService.answer` and streaming handlers are high-fanout, report the risk and affected processes before editing. If HIGH/CRITICAL, warn the user and obtain confirmation as required by repository policy.

- [ ] **Step 2: Write failing orchestration tests**

```python
@pytest.mark.asyncio
async def test_rag_off_sends_no_retrieved_context(chat_harness) -> None:
    observer = InMemoryEvaluationObserver()
    await chat_harness.answer(controls=EvaluationControls.rag_off("run-a"), observer=observer)
    assert observer.snapshot().selected_context == ()
    assert observer.snapshot().graph_ran is False


@pytest.mark.asyncio
async def test_graph_required_failure_is_not_silently_swallowed(chat_harness) -> None:
    with pytest.raises(GraphCertificationError):
        await chat_harness.answer(
            controls=EvaluationControls.hybrid_graph_on("run-c", graph_required=True),
            graph=FailingGraphService(),
        )


@pytest.mark.asyncio
async def test_observer_records_exact_prompt_context(chat_harness) -> None:
    snapshot = await chat_harness.answer_and_snapshot(mode="hybrid_graph_on")
    assert snapshot.selected_chunk_ids == snapshot.generator_context_chunk_ids
    assert set(snapshot.cited_chunk_ids).issubset(snapshot.selected_chunk_ids)
```

- [ ] **Step 3: Verify RED**

Run: `uv run pytest tests/evaluation/test_chat_observer.py tests/test_graph_rag_chat_release_gates.py -q`

Expected: missing controls/observer and silent Graph fallback failures.

- [ ] **Step 4: Implement internal controls without exposing a public bypass**

Keep public API request schemas unchanged. Evaluation code calls `ChatService` internally with frozen controls. RAG OFF bypasses retrieval and graph while still using the same guardrails/generation boundary. Graph OFF runs identical hybrid retrieval but skips traversal. Graph ON records traversal; when `graph_required=True`, traversal errors raise `GraphCertificationError` instead of logging and continuing.

Move exact reranked context selection behind a single helper so the observer records the same ordered chunks passed to `ChatGenerator`, not pre-rerank candidates.

- [ ] **Step 5: Verify and commit**

Run focused chat, citation, graph, and observer suites. Run change detection and two-stage review. Commit:

```powershell
git add app/backend/src/hospital_ai/services app/backend/src/hospital_ai/evaluation/observer.py app/backend/tests/evaluation/test_chat_observer.py app/backend/tests/test_graph_rag_chat_release_gates.py
git commit -m "backend: trace RAG ablation context"
```

### Task 6: Prove Authorization and Transport Parity

**Files:**
- Modify: `app/backend/src/hospital_ai/services/retrieval.py`
- Modify: `app/backend/src/hospital_ai/api/routes/chat_stream.py`
- Modify: `app/backend/src/hospital_ai/api/routes/rag_trace.py`
- Modify: `app/backend/src/hospital_ai/services/chat_threads.py`
- Create: `app/backend/tests/evaluation/test_authorization_matrix.py`
- Create: `app/backend/tests/evaluation/test_transport_parity.py`

**Interfaces:**
- Produces: shared `authorize_evidence_rows(session, user_id, patient_id, chunk_ids) -> tuple[AuthorizedEvidence, ...]`.
- Consumes: observer snapshot contract from Task 5.
- Produces: `TransportResult` normalization for sync, SSE, thread, and trace comparison.

- [ ] **Step 1: Run impact analysis on every existing authorization/transport symbol**

Inspect direct callers and affected execution flows. Warn before HIGH/CRITICAL edits.

- [ ] **Step 2: Write the failing Cartesian authorization matrix**

Parameterize role × document type × patient × permission state × lifecycle state × join integrity. Include active, revoked, expired, absent, soft-deleted document/page/chunk, mismatched document patient, mismatched page document, and mismatched chunk patient.

```python
@pytest.mark.parametrize("surface", ["sync", "sse", "thread", "rag_trace"])
@pytest.mark.parametrize("denial_fixture", DENIAL_FIXTURES, ids=lambda item: item.name)
async def test_denied_evidence_never_reaches_any_surface(surface, denial_fixture, transport_harness) -> None:
    result = await transport_harness.execute(surface, denial_fixture)
    assert result.selected_model_chunk_ids == ()
    assert result.returned_evidence_chunk_ids == ()
    assert result.denied is True
```

- [ ] **Step 3: Verify RED**

Run the new tests plus existing retrieval, SSE, thread, and trace tests. Expected failures must identify actual role-tag or read-time authorization gaps, not fixture errors.

- [ ] **Step 4: Centralize the full join-chain invariant**

Require active patient permission with accepted scope, exact patient equality on Document/DocumentPage/DocumentChunk, matching page-document and chunk-document joins, indexed document state, and non-deleted rows. Apply role/document-type checks after the join-chain predicate and before result ranking. Do not allow a generic `read` tag to bypass document-type isolation.

Use the same service in vector, BM25, graph chunk lookup, SSE persistence, thread evidence reads, and RAG trace reads.

- [ ] **Step 5: Establish parity**

Normalize sync and SSE results and assert identical answer policy, selected evidence IDs, cited evidence IDs, graph provenance, and safety status. Revoke permission after persistence and assert thread/trace reads no longer expose evidence.

- [ ] **Step 6: Verify and commit**

Run PostgreSQL production-shaped focused suites and all four surfaces. Run change detection and security-focused review. Commit:

```powershell
git add app/backend/src/hospital_ai/services/retrieval.py app/backend/src/hospital_ai/services/chat_threads.py app/backend/src/hospital_ai/api/routes/chat_stream.py app/backend/src/hospital_ai/api/routes/rag_trace.py app/backend/tests/evaluation
git commit -m "security: enforce RAG evidence authorization parity"
```

### Task 7: Execute A/B/C Certification and Produce Auditable Artifacts

**Files:**
- Create: `app/backend/src/hospital_ai/evaluation/runner.py`
- Create: `app/backend/src/hospital_ai/evaluation/reporting.py`
- Modify: `app/backend/scripts/run_rag_eval.py`
- Create: `app/backend/tests/evaluation/test_runner.py`
- Create: `app/backend/tests/evaluation/test_reporting.py`

**Interfaces:**
- Consumes: benchmark, observer, scoring, and chat controls from Tasks 3-6.
- Produces: `run_certification(config: EvaluationConfig) -> CertificationRun`.
- Produces: `write_artifacts(run: CertificationRun, output_dir: Path) -> ArtifactSet`.
- CLI modes: `deterministic` and `live`; deterministic is the default and requires no secrets.

- [ ] **Step 1: Write failing runner/report tests**

```python
@pytest.mark.asyncio
async def test_runner_executes_same_case_in_all_three_modes(runner, case) -> None:
    run = await runner.run_cases([case])
    assert [item.mode for item in run.case_runs] == ["rag_off", "hybrid_graph_off", "hybrid_graph_on"]
    assert len({item.question for item in run.case_runs}) == 1


def test_report_contains_denominators_and_explicit_states(certification_run, tmp_path) -> None:
    artifacts = write_artifacts(certification_run, tmp_path)
    aggregate = json.loads(artifacts.aggregate_json.read_text(encoding="utf-8"))
    assert aggregate["metrics"]["citation_precision"]["denominator"] > 0
    assert set(aggregate["gates"].values()) <= {"pass", "fail", "blocked", "not_run"}


def test_missing_case_is_a_hard_failure(runner, benchmark) -> None:
    with pytest.raises(IncompleteRunError):
        runner.finalize(benchmark=benchmark, completed=benchmark[:-1])
```

- [ ] **Step 2: Verify RED**

Run: `uv run pytest tests/evaluation/test_runner.py tests/evaluation/test_reporting.py -q`

- [ ] **Step 3: Implement runner and artifact contracts**

Pin and fingerprint corpus, benchmark, prompt, provider/model, settings, database seed, and commit. Execute every case in a fresh transaction/known seed state. Emit per-case JSONL, aggregate JSON, JUnit XML, Markdown, and configuration JSON. Preserve provider error, timeout, malformed output, blocked, and not-run as explicit states.

- [ ] **Step 4: Replace the six-case CLI**

The CLI must support:

```powershell
uv run python scripts/run_rag_eval.py --mode deterministic --benchmark data/rag_value_benchmark_v1.jsonl --output history/rag-eval/v1 --ci
uv run python scripts/run_rag_eval.py --mode live --benchmark data/rag_value_sentinel_v1.jsonl --sample-size 30 --repetitions 3 --output history/rag-eval/live
```

`--ci` exits nonzero for any mandatory gate failure, missing case, invalid denominator, leakage, or missing artifact. Live mode exits with a distinct blocked state when provider configuration is absent.

- [ ] **Step 5: Run deterministic certification and inspect failures**

Run the first command. Fix product behavior only through a new failing regression test in the appropriate earlier task module. Do not lower thresholds or edit expected facts to make the report green.

- [ ] **Step 6: Review and commit**

Run change detection and reviews. Commit:

```powershell
git add app/backend/src/hospital_ai/evaluation app/backend/scripts/run_rag_eval.py app/backend/tests/evaluation
git commit -m "test: add RAG value certification runner"
```

### Task 8: Make Certification a Real CI and Live Release Gate

**Files:**
- Modify: `.github/workflows/ci.yml`
- Create: `.github/workflows/rag-live-evaluation.yml`
- Modify: `docs/09-testing/test-plan.md`
- Create: `docs/09-testing/rag-value-certification-v1.md`
- Modify: `app/backend/data/hosp_ai_synthetic_dataset/VALIDATION_REPORT.md`

**Interfaces:**
- Consumes: deterministic and live CLI contracts from Task 7.
- Produces: required CI job `rag-value-certification` and uploaded artifacts.
- Produces: dispatch/nightly live workflow with pinned inputs and explicit blocked/not-run reporting.

- [ ] **Step 1: Write failing workflow contract tests**

Add a Python/YAML contract test that loads workflows and asserts:

```python
def test_rag_certification_job_is_mandatory(ci_workflow) -> None:
    job = ci_workflow["jobs"]["rag-value-certification"]
    assert job.get("continue-on-error") is not True
    assert "scripts/run_rag_eval.py --mode deterministic" in flatten_run_steps(job)
    assert "rag-evaluation-artifacts" in flatten_artifact_names(job)


def test_live_workflow_never_runs_on_pull_request(live_workflow) -> None:
    triggers = live_workflow[True]
    assert "pull_request" not in triggers
    assert {"workflow_dispatch", "schedule"} <= set(triggers)
```

- [ ] **Step 2: Verify RED**

Run the workflow contract test. Expected: current `rag-evaluation` uses `continue-on-error: true` and the live workflow is absent.

- [ ] **Step 3: Replace the fake CI job**

Provision PostgreSQL, install the frozen Python 3.12 backend environment, migrate/seed the canonical corpus, run deterministic certification, upload artifacts with `if: always()`, and make the summary job depend on `rag-value-certification`. Remove the old fake evaluator invocation and `continue-on-error`.

- [ ] **Step 4: Add the live lane**

Use only `workflow_dispatch` and nightly `schedule`. Require configured provider secrets at runtime; missing secrets produce a visible blocked summary and no pass badge. Record model/provider/prompt/corpus/benchmark fingerprints and execute 30 cases × 3 repetitions.

- [ ] **Step 5: Run full local verification**

Backend:

```powershell
uv run ruff check src tests scripts
uv run ruff format --check src tests scripts
uv run pytest tests/ -q --tb=short --cov=hospital_ai --cov-report=term --cov-fail-under=80
uv run python scripts/verify_contracts.py
uv run python scripts/run_rag_eval.py --mode deterministic --benchmark data/rag_value_benchmark_v1.jsonl --output history/rag-eval/v1 --ci
```

Frontend:

```powershell
bun run typecheck
bun run lint
bun run test -- --run
bun run build
```

Database and product-shaped gates:

```powershell
uv run alembic upgrade head
uv run pytest tests/evaluation/test_ingestion_certification.py tests/evaluation/test_authorization_matrix.py tests/evaluation/test_transport_parity.py -q
```

Expected: all commands pass, coverage is at least 80%, deterministic certification passes every mandatory gate, and generated artifacts have no secrets or real PHI.

- [ ] **Step 6: Final task review and commit**

Run change detection, workflow/security review, and re-review after fixes. Commit:

```powershell
git add .github/workflows docs/09-testing app/backend/data/hosp_ai_synthetic_dataset/VALIDATION_REPORT.md
git commit -m "ci: gate merges on RAG value certification"
```

## Final Whole-Branch Review and PR

- [ ] Run `git merge-base main HEAD` and generate a whole-branch review package with the subagent-driven-development review-package script.
- [ ] Dispatch a fresh most-capable final reviewer using the requesting-code-review template. Include the full spec, plan, review package, deterministic artifact paths, all recorded Minor findings, and the backend baseline history.
- [ ] Dispatch one fix agent for the complete final finding set. Re-run covering tests and re-review until no Critical/Important/P1 findings remain.
- [ ] Run GitNexus `detect_changes(scope="compare", base_ref="main", worktree="D:\\projects\\chatbot-hospital-system-rag-value-cert-v1")`; inspect every affected process and confirm scope.
- [ ] Run a secrets scan and verify that only synthetic/de-identified data is committed.
- [ ] Run the complete verification suite again after the final fix commit.
- [ ] Use the finishing-a-development-branch skill, push with upstream tracking, and create a ready PR only if deterministic certification and required tests pass. If the live provider is unavailable, state `live-provider: not_run` in the PR rather than implying certification.
- [ ] PR description includes: requirement/spec link, corpus and benchmark fingerprints, 100/200/300/50 counts, A/B/C metrics, authorization matrix result, claim-support metrics, sync/SSE/thread/trace parity, deterministic CI evidence, live-provider status, security/privacy impact, latency, and remaining limitations.
