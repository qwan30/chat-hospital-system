<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **chat-hospital-system** (84536 symbols, 213797 relationships, 300 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

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
- **Security Policy**:
  - JWT RBAC/ABAC role filtering in DB layer (`WHERE role_can_access = true` join queries) before retrieval.
  - Citation validation: every LLM citation cross-checked against actual document chunks.
  - Audit logging for all unauthorized or PHI queries.
  - Bearer tokens only stored in React memory, never persisted to localStorage.
