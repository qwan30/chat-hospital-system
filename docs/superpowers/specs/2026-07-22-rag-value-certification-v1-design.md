# RAG Value Certification v1 Design

**Status:** Approved design, pending written-spec review

**Branch:** `feat/rag-value-certification-v1`

**Base:** `origin/main` at `4acadec696b7a4e4a199473de1353009459900ce`
**Date:** 2026-07-22

## 1. Purpose

PR #40 established a useful RAG safety baseline, but it did not prove that retrieval or Graph RAG materially improves chat quality. RAG Value Certification v1 adds a reproducible evidence system that answers five release questions:

1. Does patient-scoped retrieval improve answer accuracy over the same chat path with RAG disabled?
2. Does Graph RAG improve questions that genuinely require relationship traversal?
3. Are answer claims supported by the cited source passages rather than merely carrying valid evidence identifiers?
4. Can any unauthorized, revoked, expired, deleted, or mismatched evidence reach the model or a later read surface?
5. Is the 100-patient synthetic corpus sufficiently governed, clean, and stable to support repeatable evaluation?

The certification is a release gate, not a product demo. A green result must be derived from controlled ground truth and actual system output. Expected answers must never be copied into the evaluated output path.

## 2. Scope

### 2.1 In scope

- Governance of the existing 100-patient synthetic corpus and its 200 patient records.
- Removal of byte-identical duplicate corpus trees only after SHA-256 verification.
- A versioned, machine-readable corpus manifest with one record per canonical file.
- A deterministic benchmark with at least 300 cases and a manually verified 50-case subset.
- Three-mode ablation: RAG OFF, hybrid retrieval with Graph OFF, and hybrid retrieval with Graph ON.
- Retrieval, answer-quality, refusal, citation, authorization, transport-parity, and latency measurements.
- Claim-to-evidence mappings and capture of the exact context selected for the model.
- Deterministic CI release gates plus separate live-provider manual/nightly runs.
- Machine-readable artifacts and a human-readable certification report.

### 2.2 Out of scope

- Adding Synthea or increasing the patient count beyond 100.
- Using real PHI or production patient data.
- Treating public guidelines or drug reference data as patient evidence before provenance and license review.
- Training or fine-tuning a model.
- Replacing the current chat UI or graph visualization.
- Claiming clinical validation, medical-device approval, or production readiness from synthetic evaluation alone.

## 3. Binding Principles

1. **Ground truth is independent of model output.** Expected facts, allowed evidence, forbidden evidence, relations, and refusal policy are derived from canonical source records and reviewer annotations.
2. **Authorization precedes ranking and generation.** Evidence that fails any ownership, lifecycle, role, or permission check must not be ranked, graph-expanded, sent to the model, persisted as cited evidence, or returned through trace/thread APIs.
3. **Citation existence and citation support are separate.** A valid evidence ID is insufficient; the cited span must support the associated answer claim.
4. **Graph value is causal.** Graph RAG is credited only when Graph ON improves the graph-only subset over the identical Graph OFF configuration and graph-expanded evidence is selected and cited.
5. **Deterministic and live evidence are separate lanes.** CI must not depend on provider secrets. Live-provider results are versioned artifacts with pinned model, prompt, corpus, and run settings.
6. **No silent success.** Missing cases, missing annotations, swallowed ingest failures, provider fallback, graph fallback, or incomplete metric denominators fail the relevant gate.
7. **Patient and public knowledge remain separated.** Unreviewed public knowledge is quarantined and excluded from patient-evidence retrieval at runtime.

## 4. System Architecture

The certification system consists of six bounded components.

### 4.1 Corpus release validator

The validator scans the canonical corpus and emits a versioned release manifest. Each file record contains:

- relative canonical path;
- SHA-256 digest and byte size;
- patient ID;
- document ID or stable source record ID;
- document type and MIME type;
- generator name and version;
- source classification;
- synthetic-data marker;
- license or license-review state;
- expected ownership and record linkage;
- quarantine state;
- manifest schema version.

The validator rejects:

- duplicate digests in canonical patient data unless explicitly declared as intentional fixtures;
- orphan files or manifest records;
- null or mismatched patient ownership;
- path traversal or files outside the canonical root;
- unsupported MIME/extension combinations;
- public knowledge marked as runtime-approved without provenance and license approval;
- a manifest whose declared counts differ from the filesystem.

