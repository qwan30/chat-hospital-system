<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **chat-hospital-system** (11871 symbols, 20034 relationships, 300 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> Index stale? Run `node .gitnexus/run.cjs analyze` from the project root — it auto-selects an available runner. No `.gitnexus/run.cjs` yet? `npx gitnexus analyze` (npm 11 crash → `npm i -g gitnexus`; #1939).

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows. For regression review, compare against the default branch: `detect_changes({scope: "compare", base_ref: "main"})`.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `context({name: "symbolName"})`.

## Never Do

- NEVER edit a function, class, or method without first running `impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `rename` which understands the call graph.
- NEVER commit changes without running `detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/chat-hospital-system/context` | Codebase overview, check index freshness |
| `gitnexus://repo/chat-hospital-system/clusters` | All functional areas |
| `gitnexus://repo/chat-hospital-system/processes` | All execution flows |
| `gitnexus://repo/chat-hospital-system/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->

## Git Branch Naming

Use `<type>/<short-kebab-case>` branch names: `feat/`, `fix/`, `refactor/`, `docs/`, `test/`, `ci/`, or `chore/`. Include a date only when it disambiguates a time-bound initiative, for example `feat/full-ai-evaluation-platform-20260722`. Do not use agent or tool prefixes such as `codex/`.

---
# 🏥 Project Instructions & Developer Guide (ECC & Mario SDLC Compliant)

## 🛠️ Tech Stack
- **Backend**: FastAPI (Python 3.11+) + SQLAlchemy 2.0 (asyncio) + pgvector (PostgreSQL) / aiosqlite (SQLite for dev/tests).
- **Frontend**: TanStack Start (Vite 8 + React 19) + Tailwind CSS v4 + shadcn/ui.
- **Async Workers**: Redis + RQ (Redis Queue) for document parsing, OCR (PaddleOCR), embeddings, and CDSS jobs.
- **AI/LLM Stack**: Ollama (Qwen 2.5 3B/7B) / OpenAI / Stub provider (for tests).

## 🚀 Build & Run Commands

### Backend (FastAPI)
- **Dev Server**: `cd app/backend && .venv/Scripts/python -m uvicorn hospital_ai.main:create_app --reload`
- **Database Migrations**: `cd app/backend && .venv/Scripts/python -m alembic upgrade head`
- **Seed Dev Data**: `cd app/backend && .venv/Scripts/python scripts/seed_dev.py`
- **Run Pytest Suite**: `cd app/backend && .venv/Scripts/python -m pytest tests/`
- **RAG Evaluation**: `cd app/backend && .venv/Scripts/python scripts/run_rag_eval.py`
- **API Contract Check**: `cd app/backend && .venv/Scripts/python scripts/verify_contracts.py`

### Frontend (TanStack Start)
- **Dev Server (Port 8082)**: `cd app/frontend && bun run dev`
- **Production Build**: `cd app/frontend && bun run build`
- **Run Unit Tests (Vitest)**: `cd app/frontend && bun run test`
- **Run E2E Tests (Playwright)**: `cd app/frontend && bun run test:e2e`
- **Lint Code**: `cd app/frontend && bun run lint`
- **Type Check**: `cd app/frontend && bun run typecheck`

## 📐 Code Style & Conventions
- **TypeScript**: Function components with named exports, PascalCase for components, camelCase for local variables.
- **Python**: PEP 8 compliance, async handlers for routes, Pydantic v1 models (FastAPI 0.95+ dependency).
- **Clean Architecture**: Domain exceptions in `exceptions.py` (no FastAPI imports), providers abstract interfaces in `interfaces.py`.
- **Security Policy** (describes what the code actually does — keep it that way):
  - **Patient-scope ABAC is enforced in SQL**: retrieval joins an active-permission subquery
    in the `WHERE` clause (`services/retrieval.py`, `services/permissions.py`), so
    unauthorized patient chunks never leave the database. Expiry- and soft-delete-aware.
  - **Role filtering runs in Python after retrieval** (`services/retrieval.py:76-112`,
    `_apply_role_filters`). There is no `role_can_access` column. It executes *after*
    `LIMIT :top_k`, so a filtered result set can be smaller than `top_k` — account for that
    when tuning retrieval recall.
  - **Citation validation is enforced twice**: inside the pipeline (`services/reasoning.py`)
    and again at the service boundary (`services/chat.py`), which additionally rejects
    answers containing zero citations.
  - Audit logging covers access, denial, query, and config-change events. Use
    `core/security.py:sanitize_audit_query` for anything user-authored — never write raw
    clinical free text into audit metadata.
  - **Rate limiting is fail-closed**: `api/limiter.py` enables limits unless `TESTING=true`
    is set explicitly. Never reintroduce a default that disables it.
  - **Bearer tokens are never written to `localStorage`.** `lib/session.tsx` persists only
    `{role, workspaceId}` (typed `PersistedSession`, enforced with `satisfies` so a token
    cannot be reintroduced without a type error) and re-derives the dev token from the role
    map on rehydrate; `lib/api-client.ts` keeps the real token in memory only. An httpOnly
    refresh cookie so a real JWT session survives reload is still future work.
