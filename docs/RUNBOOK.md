# Test and evidence runbook

## Before running

1. Confirm the branch and exact commit SHA.
2. Confirm `.env` and generated output are ignored and contain no committed secrets.
3. Use synthetic/de-identified fixtures.
4. Confirm the required runtime and dependency set from `app/backend/pyproject.toml`, `app/frontend/package.json`, and the CI workflow.

## Lanes

Run backend, frontend, OCR/GraphRAG evaluation, and browser lanes independently. Keep the command, start time, exit code, logs, and report artifact for each lane. If a lane fails because of a dependency or resource problem, classify it as an environment blocker; do not convert it to PASS or silently skip it.

For live-model checks, select one provider explicitly through environment variables. The evaluator's OpenAI-compatible lane uses `--llm-judge-provider openai` plus `AI_EVAL_PROVIDER`, `AI_EVAL_MODEL`, `AI_EVAL_BASE_URL`, and `AI_EVAL_API_KEY`; the application lane uses the `HOSPITAL_AI_*` provider variables. DeepSeek may be selected explicitly; it is not an automatic fallback when Gemini is unavailable. Do not place credentials in this runbook, a shell transcript, or a report.

## Failure handling

Retry infrastructure/resource failures at most three times, inspecting logs between retries, and stop after 20 minutes per lane. For test failures, preserve the first failing artifact, identify the affected contract, and fix only in-scope code. Streaming failures must include disconnect/abort, citation, safety, audit, and sanitized-error checks.

## PR gate

Before commit, run `git diff --check` and GitNexus `detect_changes` for the target worktree. Before merge, confirm required CI checks are green, review has no P1 findings, skipped/deferred lanes are explicitly documented, and the exact merge/release SHA is recorded. The current CI workflow defers Playwright without a backend and PR AI evaluation requests only the corpus component; do not report those as full-project green. Release certification is a separate gate from test inventory or local green results.