The nested duplicate dataset tree may be removed only when every candidate file is paired with a canonical file having the same SHA-256 digest. The deletion evidence is retained as a generated comparison artifact, not as a second data copy.

### 4.2 Ingestion certification adapter

The existing ingestion path remains the production path. A certification adapter observes it and produces durable per-file results:

- accepted, rejected, failed, or skipped state;
- source fingerprint;
- generated document, page, and chunk identifiers;
- embedding/index generation identity;
- error category without PHI-bearing raw exception leakage;
- retry attempt and terminal state.

A clean index run must account for every canonical patient file. A second run with the same source fingerprints must be idempotent: no duplicate documents, pages, chunks, graph facts, or embeddings. Failed or partially indexed inputs must not be reported as successful or permanently skipped.

### 4.3 Golden benchmark registry

The benchmark registry stores at least 300 versioned cases. A case is valid only when it contains:

- stable case ID and benchmark schema version;
- corpus version and patient ID;
- actor ID or actor fixture, role, and permission state;
- question and case category;
- expected atomic facts or slots;
- allowed document/page/chunk IDs;
- forbidden document/page/chunk IDs;
- expected claim-to-evidence mappings;
- required graph relations and graph seed evidence when applicable;
- expected answer policy: answer, scoped refusal, or safe no-evidence response;
- critical-fact markers;
- annotation provenance and review state.

The minimum benchmark composition is:

| Category | Minimum cases | Purpose |
| --- | ---: | --- |
| Single-hop patient facts | 70 | Basic retrieval and answer usefulness |
| Multi-document synthesis | 50 | Cross-record aggregation |
| Temporal conflict/latest-state | 35 | Correct date/version selection |
| Graph-only or multi-hop | 45 | Causal Graph RAG value |
| Overlapping cross-patient facts | 30 | Patient isolation under confusing similarity |
| Permission adversarial | 45 | Role, lifecycle, and join-chain denial |
| Safe refusal/no evidence | 25 | Refusal behavior and false-refusal control |
| **Total** | **300** | Required minimum |

At least 50 cases, including every category and all critical-clinical-fact patterns, receive manual review. Generated cases may expand coverage, but generation logic cannot infer ground truth from a model answer. The 50 reviewed cases form a frozen sentinel subset and cannot be silently regenerated.

### 4.4 Evaluation runner and ablation controller

Every answerable benchmark question is executed through the same chat orchestration under three configurations:

| Mode | Retrieval | Graph expansion | Purpose |
| --- | --- | --- | --- |
| A: RAG OFF | Disabled | Disabled | Model/prompt baseline |
| B: Hybrid Graph OFF | Vector + BM25/hybrid | Disabled | Retrieval contribution |
| C: Hybrid Graph ON | Same as B | Enabled | Incremental graph contribution |

All non-ablation variables are pinned: corpus version, database seed, actor, permissions, prompt version, model/provider configuration, retrieval limits, thresholds, graph depth, and random seed where supported. The runner records configuration fingerprints so results from different configurations cannot be combined.

Graph ON is considered active only when the trace proves that graph traversal ran. A graph-only success additionally requires at least one authorized graph-expanded chunk to be selected into model context and cited by a supported claim. A graph node shown in the UI or present only in diagnostic candidates earns no credit.

### 4.5 Evidence and authorization observer

The observer captures four distinct sets for each query:

1. retrieved candidates;
2. authorization-filtered candidates;
3. exact chunks selected for model context;
4. chunks cited by the final answer.

Each set carries stable document, page, chunk, patient, retrieval-method, score-scale, and graph-origin metadata. Context capture stores a digest plus a test-artifact representation suitable for synthetic data; production logging must not expand PHI exposure.

Answer text is decomposed into evaluable claims. Each claim records its cited evidence IDs and support verdict:

- `supported`: the cited span entails or directly contains the atomic fact;
- `unsupported`: the citation exists but does not support the claim;
- `contradicted`: the cited span conflicts with the claim;
- `uncited`: a factual claim has no citation;
- `not_applicable`: non-factual connective or safety language.

Deterministic cases use expected atomic facts and source spans for claim support. The live-provider lane may add a judge, but judge output cannot override deterministic critical-fact, authorization, or citation failures.

Authorization evaluation covers the Cartesian product that is meaningful for each fixture:

