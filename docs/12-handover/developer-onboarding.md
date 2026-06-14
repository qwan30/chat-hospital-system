# Developer Onboarding Guide

> Project: HOSP-AI-001 · Version: 1.0 · Owner: Tech Lead · Last Updated: 2026-06-14

## 1. Quick Start (5 Minutes)

```bash
# Clone and enter
git clone <repo-url> && cd chatbot-hospital-system/app

# Backend setup
cd backend
poetry install
cp .env.example .env
poetry run alembic upgrade head
poetry run python scripts/seed_dev.py
poetry run uvicorn hospital_ai.main:create_app --reload

# Frontend setup (new terminal)
cd ../frontend
npm install
npm run dev
```

**Verify:** `http://localhost:3000` (UI) · `http://localhost:8000/docs` (Swagger)

## 2. Repository Structure

```
├── docs/                    # 12-domain documentation pack
├── app/
│   ├── backend/             # FastAPI (Python)
│   │   ├── alembic/         # 6 migrations
│   │   ├── scripts/         # seed, demo, smoke tests
│   │   └── src/hospital_ai/
│   │       ├── api/routes/  # 14 route modules
│   │       ├── core/        # config, errors, security
│   │       ├── db/          # 13 models, session
│   │       ├── schemas/     # Pydantic models
│   │       ├── services/    # 18 business modules
│   │       │   ├── embedding/  # 3 providers
│   │       │   └── llm/        # 3 providers
│   │       └── workers/     # RQ job definitions
│   └── frontend/            # Next.js 16 (TypeScript)
│       └── src/
│           ├── app/(app)/   # 14 pages
│           ├── components/  # 60+ feature + 30 UI
│           └── lib/         # API client, auth
```

## 3. Key Architecture Concepts

- **BFF Pattern:** FastAPI = single entry point for Next.js UI
- **Service Layer:** All business logic in `services/`, not routes
- **LLM Manager:** Stub/Ollama/OpenAI, runtime-switchable
- **RAG Pipeline:** Permission → Embed → Retrieve → Rerank → Generate → Validate
- **Local-First PHI:** Patient data never leaves hospital intranet

## 4. Development Workflow

1. Read `00-overview/project-foundation.md` (Source of Truth first)
2. Pick task → branch `feature/<desc>`
3. TDD: Red → Green → Refactor
4. Follow `04-architecture/coding-standards.md`
5. Run checks: `ruff check` / `npm run typecheck && npm run lint`
6. Run tests: `pytest` / `npm test`
7. Code review → address CRITICAL/HIGH findings
8. Commit: `feat(scope): description`

## 5. Useful Commands

**Backend:**
```bash
cd app/backend
poetry run uvicorn hospital_ai.main:create_app --reload
poetry run pytest
poetry run pytest --cov=src/hospital_ai
poetry run ruff check src/
poetry run alembic revision --autogenerate -m "desc"
poetry run alembic upgrade head
poetry run python scripts/seed_dev.py
```

**Frontend:**
```bash
cd app/frontend
npm run dev
npm test
npm run typecheck
npm run lint
npm run build
```

## 6. Key Files

| File | Purpose |
|------|---------|
| `api/router.py` | All 14 route modules registered |
| `db/models.py` | All 13 database tables |
| `core/config.py` | Environment-based settings |
| `core/errors.py` | AppError exception hierarchy |
| `api/deps.py` | FastAPI dependencies (auth, session) |
| `services/chat.py` | Main RAG pipeline |
| `services/llm/manager.py` | LLM provider registry |
| `services/reasoning.py` | 3 reasoning pipelines |
| `services/permissions.py` | ABAC + RBAC enforcement |
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
CORS_ORIGINS=http://localhost:3000
```

## Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-06-14 | Agent | Created onboarding guide |
