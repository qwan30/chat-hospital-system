# Full-project automation and AI quality plan

## Goal

Produce one source-backed automation plan for the hospital knowledge assistant, covering the existing backend/frontend/E2E test inventory, 50 chatbot answer-quality scenarios, OCR accuracy, GraphRAG authorization/display, and the verification gates required before a pull request can be merged. The plan must distinguish declared tests from tests actually executed and passed.

## Architecture

The test matrix follows the runtime boundaries: FastAPI routes and services, persistence and permission joins, LLM/retrieval evaluation adapters, TanStack/Vitest UI contracts, and Playwright browser journeys. Deterministic fixtures and stub providers are the default. A live OpenAI-compatible provider is an optional, explicitly configured lane; DeepSeek is selected only through process environment variables and is not an automatic Gemini failover.

## Tech Stack

Python 3.11 + pytest for backend tests and evaluation harnesses; Bun + Vitest for frontend unit tests; Playwright Chromium for browser tests; FastAPI HTTP/SSE contracts; SQLite or synthetic isolated fixtures where supported; GitHub Actions as the CI source of truth; GitNexus for impact and change-scope evidence when indexed.

## Global Constraints

- Use synthetic or de-identified patient/document data only. Never commit API keys, PHI, generated secrets, or raw provider responses containing sensitive data.
- Treat source counts as inventory only. A PASS claim requires a recorded command, exit status, and artifact or test report.
- Preserve full authorization joins across patient, document, page, and chunk before ranking or LLM invocation. Test revoked, expired, soft-deleted, mismatched-owner, and cross-tenant cases.
- Streaming tests must cover client abort/disconnect and must enforce the same citation, safety, threshold, audit, trace, and sanitized-error contracts as non-streaming chat.
- For an optional DeepSeek live judge lane, the operator must explicitly select `--llm-judge-provider openai` and export `AI_EVAL_PROVIDER=openai`, `AI_EVAL_MODEL=deepseek-chat`, `AI_EVAL_BASE_URL=https://api.deepseek.com/v1`, and `AI_EVAL_API_KEY` in the shell that launches the test. The application chat provider can separately use `HOSPITAL_AI_CHAT_PROVIDER=openai` and its OpenAI-compatible settings. Do not place the key in files or command output. Skip the lane when the variable is absent.
- Do not change existing application symbols in this documentation/test-inventory task. If implementation changes become necessary, run GitNexus `impact` upstream first and warn on HIGH or CRITICAL risk.

## Execution tasks

### 1. Establish the source inventory and evidence ledger

Inspect `app/backend/pyproject.toml`, `app/frontend/package.json`, `.github/workflows/ci.yml`, `README.md`, `docs/09-testing/`, and the source/test trees. The current inventory is 83 backend test files/619 direct declarations and 738 pytest-collected tests, 18 Vitest files/122 direct declarations and 130 executed tests, and 15 Playwright specs/126 direct declarations and 152 collected browser tests. The direct-declaration subtotal is 867; collected/ executed counts must remain separate. Recount with the commands below after changes; record runnable failures separately from source counts.

Commands:

```powershell
rg --files app/backend/tests app/frontend/src app/frontend/e2e
rg -n "^\s*(async\s+)?def\s+test_|\b(it|test)\(" app/backend/tests app/frontend/src app/frontend/e2e
git status --short
```

Expected evidence: a dated inventory table, the exact commands used, and a blocker table for missing/broken runtimes or dependencies.

### 2. Build the chatbot 50-scenario matrix and deterministic automation

Map every scenario to the existing chat route/pipeline/retrieval/citation/audit tests. Add only deterministic tests that exercise a real contract and keep each new file's ownership disjoint from auth work. The scenario matrix is grouped as: single-hop usefulness (C01-C10), safe refusal and permission (C11-C20), GraphRAG and multi-hop (C21-C30), SSE/transport/thread behavior (C31-C40), and adversarial quality/provider behavior (C41-C50).

Required assertions include answer usefulness, grounded citations, no unauthorized chunk reaching the LLM, safe refusal when evidence is insufficient, sanitized errors, trace/audit records, deterministic ordering, abort behavior, and provider configuration. A citation-valid response without useful support is not sufficient.

Commands:

```powershell
python -m pytest app/backend/tests/test_streaming.py app/backend/tests/test_chat_stream_citation_contract.py app/backend/tests/test_audit_2026_05.py -q
bun run test -- --run
```

Expected evidence: scenario IDs mapped to executable test IDs, fixture/seed requirements, and a report separating deterministic PASS, SKIP, FAIL, and NOT RUN.

### 3. Cover OCR ingestion and accuracy

