# CDI V2 promotion to main and production certification plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** Promote the CDI V2 stack to **main** through reviewable pull requests so that the three contractual capabilities work together in a deployed environment: (1) upload, OCR, and indexing, (2) chat/RAG with validated citations, and (3) permission-filtered GraphRAG. After that promotion, resolve and recertify every material finding recorded by the 2026-08-14 automation plan and production click-through report.

**Architecture:** Use one ordinary checkout and two sequential branches. First merge the complete CDI V2 integration candidate into an integration branch with a no-commit merge, reconcile the complete schema and runtime contract, prove the three vertical slices against synthetic data, then merge that PR to main. Only after the exact main SHA is known, create a second audit-remediation branch from it and correct the production data-source, browser-flow, error-handling, and automation gaps. Runtime proof must always travel from a synthetic upload through persistent pages/chunks/vectors/graph evidence to an authorized cited answer; a fixture or static dashboard counter is never proof.

**Tech Stack:** FastAPI, SQLAlchemy/Alembic, PostgreSQL/pgvector, local or R2 object storage, worker queue, PyMuPDF-first OCR with optional PaddleOCR, TanStack Start/React/TypeScript, Bun, Vitest, Playwright, pytest, GitHub Actions, GitNexus.

## Global Constraints

- This is an explicit **no-worktree** execution plan. Use the existing checkout only and sequential Git branches; do not invoke git worktree, stash, reset --hard, checkout --, force-push, or --no-verify.
- Preserve the pre-existing dirty files exactly as found: AGENTS.md, CLAUDE.md, .tmp-ci-* directories, .tmp-pytest-retrieval, the two synthetic E2E files, and the existing untracked click-through report. Stop if a merge conflicts with any of them; ask the owner rather than deleting, staging, or overwriting them.
- Do not commit directly to main. Do not declare a PR merged because a compare URL exists. Re-query GitHub and record the merge commit SHA after each PR.
- Live facts at planning time are inputs, not permanent truth: main is 7fdf2b5c281a03f411e44614d925000bdd67a004; the candidate is origin/ci/cdi-v2-e2e-integration at adb6cda62babd429b0dd4ba32dd905605fec4f6b; merge base is 6794777f48862a4d1278b3bd4e83e93e7514d027; divergence is 41 commits only on main and 133 only on candidate. Re-read all four values immediately before implementation.
- PR #90 is already on main, while the implementation chain #91 through #103 is not. Treat the candidate as one coherent migration chain; do not reconstruct it with ad-hoc cherry-picks.
- Every new or changed function/class/method requires GitNexus impact analysis before editing. Run GitNexus detect_changes before every commit and compare against the branch base.
- All fixtures, logs, screenshots, DB dumps, and browser inputs must be synthetic/de-identified. No clinical data or keys may enter source control, reports, screenshots, terminal output, or PR bodies. Rotate the DeepSeek key previously exposed in conversation before it is ever used again; credential rotation itself requires the secret owner.
- A green focused test, TypeScript compilation, a Playwright --list result, or a rendered fixture is only a narrow check. None is a production release certificate.

## Evidence and Decision Record

| Item | Planning-time evidence | Execution requirement |
|---|---|---|
| Candidate shape | #91–#103 contain 653 changed files in aggregate and are absent from main; candidate adds CDI routes, UI, migrations, tests, evaluations, and generated artifacts. | Merge the candidate once into a disposable integration state, make an explicit include/exclude disposition for every conflicted or generated path, then create one reviewed merge commit on the feature branch. |
| Upload contract | Current main UI calls legacy POST /documents. Candidate UI uses POST /documents/upload-sessions, authenticated PUT /upload-objects/{objectKey}, then POST /documents/{documentId}/uploads/{uploadId}/finalize with idempotency. | Select exactly one canonical UI path. Keep legacy only as a tested adapter or remove its UI reachability. Both paths may not independently enqueue/index the same upload. |
| Schema risk | A candidate filename named cdi_v2_0004_add_build_authorized_revision_state declares Alembic revision cdi_v2_0005, while cdi_v2_0004_cleanup_legacy_search_artifacts declares cdi_v2_0004; the following cdi_v2_0006 forward migration restores model-owned objects. | Establish one linear Alembic head from current main by validating headers and directed lineage, not filenames; rename the misleading candidate-only filename without altering its revision ID, preserve historical revisions, and prove upgrade from fresh and representative pre-CDI databases. |
| Production evidence | The 2026-08-14 click-through report observed Failed to fetch for PDF/TXT/HL7 uploads, 0 indexed documents, no-evidence chat, and a one-node/zero-edge graph. | Repair the causal runtime path and repeat actual browser interactions at the deployed exact SHA with artifacts. Do not use seeded counters to call these cases passed. |

## Planned File Structure

The first PR is expected to reconcile the candidate files below, not blindly accept every file from it.

