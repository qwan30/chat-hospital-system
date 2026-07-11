# Developer Onboarding Guide

> Project: HOSP-AI-001 · Version: 2.0 · Owner: Tech Lead · Last Updated: 2026-07-12

## 1. Quick Start (5 Minutes)

```bash
# Clone and enter
git clone <repo-url> && cd chatbot-hospital-system/app

# Backend setup
cd backend
pip install -e ".[dev,postgres]"
cp .env.example .env
alembic upgrade head
python scripts/seed_dev.py
uvicorn hospital_ai.main:create_app --factory --reload

# Frontend setup (new terminal)
cd ../frontend
bun install
bun run dev
```

**Verify:** `http://localhost:8082` (UI) · `http://localhost:8000/docs` (Swagger)

## 2. Repository Structure

```
├── docs/                    # 12-domain documentation pack
├── app/
│   ├── backend/             # FastAPI (Python 3.12)
│   │   ├── alembic/         # 7 migrations
│   │   ├── scripts/         # seed, demo, smoke tests
│   │   └── src/hospital_ai/
│   │       ├── api/routes/  # 14 route modules
│   │       ├── core/        # config, errors, security
│   │       ├── db/          # 14 models, session
│   │       ├── schemas/     # Pydantic models
│   │       ├── services/    # 18 business modules
│   │       │   ├── embedding/  # 3 providers
│   │       │   └── llm/        # 3 providers
│   │       └── workers/     # RQ job handlers (OCR, Graph, CDSS)
│   └── frontend/            # TanStack Start (TypeScript + Bun)
│       ├── e2e/             # Playwright E2E tests
│       └── src/
│           ├── routes/      # 90+ TanStack Router pages
│           ├── components/  # 60+ feature + 30 UI components
│           └── lib/         # API client, auth
```

## 3. Key Architecture Concepts

- **BFF Pattern:** FastAPI = single entry point for TanStack Start UI
- **Service Layer:** All business logic in `services/`, not routes
- **LLM Manager:** Stub/Ollama/OpenAI, runtime-switchable
- **RAG Pipeline:** Permission → Embed → Retrieve → Rerank → Generate → Validate
- **Autonomous CDSS Agent:** After OCR + graph indexing, a background RQ worker (`workers/cdss.py`) runs `run_cdss_analysis(session, document_id)` — queries the patient Knowledge Graph (GraphEntity + GraphRelation), feeds context to LLM, and persists `ClinicalAlert` rows. See `docs/04-architecture/architecture.md` for the full sequence diagram.
- **Local-First PHI:** Patient data never leaves hospital intranet

## 4. Development Workflow

1. Read `00-overview/project-foundation.md` (Source of Truth first)
2. Pick task → branch `feature/<desc>`
3. TDD: Red → Green → Refactor
4. Follow `04-architecture/coding-standards.md`
5. Run checks: `ruff check src/` / `bun run typecheck && bun run lint`
6. Run tests: `pytest` / `bun run test`
7. Code review → address CRITICAL/HIGH findings
8. Commit: `feat(scope): description`

## 5. Useful Commands

**Backend:**
```bash
cd app/backend
uvicorn hospital_ai.main:create_app --factory --reload
python -m pytest tests/
python -m pytest tests/ --cov=src/hospital_ai
ruff check src/
alembic revision --autogenerate -m "desc"
alembic upgrade head
python scripts/seed_dev.py

# CDSS-specific tests
python -m pytest tests/test_cdss_agent.py -v
```

**Frontend:**
```bash
cd app/frontend
bun run dev
bun run test
bun run typecheck
bun run lint
bun run build

# CDSS E2E test
bun run test:e2e e2e/cdss-flow.spec.ts
```

## 6. Key Files

| File | Purpose |
|------|---------| 
| `api/router.py` | All 14 route modules registered |
| `db/models.py` | All 14 database tables (incl. `ClinicalAlert`) |
| `core/config.py` | Environment-based settings |
| `core/errors.py` | AppError exception hierarchy |
| `api/deps.py` | FastAPI dependencies (auth, session) |
| `services/chat.py` | Main RAG pipeline |
| `services/llm/manager.py` | LLM provider registry |
| `services/reasoning.py` | 3 reasoning pipelines |
| `services/permissions.py` | ABAC + RBAC enforcement |
| `workers/cdss.py` | Autonomous CDSS Agent — graph context + LLM risk alerts |
| `workers/jobs.py` | RQ job handlers — OCR, indexing, CDSS enqueueing |
| `lib/api-client.ts` | Frontend typed API client |
| `lib/auth-context.tsx` | React auth context |

## 7. Environment Variables

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/hospital_ai
HMS_JWT_SECRET=<shared-secret>
CHAT_PROVIDER=ollama|stub|openai
EMBEDDING_PROVIDER=ollama|deterministic|openai
OLLAMA_BASE_URL=http://localhost:11434
CHAT_MODEL=qwen2.5:7b
CORS_ORIGINS=http://localhost:8082
```

## Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-06-14 | Agent | Created onboarding guide |
| 2.0 | 2026-07-12 | Agent | Updated for CDSS Autonomous Agent feature: added `workers/cdss.py`, `ClinicalAlert` (14th model), 7 migrations, CDSS test commands; replaced `poetry`→`pip`, `npm`→`bun`, `Next.js 16`→`TanStack Start`; fixed port to 8082 |