- role and document type;
- actor and patient;
- active, revoked, expired, and absent permission;
- active and soft-deleted document/page/chunk;
- matching and mismatched patient-document-page-chunk joins;
- sync chat, SSE chat, thread reads, and RAG trace reads.

The required invariant is zero unauthorized chunks in selected model context. Read-time authorization is re-applied to persisted thread and trace evidence so later permission revocation cannot expose stale content.

### 4.6 Scoring and reporting engine

The scoring engine emits per-case JSONL, aggregate JSON, JUnit-compatible gate results, and a Markdown certification report. Every metric includes numerator, denominator, excluded-case count, and exclusion reason. Empty denominators fail instead of defaulting to `1.0`.

Primary metrics:

- Retrieval Recall@5 and MRR@5 against allowed ground-truth chunks.
- Atomic fact/slot precision, recall, and F1 for answers.
- Citation precision: supported cited claims divided by cited factual claims.
- Citation recall: supported cited required facts divided by required factual claims.
- Critical-fact support rate.
- Safe-refusal recall and false-refusal rate.
- Unauthorized-context count and denial rate by adversarial category.
- Transport parity across answer policy, selected evidence, citations, and safety metadata.
- RAG lift in percentage points: mode B or C answer accuracy minus mode A.
- Graph lift in percentage points: mode C minus mode B on the graph-only subset.
- Graph semantic regression: mode C minus mode B on non-graph semantic cases.
- Severe hallucination count.
- End-to-end latency distribution, including p50, p95, and maximum.

## 5. Release Gates

Certification passes only when all mandatory gates pass on the declared corpus and benchmark versions.

### 5.1 Corpus gates

- Exactly 100 canonical patients and 200 canonical patient records.
- Zero unapproved duplicate SHA-256 digests.
- Zero orphan files or manifest records.
- Zero null or mismatched ownership records.
- 100% canonical files reach a declared terminal ingest state.
- 100% intended patient files index successfully.
- Re-running unchanged ingestion produces zero duplicate derived records.
- Unreviewed public guideline/drug data contributes zero runtime patient evidence.

### 5.2 Value gates

- RAG ON answer accuracy improves by at least 20 percentage points over RAG OFF.
- Graph ON improves answer accuracy by at least 15 percentage points over Graph OFF on the graph-only subset.
- Graph ON regresses by no more than 2 percentage points on ordinary semantic cases.
- Graph-only credited answers include selected and cited graph-expanded evidence.

### 5.3 Retrieval and answer gates

- Recall@5 is at least 90%.
- MRR@5 is at least 85%.
- Answer fact/slot F1 is at least 90%.
- Safe-refusal recall is 100%.
- False-refusal rate is at most 5%.
- Severe hallucination count is zero.

### 5.4 Evidence and authorization gates

- Unauthorized chunks sent to the model: zero.
- Denial rate for revoked, expired, soft-deleted, and mismatched join fixtures: 100%.
- Citation precision is at least 98%.
- Citation recall is at least 95%.
- Critical clinical facts supported by evidence: 100%.
- Sync/SSE/thread/RAG-trace parity: 100% for applicable cases.

### 5.5 Live-provider gate

- A representative stratified set of 30 cases runs three times each.
- Model, provider, prompt, corpus, retrieval configuration, and run timestamp are recorded.
- p95 end-to-end latency is at most 30 seconds.
- No live run may weaken the zero-leakage, denial, critical-fact, or severe-hallucination gates.
- Provider unavailability is reported as `not_run` or `blocked`, never as pass.

## 6. CI and Execution Lanes

### 6.1 Mandatory deterministic CI

CI runs without external provider secrets and blocks merge when:

- corpus/manifest validation fails;
- benchmark schema or coverage validation fails;
- any deterministic metric misses its threshold;
- any case is silently skipped;
- the evaluator detects expected-output substitution, constant scoring, or an empty denominator;
- the evaluation job is marked `continue-on-error`;
- required artifacts are absent.

The deterministic provider must produce output through the real chat/evidence orchestration boundary. It may make generation reproducible, but it must not receive expected answers, expected facts, or expected citation mappings as input.

### 6.2 Manual/nightly live-provider lane

The live-provider lane is non-secret-dependent for pull-request CI and runs manually or nightly in an authorized environment. It publishes immutable artifacts keyed by commit, corpus version, benchmark version, provider, model, and prompt version. A pull request may state that deterministic certification passed while live certification is pending; it must not collapse those states into a single green claim.