Exercise `upload_document`, indexing/retry, `OcrService.extract_pages`, source fingerprint/generation preservation, native text PDFs, image-only documents when the optional PaddleOCR worker is available, malformed/empty input, page ordering, language/script handling, and sanitized failure recovery. Use the existing OCR evaluation harness and report page accuracy, character/word error where available, critical-field precision/recall, and per-document failures; do not report a single aggregate as proof of clinical readiness.

Commands:

```powershell
python -m pytest app/backend/tests/test_ocr_service.py app/backend/tests/test_documents.py app/backend/tests/evaluation/test_ocr_evaluation.py -q
python app/backend/scripts/run_paddle_ocr_worker.py --help
```

Expected evidence: fixture manifest, extraction artifacts, metrics, unavailable-optional-dependency status, and preservation/fail-closed assertions.

### 4. Cover GraphRAG retrieval, authorization, and display

Exercise the patient graph endpoint, related-entity BFS/hop limits, empty/deleted/out-of-scope/mismatched edges, permission-filtered chunk IDs, graph-enriched chat citations, and frontend loading/empty/error/details states. Verify that graph output cannot bypass normal retrieval authorization and that the UI renders only the contract fields returned by the API.

Commands:

```powershell
python -m pytest app/backend/tests/test_graph_endpoint.py app/backend/tests/test_graph_rag_chat_release_gates.py app/backend/tests/evaluation/test_product_retrieval_adapter.py -q
bun run test -- --run
bunx playwright test app/frontend/e2e --list
```

Expected evidence: endpoint contract report, authorization matrix, UI state coverage, and browser results when a real backend is running.

### 5. Synchronize documentation from source

Update the consolidated automation document, README test-status claims, `docs/09-testing/` indexes, and provider/environment documentation from current package scripts, CI, routes, OpenAPI/contracts, and source configuration. Create or update `docs/CONTRIBUTING.md` and `docs/RUNBOOK.md` only with source-backed commands and generated-status markers. Correct provider-count and execution-status drift; preserve historical reports as historical.

Required checks:

```powershell
git diff --check
rg -n "pytest|vitest|playwright|HOSPITAL_AI_CHAT_PROVIDER|DEEPSEEK|Gemini|pass|PASS|release" README.md docs app/backend/.env.example .github/workflows/ci.yml
```

Expected evidence: every changed claim has a canonical source path and date, and no secret appears in the diff.

### 6. Execute bounded verification lanes

Run deterministic backend, frontend, evaluation, and browser lanes independently so one environment failure does not erase evidence from another. Use a maximum of three retries only for infrastructure/resource failures, inspect logs between retries, and stop after 20 minutes per lane. The evaluator accepts an explicit OpenAI-compatible judge provider; run the optional DeepSeek live lane only when explicitly configured by the operator. This is manual provider selection, not silent substitution for a missing Gemini key.

Required artifacts: pytest/JUnit output, Vitest output, Playwright report where runnable, OCR/GraphRAG/chat evaluation markdown or JSON, and a command ledger with commit SHA, environment, exit code, and blocker classification.

### 7. Review, PR, CI, and merge gates

Run `git diff --check`, inspect the exact diff, invoke GitNexus `detect_changes` against the automation worktree before commit, and request an independent review of test relevance, security/authorization, documentation truthfulness, and secret handling. Open the PR with a source/test/evidence summary. Inspect GitHub Actions logs after the PR is opened; fix only reproducible in-scope failures, re-run affected lanes, and merge only when required checks are green and no P1 review finding remains.

The current workflow does not make this full matrix a single PR merge gate: Markdown-only changes can skip CI, PR AI evaluation requests only the corpus component, and Playwright is deferred because the frontend job has no backend service. Therefore the PR must state which required CI jobs actually ran and which matrix lanes remain advisory/deferred; “CI green” must not be expanded into “full project green.”

The automation branch also depends on the auth branch. Before integration, record the auth branch's exact commit SHA, verify that auth tests and fixtures remain compatible, then run the combined focused backend lane. Do not merge the automation branch as auth-fix evidence until that dependency is present.

Final gates: no untracked secret or fixture leakage, exact branch/commit recorded, deterministic required checks green, optional/live skips explicitly labeled, CI results accurately scoped, review resolved, mergeability confirmed, and release claims kept separate from test automation claims.

## Self-review checklist

- Every requested domain appears: chatbot, OCR, GraphRAG, frontend display, existing tests, 50 scenarios, source-sync docs, subagent/council review, CI/log/merge gates.
- Counts are labeled as source declarations rather than executed passes.
- Provider fallback language is explicit and secret-safe.
- Failure, recovery, authorization, and usefulness assertions are first-class.
- Commands are repository-relative and correspond to current source/configuration.