~~~text
app/backend/
  alembic/versions/                         # linearized CDI migration chain
  src/hospital_ai/api/routes/
    documents.py                            # legacy compatibility decision
    document_uploads.py                     # create / PUT / finalize contract
    document_revisions.py
    document_generations.py
    document_graph.py
    chat_stream.py
  src/hospital_ai/services/
    upload_sessions.py, ocr.py, ocr_routing.py, generations.py
    retrieval.py, evidence_scope.py, claim_validation.py, validated_stream.py
    graph_index.py, graph_query.py, graph_rag.py
  src/hospital_ai/workers/
    jobs.py, extraction_jobs.py, generation_jobs.py, queue.py
  tests/cdi_v2/ and tests/test_*            # deterministic acceptance tests

app/frontend/
  src/components/hms/document-upload/DocumentUploadFlow.tsx
  src/components/hms/document-upload/UploadStatePanel.tsx
  src/components/hms/document-workspace/DocumentWorkspace.tsx
  src/components/hms/{ChatMessage,CitationChip,EvidenceRail,GraphCanvas,GraphFilters}.tsx
  src/lib/api/{documents,document-revisions,document-graph,graph}.ts
  src/lib/stream-client.ts
  src/routes/_app.{documents.upload,documents.$documentId,documents.$documentId.review,chat.index,graph.patients.$patientId}.tsx
  e2e/cdi-v2-document-intelligence.spec.ts

docs/09-testing/
  full-project-automation-plan-2026-08-14.md
  production-click-through-report-2026-08-14.md
  evidence/c01-c50-registry.yaml           # test-to-evidence contract for every case
  production-certification-<exact-main-sha>.md  # created only from real rerun artifacts

.github/workflows/ci.yml
~~~