## 7. Error Handling and Failure Semantics

- Corpus validation errors identify the file and rule while avoiding raw sensitive content.
- Ingestion failures remain durable and retryable; no broad exception handler may convert failure to success.
- Graph traversal errors fail graph-required cases and are visible in traces; silent fallback to Graph OFF is forbidden for graph certification.
- Provider errors, timeouts, and malformed output are separate result states and remain in metric denominators according to the metric contract.
- Missing authorization metadata fails closed.
- Missing claim/citation annotations invalidate the case before execution.
- A changed corpus or benchmark fingerprint invalidates comparisons against prior runs.

## 8. Security and Privacy

- Only synthetic or de-identified fixtures are permitted.
- No secrets, provider tokens, or real patient identifiers are stored in benchmark artifacts.
- Authorization filters are applied before graph expansion, before final context selection, and again on persisted evidence reads.
- Raw SQL and ORM retrieval paths share executable permission invariants.
- Test artifacts containing synthetic context are explicitly labeled synthetic and are not reused as production logging policy.
- Benchmark reports expose stable synthetic IDs and minimal evidence excerpts needed for review.

## 9. Test Strategy

Implementation follows strict red-green-refactor TDD. Each workstream has focused unit tests plus integration gates:

1. **Corpus tests:** manifest schema, SHA-256 pairing, duplicate detection, ownership validation, quarantine, and deterministic output.
2. **Ingestion tests:** complete accounting, durable failures, source fingerprinting, retry, and idempotent re-indexing.
3. **Benchmark tests:** schema validation, exact category counts, sentinel immutability, no ground-truth leakage, and deterministic generation.
4. **Evaluator tests:** deliberately wrong answers, unsupported citations, empty denominators, missing cases, constant-score detection, and A/B/C lift calculations.
5. **Authorization tests:** role/document/patient/lifecycle/join-chain matrix across sync, SSE, thread, and trace surfaces.
6. **Graph tests:** traversal execution, patient-scoped expansion, selected graph context, cited graph evidence, graph lift, and semantic non-regression.
7. **End-to-end tests:** corpus seed to retrieval to generation to citations to report artifacts on the production-shaped orchestration path.

Mocked browser output and a stub-only SQLite path are useful development evidence but are not sufficient for live release certification. PostgreSQL production-shaped tests are required for raw SQL, vector, BM25, and lifecycle behavior.

## 10. Deliverables

- Canonical corpus tree with verified duplicate removal.
- Versioned per-file corpus manifest and validation report.
- Deterministic ingestion certification and idempotency artifacts.
- Versioned 300+ case benchmark and frozen 50-case reviewed sentinel subset.
- A/B/C evaluation runner using actual chat orchestration output.
- Claim-level evidence support evaluator.
- Authorization and transport-parity matrix tests.
- Deterministic CI gate with no `continue-on-error`.
- Manual/nightly live-provider workflow and artifact schema.
- Human-readable RAG Value Certification report with explicit pass, fail, blocked, and not-run states.

## 11. Completion Criteria

The implementation is complete when:

1. All deterministic release gates in Section 5 pass on a clean, reproducible environment.
2. Backend, frontend, lint, format, type, contract, migration, and focused PostgreSQL tests pass.
3. The evaluator has regression tests proving that fake outputs, constant scores, unsupported citations, graph no-ops, authorization leakage, and incomplete denominators fail.
4. GitNexus change detection shows only intended symbols and execution flows before each commit and before final review.
5. Per-task spec and code-quality reviews have no open Critical or Important findings.
6. A final independent whole-branch review has no P1-or-higher findings.
7. The branch is pushed and a pull request documents corpus version, benchmark version, deterministic results, live-provider status, security impact, and all remaining limitations.

## 12. Baseline Verification Note

The isolated branch was created from current `origin/main`. Frontend baseline verification passed with 86 tests, successful TypeScript typecheck, and zero lint errors; three lint warnings pre-existed. Backend frozen environment provisioning was not completed because drive C had approximately 0.01 GB free and a redirected frozen `uv` sync on drive D exceeded the ten-minute command limit. This is an environment-provisioning limitation, not a passing or failing backend baseline result. Backend implementation must not begin until a Python 3.12 environment can run the clean baseline, or the user explicitly accepts a narrower verification lane.
