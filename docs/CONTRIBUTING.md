# Contributing and test evidence

Use synthetic or de-identified data only. Never commit API keys, provider payloads containing sensitive data, local `.env` files, or generated credentials.

## Local checks

From the repository root:

```powershell
cd app/backend
python -m pytest tests/ -q
ruff check src/ tests/
ruff format --check src/ tests/
python scripts/verify_contracts.py

cd ../frontend
bun run typecheck
bun run lint
bun run test -- --run
```

Playwright requires a running backend and the frontend development server:

```powershell
bun run test:e2e
```

The exact CI behavior is defined by `.github/workflows/ci.yml`. A source count is not a passing-test claim; record the command, commit SHA, exit code, and artifact/report path.

## Provider tests

Deterministic `stub`/local configurations are the default. For an explicitly selected application OpenAI-compatible provider, export `HOSPITAL_AI_CHAT_PROVIDER=openai`, the provider base URL/model, and `HOSPITAL_AI_OPENAI_API_KEY` in the process environment. For the evaluation judge, use `--llm-judge-provider openai` with `AI_EVAL_PROVIDER`, `AI_EVAL_MODEL`, `AI_EVAL_BASE_URL`, and `AI_EVAL_API_KEY`. DeepSeek is an explicit configuration option, not automatic failover from Gemini. Do not print or persist the key.

See [`docs/09-testing/full-project-automation-plan-2026-08-14.md`](09-testing/full-project-automation-plan-2026-08-14.md) for the current chatbot, OCR, GraphRAG, and evidence matrix.
