<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **chat-hospital-system** (21256 symbols, 42557 relationships, 300 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

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

# AI Copilot Assistant & Engineering Guidelines

## Project Summary
**Chatbot Hospital System (HOSP-AI-001)** is an enterprise-grade AI-powered Hospital Knowledge Assistant. It integrates a **FastAPI** backend (`app/backend`) with a **TanStack Start / React 19** frontend (`app/frontend`), featuring hybrid RAG retrieval, permission-first security scoping, and HIPAA-compliant audit logging.

## Core Commands

### Backend (FastAPI + Pip + Hatchling)
- **Dev Server**: `cd app/backend && python -m uvicorn hospital_ai.main:create_app --reload`
- **Run Tests**: `cd app/backend && python -m pytest tests/ -v --cov=hospital_ai --cov-fail-under=80`
- **Lint Code**: `cd app/backend && ruff check src/ tests/`
- **Format Code**: `cd app/backend && ruff format --check src/ tests/`
- **Verify Contracts**: `cd app/backend && python scripts/verify_contracts.py`

### Frontend (TanStack Start + Bun)
- **Dev Server**: `cd app/frontend && bun run dev` (Port 8082, proxying to 8000)
- **Build App**: `cd app/frontend && bun run build`
- **Typecheck**: `cd app/frontend && bun run typecheck`
- **Lint Code**: `cd app/frontend && bun run lint`
- **Unit Tests**: `cd app/frontend && bun run test`
- **E2E Tests**: `cd app/frontend && bun run test:e2e`

## Coding Standards & Architectural Invariants
1. **Permission First**: Always enforce active patient scope permissions before retrieving chunks or serving LLM completions.
2. **Repository Layer**: Always isolate database queries inside repositories (`app/backend/src/hospital_ai/repositories/`) rather than putting SQLAlchemy queries inside routes.
3. **Immutability**: Avoid mutating objects in-place in frontend components; return fresh state copies.
