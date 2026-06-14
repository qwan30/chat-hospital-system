# Test Strategy

> Project: HOSP-AI-001 · Version: 1.0 · Owner: QA Lead · Last Updated: 2026-06-14  

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
poetry run pytest                    # All tests
poetry run pytest --cov=src/hospital_ai  # Coverage
poetry run pytest -m "not slow"      # Skip slow tests
```

Conventions: `test_<module>.py` · `test_<what>_<expected>()` · fixtures in `conftest.py` · async via `pytest-asyncio` · mock external services

## 4. Frontend (Vitest)

```bash
cd app/frontend
npm test                    # Unit + component tests
npm test -- --coverage      # With coverage
```

Conventions: `__tests__/<path>/*.test.tsx` · React Testing Library · user-event for interactions · mock API client

## 5. E2E (Playwright)

```bash
cd app/frontend
npx playwright test         # All E2E
npx playwright test --ui    # Interactive mode
```

5 critical journeys: Login→Dashboard→Patient · Chat→Cited Answer · Document Upload→Index · Access Request→Approval · Audit→Filter→Details

## 6. RAG Evaluation

```bash
cd app/backend
poetry run python scripts/run_rag_eval.py
```

Tracks: citation accuracy, safe refusal rate, evidence threshold, retrieval precision@k

## 7. CI Integration

```
Lint → Typecheck → Unit → Build → Integration → E2E (smoke) → Security Scan
```

PR blocked: lint/typecheck fail, unit fail, coverage <80%. Nightly: full E2E + RAG eval. Release gate: all green.

## Change Log
| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-06-14 | Agent | Complete test strategy: pyramid, types, conventions, CI |