The following paths are excluded from the core code PR unless a reviewer approves a dated, reproducible release-evidence reason: app/backend/artifacts/**, app/backend/eval_output.txt, app/backend/test_results.txt, app/backend/fix.py, app/backend/patch_new_migration.py, and one-off generated datasets. A release artifact belongs in an immutable CI run or a dated certification report, never as a stale claim carried across commits.

---

## Phase A — establish a safe merge composition

### Task 1: Freeze provenance and create the first branch without disturbing existing work

**Files:** No product file changes. Create only a dated evidence directory outside version control if ignored by the repository, and the PR branch metadata.

**Consumes:** current checkout, origin/main, origin/ci/cdi-v2-e2e-integration.

**Produces:** a provenance record with remote SHAs, merge base, clean/dirty manifest, PR state #89–#103, and an approved branch base.

- [ ] Run git status --short, git branch --show-current, git remote -v, git fetch --prune origin, git rev-parse origin/main, git rev-parse origin/ci/cdi-v2-e2e-integration, git merge-base, and git rev-list --left-right --count. Compare the values with the table above; stop if candidate or main changed until the review scope is refreshed.
- [ ] Record every pre-existing dirty path and verify that the plan file is the only file introduced by this planning task. Do not stage anything except exact files owned by the later implementation task.
- [ ] Query GitHub for PR #89–#103: number, state, base/head refs, mergeCommit/mergeable, head SHA, checks, and review threads. Create a machine-readable PR manifest with the exact fetch time; no unaudited PR is assumed subsumed.
- [ ] Create and check out feat/cdi-v2-main-integration from the freshly fetched origin/main only after the dirty-overlap check passes. This branch is the sole place for the no-commit merge; main remains untouched.
- [ ] Create a failing guard script/test in app/backend/tests/cdi_v2/test_promotion_provenance.py that reads a checked-in promotion manifest and rejects missing main/candidate/base SHAs, a direct-main branch, or banned generated surfaces in the intended change list.
- [ ] Run python -m pytest tests/cdi_v2/test_promotion_provenance.py -q from app/backend. Expected initial result: FAIL until the manifest and exclusions are encoded.
- [ ] Implement the smallest manifest format under docs/09-testing/evidence/ and its validator. It must contain only public SHAs, PR numbers, path disposition, and test command identifiers — never tokens, URLs with credentials, patient identifiers, or raw synthetic contents.
- [ ] Re-run the provenance test. Expected result: PASS. Run git diff --check and GitNexus detect_changes against origin/main, then commit only the manifest/validator/test as chore: record cdi v2 promotion provenance.

### Task 2: Make an explicit candidate file-disposition manifest before committing the merge

**Files:** docs/09-testing/evidence/cdi-v2-promotion-manifest.json; app/backend/tests/cdi_v2/test_promotion_provenance.py; candidate conflict surfaces listed in the file structure.

**Consumes:** the no-commit merge index and the candidate/main diff.

**Produces:** a path-level decision of include, adapt, or exclude; no surprise generated or workflow content.

- [ ] Start the controlled composition with git merge --no-commit --no-ff origin/ci/cdi-v2-e2e-integration. If Git reports a conflict touching a pre-existing dirty file, abort the merge only after confirming it affects the just-started merge state, restore neither user change nor unrelated untracked path, and ask for direction.
- [ ] Produce a failing parametrized test for the manifest. It must reject a path categorized as include when it is an artifact/one-off script, reject duplicate migration **revision headers** or a filename/header ordinal mismatch, and reject any secret-like key in documentation or examples.
- [ ] Run the test; expected result: FAIL while the candidate paths are unclassified.
- [ ] Classify every path: **include** runtime contracts and their tests; **adapt** current-main integrations such as CI, router wiring, legacy documents route, deployment configuration, and migrations; **exclude** stale outputs/one-off repair scripts. Each adapted file needs an owner, reason, and verification command.
- [ ] For each conflict, inspect both parents and choose a semantic resolution. Do not use blanket ours/theirs. Preserve main's post-PR #90/#104/#106–#110 changes unless a candidate equivalent demonstrably supersedes them.
- [ ] Re-run the manifest test, git diff --check, secret scanner if configured, and git diff --name-only --diff-filter=ACMRT origin/main. Expected result: PASS; the path list equals the manifest's include/adapt union.
- [ ] Run GitNexus detect_changes with base_ref main. Resolve a HIGH/CRITICAL blast-radius warning before continuing. Keep the merge uncommitted until Tasks 3–7 pass the contract gates.

### Task 3: Linearize and prove the database migration contract

**Files:** app/backend/alembic/env.py; app/backend/alembic/versions/cdi_v2_0001_add_revision_generation_schema.py through cdi_v2_0006_restore_model_owned_schema.py; any new forward-only merge revision; app/backend/tests/cdi_v2/test_graph_migration.py; a new app/backend/tests/cdi_v2/test_promotion_migrations.py.

**Consumes:** current main schema plus candidate's revision/generation, graph provenance, stream state, cleanup, and restoration migrations.

**Produces:** exactly one Alembic head; repeatable upgrade on empty and pre-CDI schema; models and schema converge.

- [ ] Before changing any migration symbol, run GitNexus impact on the affected migration/model symbols and report HIGH/CRITICAL results in the PR.
- [ ] Write failing tests that create an empty database and a snapshot at current-main head, execute alembic upgrade head, then assert: exactly one head; Document/DocumentUpload/Revision/Generation/Graph provenance tables exist; document_chunks search_vector and vector index shapes match models; all expected constraints exist; no orphan legacy graph relation is created.
- [ ] Add a test that parses every Alembic revision header and fails on duplicate revision strings, a missing down_revision target, a cycle/disconnected lineage, an unexpected branch label, a filename/header ordinal mismatch, or a downgrade that drops data needed by the previous main. The test must prove the candidate-only filename cdi_v2_0004_add_build_authorized_revision_state declares cdi_v2_0005 and is renamed without changing revision ID.
- [ ] Run python -m pytest tests/cdi_v2/test_promotion_migrations.py tests/cdi_v2/test_graph_migration.py -q. Expected initial result: FAIL on header graph, filename/header mismatch, disconnected lineage, or schema drift.
- [ ] Add only forward migrations needed to join heads or repair model-owned objects. Never rewrite a migration that may have reached any environment; preserve candidate's cdi_v2_0006 restoration rationale where its predecessor removed still-modelled search artifacts.
- [ ] Run alembic heads, alembic history --verbose, alembic upgrade head on both fixtures, and the focused migration tests. Expected result: one head and all assertions green.
- [ ] Run python scripts/verify_contracts.py and capture version/DB dialect in the evidence record. A SQLite pass does not replace a PostgreSQL/pgvector pass; execute both where CI/deployment support them.
- [ ] Run GitNexus detect_changes and commit only the resolved merge plus migration/test changes after Tasks 4–7 have passed; do not create an intermediate migration-only merge commit that CI could deploy.

## Phase B — prove the three connected production capabilities

### Task 4: Make upload → OCR → index one canonical, observable state machine

**Files:** app/backend/src/hospital_ai/api/routes/{documents,document_uploads,document_generations}.py; app/backend/src/hospital_ai/services/{upload_sessions,ocr,ocr_routing,generations,storage}.py; app/backend/src/hospital_ai/workers/{jobs,extraction_jobs,generation_jobs,queue}.py; app/frontend/src/components/hms/document-upload/{DocumentUploadFlow,UploadStatePanel}.tsx; app/frontend/src/lib/api/documents.ts; app/frontend/src/routes/_app.documents.upload.tsx; app/backend/tests/cdi_v2/test_{upload_sessions,extraction_worker,generation_api,generation_worker,ocr_routing,legacy_parity}.py; app/frontend/src/components/hms/document-upload/*.test.tsx.

**Consumes:** immutable upload session, authenticated storage object, finalize request, job queue, extracted pages, chunks, embeddings, and graph entities.

**Produces:** one document generation with an auditable terminal status and source hash; an authorized user can see the matching state without polling a different source.

- [ ] Run GitNexus impact before editing process_document, OcrService, upload session handlers, or their V2 equivalents; document direct callers including legacy upload/retry paths.
- [ ] Write failing API tests for the canonical sequence: authorized create with Idempotency-Key returns 201; PUT rejects a missing If-None-Match, mismatched MIME, wrong byte length, wrong object key, and duplicate object; finalize is idempotent and enqueues exactly once.
- [ ] Write failing worker tests with a synthetic text PDF, DOCX, HL7 text, and image-only scan. Assert extracted page provenance, source SHA-256, chunk/vector persistence, graph-index handoff, retry behavior, and terminal status. The image-only case must be ready_with_warnings or a documented deterministic failure when PaddleOCR is unavailable — never silently indexed empty.
- [ ] Write a failing compatibility test that either proves POST /documents delegates to the same generation state machine or proves the frontend has no remaining reachable legacy upload action. It must fail if one physical file can make two jobs/documents.
- [ ] Run the focused pytest set. Expected initial result: FAIL on route divergence, state semantics, or V2 fixture gaps.
- [ ] Implement the minimum adapter/removal needed for one canonical path. Retain API backwards compatibility only when a versioned client uses it; return a safe migration response otherwise. Normalize status vocabulary and trace ID across create, PUT, finalize, extraction, indexing, retry, and terminal events.
- [ ] Implement frontend state transitions: local upload uses the authenticated V2 PUT endpoint, R2 uses a presigned destination, and the UI shows queued/processing/ready/ready_with_warnings/failed with a sanitized actionable message. The UI must not display "success" before finalize and terminal completion.
- [ ] Add a deterministic test double for OCR/embedding/queue; no test may call a paid provider or read external PHI. Re-run focused backend and frontend tests. Expected result: PASS.
- [ ] Run a real local browser journey with a synthetic PDF and a synthetic HL7 file: choose patient, create session, upload, finalize, observe terminal processing, open document workspace, and verify the page/chunk count and source hash against the API. Save ordered network/SSE/worker trace IDs and screenshots as non-secret artifacts.

### Task 5: Prove Chat/RAG/citation validates before emission and before persistence

**Files:** app/backend/src/hospital_ai/api/routes/chat_stream.py; app/backend/src/hospital_ai/services/{retrieval,evidence_scope,claim_validation,validated_stream,permissions,chat_threads}.py; app/backend/src/hospital_ai/core/interfaces.py; app/frontend/src/lib/stream-client.ts; app/frontend/src/components/hms/{ChatMessage,CitationChip,EvidenceRail}.tsx; app/frontend/src/routes/_app.chat.index.tsx; app/backend/tests/{test_chat_stream_citation_contract,test_chat_stream_endpoint,test_chat_citations,test_streaming,test_audit_2026_05}.py; app/backend/tests/cdi_v2/test_{claim_validation,cross_path_evidence_scope,evidence_scope}.py; frontend component tests.

**Consumes:** permission-filtered retrieved chunks, graph-enriched evidence, provider tokens, claim/citation validator, SSE stream, chat message/audit persistence.

**Produces:** a final answer whose every citation points to returned authorized evidence, or a safe no-evidence/denied response with no unauthorized chunk sent to the LLM.

- [ ] Run GitNexus impact on _apply_stream_completion, retrieval entry point, EvidenceScope/validator symbols, and the client stream parser before editing. Treat a HIGH/CRITICAL result as a stop-and-review event.
- [ ] Add failing tests C01–C10: exact synthetic fact retrieval, page/chunk citation binding, irrelevant chunk rejection, citation deduplication, conflict disclosure, source precedence, absent evidence refusal, and persistence of only validated retrieved evidence.
- [ ] Add failing tests C11–C20 with an instrumented stub LLM that records its prompt: unauthenticated, wrong organization, wrong patient, role denial, revoked/expired session, soft-deleted document, mismatched document/page/chunk chain, attachment scope, and malformed authorization relation. Each denial must assert the captured LLM evidence is empty.
- [ ] Add failing tests C31–C40 for ordered SSE states, exactly one terminal event, cancellation during retrieval/streaming, provider timeout/rate limit/malformed chunk, validator rejection, persistence outcome, and equivalence of stream/non-stream final citation contracts. Raw exception text must never be emitted.
- [ ] Run the focused tests. Expected initial result: FAIL wherever candidate stream events, legacy code, and UI parsing disagree.
- [ ] Implement a single validated completion path: accumulate model output, validate claims/citation IDs against the authorized evidence scope, persist an outcome, then emit a terminal safe response. A client disconnect may stop delivery but cannot create a second terminal event or persist unvalidated evidence.
- [ ] Update the UI stream parser and evidence rail so it renders only final validated citations; it must preserve event order, discard late events after terminal, provide an accessible error/retry state, and never render server raw JSON.
- [ ] Re-run the tests and a local browser chat from the document uploaded in Task 4. The answer must quote the seeded fact only through citation metadata that matches its document/page/chunk/source hash. Save the ordered event log, thread ID, audit event, prompt-capture assertion result, and screenshot.

### Task 6: Prove GraphRAG is source-backed, scope-filtered, and coherent with vector RAG

**Files:** app/backend/src/hospital_ai/api/routes/{document_graph,graph}.py; app/backend/src/hospital_ai/services/{graph_index,graph_query,graph_rag,retrieval,evidence_scope}.py; app/backend/src/hospital_ai/db/{clinical_graph,models}.py; app/frontend/src/components/hms/{GraphCanvas,GraphFilters,GraphExplanationPanel}.tsx; app/frontend/src/lib/api/{document-graph,graph}.ts; app/frontend/src/routes/_app.graph.patients.$patientId.tsx; app/backend/tests/{test_graph_rag_chat_release_gates,test_graph_endpoint}.py; app/backend/tests/cdi_v2/test_{graph_index,graph_query,document_graph_api,cross_path_evidence_scope}.py; frontend graph tests.

**Consumes:** page/chunk provenance from Task 4, graph nodes/edges, request scope, vector evidence, query planner, citation validator.

**Produces:** authorized graph traversal evidence with provenance, merged/deduplicated with vector evidence, or an explicit empty/error/denied result.

- [ ] Run GitNexus impact on graph index/query/RAG handlers and on any shared retrieval/evidence-scope symbol before edits.
- [ ] Write failing C21–C30 tests: one-hop and two-hop traversal; top-k/limit; empty graph; deleted node/edge; out-of-scope patient/doc/page/chunk; mismatched provenance; node without source; conflicting source precedence; vector+graph merge and citation deduplication.
- [ ] Instrument the graph-enrichment path to assert it re-enters the same permission-filtered evidence scope before an LLM sees text. A graph edge alone must never authorize its source content.
- [ ] Write failing API and UI tests for loading, retry, patient switch, missing graph, 4xx/5xx/malformed payload, node selection, source detail, and escaped script-like labels. Assert no stale previous-patient graph remains visible.
- [ ] Run the focused tests. Expected initial result: FAIL if the graph returns a fixture independent of the indexed document or bypasses scope.
- [ ] Implement source/provenance checks at node creation and traversal; merge graph/vector candidates by stable chunk identity before citation validation. Return typed empty/error states instead of a fabricated graph.
- [ ] Update GraphCanvas/filters/explanation panel to expose count, scope, selected-node provenance, empty/error/retry, and accessible labels. Do not claim a clinical relationship without a source citation.
- [ ] Re-run focused tests and a real browser journey from Task 4 data: open the same patient graph, select a source-backed node, ask a graph-enriched chat question, and verify its citation resolves to the uploaded document. Save screenshot, API payload, trace IDs, and citation linkage.

### Task 7: Turn the three vertical slices into non-flaky CI gates and merge PR A

**Files:** .github/workflows/ci.yml; app/backend/scripts/{verify_cdi_v2_release,verify_contracts}.py; app/backend/tests/cdi_v2/acceptance/harness.py; app/frontend/e2e/cdi-v2-document-intelligence.spec.ts; app/frontend/e2e/fixtures/api-mocks.ts; docs/09-testing/evidence/{c01-c50-registry,cdi-v2-core-gate-<sha>}.{yaml,json}.

**Consumes:** the passing core tests, local database/services, browser fixture, and branch diff.

**Produces:** CI-enforced deterministic core gates and PR A evidence tied to its head SHA.

- [ ] Write a failing release-gate test that consumes the checked-in C01–C50 registry and a JSON evidence schema. The registry maps each ID to synthetic fixture hash, actor role, API/UI steps, expected assertion, test source, runner command, and artifact schema. The verifier rejects missing/duplicate IDs, head SHA mismatch, skipped browser lane, fixture-only graph proof, absent prompt-capture authorization assertion, or a command with no exit status/artifact.
- [ ] Run it; expected result: FAIL until CI output is structured and exact-SHA-bound.
- [ ] Make CI start the backend, database/vector dependencies, worker/test adapter, and frontend for the CDI V2 Playwright lane. Keep provider calls stubbed and prohibit silent fallback to a live Gemini/DeepSeek/OpenAI provider.
- [ ] Run backend focused core tests, full backend suite, frontend typecheck, lint, unit tests, Playwright list, and the CDI V2 browser journey. A timeout, skipped test, unavailable dependency, or local-only pass is a NO-GO with a classified blocker, not a waiver.
- [ ] Run app/backend/scripts/verify_cdi_v2_release.py only after the three runtime paths have actually completed. Store the generated result outside source control or in a dated report that records exact commit SHA, command, exit code, environment/dialect, and artifact paths.
- [ ] Deploy the immutable PR A head SHA to the target-like environment before asking to merge. Run the three synthetic browser slices there: upload/OCR/index, cited chat, and source-backed GraphRAG. The artifact records deployed Git SHA, build ID, API base URL, worker version, database dialect/vector extension, fixture hash, trace IDs, screenshots, and result. A preview that cannot identify its SHA is not evidence.
- [ ] Re-run git diff --check, GitNexus detect_changes compare main, secret scan, GitHub required checks, review threads, and mergeability. Resolve every P1 finding before requesting merge.
- [ ] Commit the resolved controlled merge and all owned test/CI changes on feat/cdi-v2-main-integration with a concise imperative message. Push normally, open PR A to main, and include scope, migration plan, excluded artifacts, commands, known limitations, screenshots, and privacy boundary.
- [ ] Merge PR A only after required checks are green, independent review has no P1, and GitHub reports merged. Record the actual merge commit SHA M1. Fetch origin/main and verify M1 is an ancestor; do not infer success from local branch history.
- [ ] Immediately deploy or identify the deployment of merged origin/main SHA M1 and repeat the same three synthetic browser slices. If M1 differs from the tested PR SHA and fails, publish NO-GO for production readiness, stop PR B scope expansion, and prepare the smallest reviewed remediation/revert; main is not considered functionally certified until M1 passes.

## Phase C — remediate the 2026-08-14 production and automation audit on a new branch

### Task 8: Start the post-merge audit branch and establish one runtime source of truth

**Files:** app/backend/src/hospital_ai/api/routes/{documents,metrics,chat_stream,graph}.py as applicable after investigation; app/backend/src/hospital_ai/services/{metrics,retrieval,graph_rag,storage}.py; app/frontend dashboard/documents/vector/chat/graph API clients and routes; app/backend/tests/test_*; app/frontend/e2e/*; docs/09-testing/production-certification-<M1>.md.

**Consumes:** M1 on origin/main and the two 2026-08-14 audit documents.

**Produces:** fix/production-evidence-and-audit-gates based exactly on M1, a causal trace for Failed to fetch/zero index, and a data-source contract shared by dashboard, documents, vector metrics, chat, and graph.

- [ ] Fetch origin/main, verify M1, and create fix/production-evidence-and-audit-gates from it in the same checkout. Repeat the dirty-overlap check; do not reuse the integration branch.
- [ ] Attach the M1 post-merge smoke artifact before beginning audit fixes. If it is absent or failed, make restoration of the three core slices the first PR B item rather than treating the audit report as a separate concern.
- [ ] Translate every production report observation into a test identifier, owner, source path, and objective expected result. Mark all as NOT PROVEN until a rerun artifact exists; do not overwrite the 2026-08-14 observations.
- [ ] Write failing integration tests for a synthetic document that assert the same document/generation IDs are returned by Documents, dashboard counters, vector statistics, Chat retrieval, and GraphRAG. Add a test that rejects UI-only fixture metrics when the API source differs.
- [ ] Run the tests. Expected initial result: FAIL reproducing the inconsistent 0 documents versus 48,221/1.42M fixture counters or the failed fetch causal path.
- [ ] Trace request URL, VITE_API_URL build value, CORS preflight/POST/PUT/finalize, auth bearer/session, proxy forwarding, backend trace ID, worker dispatch, and database commit. Diagnose from evidence; do not assume the V2 merge itself caused Failed to fetch.
- [ ] Implement the smallest source-of-truth correction. Production metrics may aggregate a distinct source only if the UI labels it and does not present it as the active clinical corpus. Keep correlation IDs safe and visible in diagnostic artifacts, not raw errors in the UI.
- [ ] Re-run the integration test and a deployed synthetic upload. Expected result: every screen reports consistent IDs/counts and an authorized answer/graph source from the exact upload.

### Task 9: Repair all P1 browser blockers and error sanitation, then regress them

**Files:** applicable frontend routes/components for auth callback, audit, document detail, access requests, chat errors, and graph errors; their API clients/routes; matching backend handlers; app/frontend/e2e/*.spec.ts; app/backend/tests/test_*.

**Consumes:** the P1 list in production-click-through-report-2026-08-14.md: /auth/sso-callback, /audit, /documents/d-04, access request detail, raw chat 401/422, graph placeholder failure.

**Produces:** all P1 routes render a secure success/empty/error state, never a blank page or raw response body; authenticated workflow paths are independently observable.

- [ ] For each P1 item, add a failing browser test and the lowest-level API/unit test. Test direct URL refresh, no data, denied role, expired session, 401/403/422/5xx, retry, and navigation away/back where relevant.
- [ ] Run the selected tests. Expected initial result: FAIL reproducing the report observation.
- [ ] Correct route data fetching, session/callback completion, role guard behavior, typed error mapping, graph empty/error boundary, and request-detail identity handling. Show a short safe user message plus retry/support trace identifier; never show raw JSON, stack traces, access tokens, or PHI.
- [ ] Add accessibility assertions for focus, error announcement, disabled/retry state, and escaped backend labels.
- [ ] Re-run unit/API/browser tests. Expected result: PASS for success, empty, denied, and failure recovery branches.
- [ ] Manually click every repaired route in the deployed target using synthetic identity/data. Record role, direct URL, action sequence, expected/actual, trace ID, screenshot, and final state.

### Task 10: Close P2 consistency gaps and harden audit/observability boundaries

**Files:** frontend chat-history/dashboard views and their clients; backend thread/audit/metrics projection services and routes; tests and Playwright specs; certification report.

**Consumes:** P2 report findings: chat history differs from recent threads; degraded dashboard looks healthy; live counters conflict; browser safety observations are incomplete.

**Produces:** consistent projections or explicit eventual-consistency messaging, a clear degraded state, and auditable safe diagnostics.

- [ ] Write failing tests that create a chat thread, poll both recent and history projections, and assert a defined consistency window/state. Add tests for zero-index/degraded service response so the dashboard cannot look healthy while core data is unavailable.
- [ ] Implement a shared projection query or a documented asynchronous model with visible freshness/time and retry behavior. Do not silently manufacture counts to satisfy the UI.
- [ ] Test audit logs as an authorization boundary: only Admin/Security roles receive logs, denied users receive a safe response, and sensitive fields are redacted. Validate server-side behavior, not just hidden navigation.
- [ ] Re-run the focused tests and browser journeys. Expected result: both projections converge within the documented contract, degraded banner is unambiguous, and audit errors are safe.

### Task 11: Re-run the full automation matrix and create a truthful certification report

**Files:** docs/09-testing/full-project-automation-plan-2026-08-14.md; docs/09-testing/production-click-through-report-2026-08-14.md; new docs/09-testing/production-certification-<exact-sha>.md; CI artifact configuration; test artifacts outside committed source.

**Consumes:** PR B head, CI results, deployed exact SHA, synthetic corpus, browser/session traces, and the 2026-08-14 baseline findings.

**Produces:** a SHA-bound PASS/PARTIAL/NO-GO report in which every claim has a command or click path and artifact, while unavailable lanes remain explicitly unavailable.

- [ ] Write a failing report-schema test that requires: exact commit/deploy SHA; timestamp/timezone; environment; synthetic fixture hashes; each test ID; actor role; expected/actual; command/click path; exit status; artifact; and verdict. It must reject "pass" backed only by --list, a static fixture, or an old SHA.
- [ ] Run the report test; expected result: FAIL until current-run evidence exists.
- [ ] Execute and retain results for: python -m pytest tests/ -q; ruff check src/ tests/; ruff format --check src/ tests/; python scripts/verify_contracts.py; bun run typecheck; bun run lint; bun run test -- --run; bun run test:e2e; and the exact CDI V2 browser journey against the real backend. Use bounded waits and inspect job results instead of treating a local timeout as code failure.
- [ ] Execute C01–C50 using the matrix below. Provider fault cases use a deterministic test-only adapter/staging fault injection. A live provider is an opt-in supplementary lane and never substitutes for deterministic validation.
- [ ] Update the two 2026-08-14 documents only by adding dated rerun links/statuses; preserve their historical observations. Write the new certification report with a separate row for implementation/CI, browser evidence, deployment SHA, and release decision.
- [ ] Re-run the report schema test, diff check, GitNexus detect_changes, required CI, and independent review. Commit PR B only with the exact remediation/tests/docs. Merge only if all required entries are PASS and no P1 remains; otherwise publish an honest NO-GO/PARTIAL report and leave main unchanged.

## C01–C50 Acceptance Matrix

| IDs | Required proof | Hard assertion |
|---|---|---|
| C01–C05 | Known synthetic facts, page/chunk/source-hash citation binding, irrelevant retrieval exclusion, citation dedup. | Every displayed/persisted citation exists in the authorized retrieval set and resolves to the original upload. |
| C06–C10 | Conflicting evidence, precedence, absent evidence, malformed citation identifier, persistence. | Conflict is disclosed or safely refused; an invented/unretrieved ID cannot be emitted or stored. |
| C11–C16 | unauthenticated, wrong-org, wrong-patient, insufficient role, revoked/expired state, deleted source. | Capturing stub LLM receives zero unauthorized chunks; response/audit is safe and typed. |
| C17–C20 | attachment scope, relation-chain mismatch, session switch, direct endpoint probing. | Same policy applies to streaming, non-streaming, graph enrichment, and direct API calls. |
| C21–C25 | one/two-hop traversal, top-k, empty graph, deleted graph item, patient switch. | Traversal output carries source provenance; no stale node/edge survives scope change. |
| C26–C30 | out-of-scope edge, mismatched page/document, source-less node, conflict precedence, vector+graph dedup. | Graph topology never grants content access; merged evidence is permission-filtered and citation-deduplicated. |
| C31–C35 | ordered SSE events, terminal behavior, cancellation, provider timeout/rate limit, malformed provider chunk. | Exactly one terminal outcome; no raw server error, late event, or invalid persisted evidence. |
| C36–C40 | validator rejection, non-stream parity, retry, concurrent threads, audit trace. | Final answer/citation contract matches across modes and trace/audit result is immutable and safe. |
| C41–C45 | retrieved-document prompt injection, script-like labels, unsafe tool instruction, cross-document contamination, unsafe clinical request. | Untrusted text is data, not control; UI escapes it and answer remains constrained to authorized evidence/safe refusal. |
| C46–C50 | fake citations, missing provider key, provider exhaustion/fallback, secret redaction, deployment configuration. | Fail closed with an actionable safe message; no secret is persisted, logged, displayed, or committed. |

## Merge and Release Gates

PR A (core CDI promotion) may merge only when all conditions are true:

- one Alembic head on fresh and representative upgrade paths;
- a synthetic browser upload reaches a persistent terminal generation and feeds both cited chat and source-backed GraphRAG;
- C01–C40 deterministic tests pass, including the instrumented zero-unauthorized-context assertions;
- backend full suite, frontend type/lint/unit, required Playwright runs, contracts, diff check, GitNexus change review, required CI, and independent review are green;
- the immutable PR A head is deployed and proves all three synthetic browser slices, recording its deployed SHA/build/API/worker/dialect/fixture evidence;
- exact candidate/head SHA and excluded generated surfaces are documented.

PR B (audit remediation/certification) may merge only when all conditions are true:

- deployed target advertises and serves the exact PR B SHA;
- M1's post-merge deployment rerun is PASS, or the first PR B change has repaired and rerun the failed core slice before any audit-only claim;
- the Failed to fetch/zero-index causal path is fixed using a real synthetic upload, not mocked counters;
- all P1 findings are fixed and browser-retested; P2 findings are fixed or explicitly accepted as non-release scope by the owner;
- C01–C50 and the report schema are rerun against the candidate SHA with retained artifacts;
- no secrets/PHI are present, no P1 review finding remains, and the final report's release row is PASS.

If any hard assertion fails, classify the result as **NO-GO** (functional/security/schema/browser/deployment/environment), state the exact failing test/trace/SHA, and do not merge.

## Council Review and Incorporated Amendments

**Decision reviewed:** controlled full candidate merge versus selective cherry-pick/rebuild.

**Architect initial position:** retain one controlled --no-commit --no-ff merge on feat/cdi-v2-main-integration because the CDI routes, migrations, UI, worker pipeline, evidence scope, and tests are coupled; fragmenting the stack would replay conflict resolution without preserving an auditable contract.

**Independent positions:** the pragmatist and plan critic agreed, contingent on deployed exact-SHA proof before main and again on M1. The skeptic dissented, preferring selective reconstruction because a fail-closed zero-evidence deployment can look safe while upload/index is broken.

**Verdict:** keep the controlled merge, not cherry-picks. The dissent is addressed by making deployed synthetic vertical-slice proof a PR A merge gate, adding an immediate M1 rerun, and forbidding PR B from treating an M1 core failure as an unrelated audit task.

**Amendments made:** migration validation now parses actual Alembic headers/lineage and corrects the misleading cdi_v2_0004 filename that declares revision cdi_v2_0005; a complete checked-in C01–C50 registry is mandatory; deployment artifacts must identify SHA, build, API, worker, database/vector environment, fixture hash, and traces.

## Final Handoff Format

The executor must return:

1. PR A and PR B URLs, head SHA, actual GitHub merge SHA, branch base SHA, and mergeability/check/review status.
2. A concise changed-file disposition including every excluded candidate artifact and every conflict resolution rationale.
3. Migration heads/history and fresh/upgrade test result.
4. One end-to-end evidence chain: synthetic upload ID → document/generation → pages/chunks/vector/graph IDs → chat thread/SSE terminal → validated citation → audit/trace IDs.
5. A C01–C50 table with PASS/PARTIAL/NO-GO, command or click path, artifact link, exact SHA, and limitation.
6. Separate verdicts for implementation/CI, browser, deployed production, security/authorization, and release readiness. Never collapse them into one unsupported "done" claim.
