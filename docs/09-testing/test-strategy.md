# Test Strategy

> Project: HOSP-AI-001 · Version: 1.0 · Owner: QA Lead · Last Updated: 2026-06-14  
>
> **Current-source note (2026-08-14):** This is a historical strategy baseline. The repository uses Python venv + `python -m pytest`, Bun/Vitest, and `bunx playwright`; CI enforces backend coverage at 60%, not this document's 80% target. Playwright is currently deferred in CI because no backend service is provided. See [`full-project-automation-plan-2026-08-14.md`](full-project-automation-plan-2026-08-14.md) for current evidence status.

## 1. Test Pyramid

```
        ┌──────┐
        │ E2E  │  Playwright — 5 critical user journeys
       ┌┴──────┴┐
       │ Integr │  pytest-asyncio — API + DB + RAG pipeline
      ┌┴────────┴┐
      │  Unit    │  pytest (BE) + Vitest (FE) — isolated logic
     └┴──────────┴┘
```

## 2. Test Types

| Type | Framework | Scope | Coverage Target | Run Time |
|------|-----------|-------|-----------------|----------|
| Unit | pytest (BE), Vitest (FE) | Isolated functions, components | 80% line | <2 min |
| Integration | pytest-asyncio | API + DB + RAG pipeline | Critical paths | <5 min |
| E2E | Playwright | 5 critical user journeys | Must pass | <10 min |
| RAG Evaluation | run_rag_eval.py | Citation accuracy, safe refusal | ≥95% cited | Manual |
| Security | Manual + CI scan | Auth, permissions, injection | All endpoints | Per release |

## 3. Backend (pytest)

```bash
cd app/backend
    python -m pytest tests/                    # All tests
    python -m pytest tests/ --cov=hospital_ai  # Coverage
    python -m pytest tests/ -m "not slow"      # Skip slow tests
```

Conventions: `test_<module>.py` · `test_<what>_<expected>()` · fixtures in `conftest.py` · async via `pytest-asyncio` · mock external services

## 4. Frontend (Vitest)

```bash
cd app/frontend
bun run test -- --run                    # Unit + component tests
bun run test -- --run --coverage         # With coverage
```

Conventions: `__tests__/<path>/*.test.tsx` · React Testing Library · user-event for interactions · mock API client

## 5. E2E (Playwright)

```bash
cd app/frontend
bunx playwright test         # All E2E
bunx playwright test --ui    # Interactive mode
```

5 critical journeys: Login→Dashboard→Patient · Chat→Cited Answer · Document Upload→Index · Access Request→Approval · Audit→Filter→Details

## 6. RAG Evaluation

```bash
cd app/backend
python scripts/run_rag_eval.py
```

Tracks: citation accuracy, safe refusal rate, evidence threshold, retrieval precision@k

## 7. CI Integration

```
Lint → Typecheck → Unit → Build → Integration → E2E (smoke) → Security Scan
```

PR blocked by the checks defined in `.github/workflows/ci.yml`; the current backend coverage gate is `--cov-fail-under=60`. Docs-only changes can be excluded by workflow path filters, frontend E2E is deferred without a backend service, and release evaluation has separate sentinel/review gates. Do not treat this historical strategy as a current full-green guarantee.

## Change Log
| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-06-14 | Agent | Complete test strategy: pyramid, types, conventions, CI |
