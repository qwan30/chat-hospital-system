# Repository Guidelines

## Project Structure & Module Organization
This repository contains the Sprint 0 documentation pack and application workspace for the AI-Powered Hospital Knowledge Assistant. The main project docs live in the hierarchical directories under `docs/` (such as `docs/01-business/` through `docs/12-handover/`).

Application code lives under `app/`. The runnable **TanStack Start** frontend is in `app/frontend`; the FastAPI backend is in `app/backend`. Frontend routes are in `app/frontend/src/routes/`, reusable UI components are in `app/frontend/src/components/hms/` and `app/frontend/src/components/shell/`, shadcn/ui primitives are in `app/frontend/src/components/ui/`, and shared helpers are in `app/frontend/src/lib`. Design references live in `docs/design/`.

## Build, Test, and Development Commands

### Frontend (TanStack Start + Vite + Bun)
Use **Bun** for the frontend workflow:

- `cd app/frontend && bun run dev` — start the Vite dev server on port 8082.
- `cd app/frontend && bun run build` — create a production build (`VITE_API_URL` required for API proxy).
- `cd app/frontend && bun run typecheck` — run `tsc --noEmit` type checking.
- `cd app/frontend && bun run lint` — run ESLint flat config across `src/`, `e2e/`, and config files.
- `cd app/frontend && bun run test` — run Vitest unit tests.
- `cd app/frontend && bun run test:e2e` — run Playwright E2E tests (Chromium, port 8082).
- `cd app/frontend && bun run format` — auto-format all files with Prettier.

### Backend (FastAPI)
Pip-based Python backend (`pyproject.toml` with hatchling):

- `cd app/backend && python -m uvicorn hospital_ai.main:create_app --reload` — start the development server.
- `cd app/backend && alembic upgrade head` — run database migrations.
- `cd app/backend && python scripts/seed_dev.py` — seed development data.
- `cd app/backend && python -m pytest tests/` — run Python tests (262 pass, 2 skip).
- `cd app/backend && ruff check src/ tests/` — lint backend code.
- `cd app/backend && ruff format --check src/ tests/` — check backend formatting.
- `cd app/backend && python scripts/verify_contracts.py` — verify API contracts.

## Coding Style & Naming Conventions
Markdown files use ATX headings, short paragraphs, and pipe tables. Use lowercase filenames with hyphens/underscores for new docs under their respective domain folders.

For frontend code, use TypeScript, React function components with named-function exports, `PascalCase` component filenames, and `camelCase` local variables. Keep shadcn-style primitives in `app/frontend/src/components/ui` and compose feature components under `app/frontend/src/components/hms/` and `app/frontend/src/components/shell/`.

## Testing Guidelines
`docs/09-testing/test-plan.md` defines the target strategy: unit, integration, permission, OCR, RAG evaluation, system, UAT, and performance testing. Quality targets include citation rate, retrieval quality, safe refusals, zero unauthorized chunks passed to the LLM, and summary latency under 30 seconds for MVP data.

When code exists, name tests by behavior, such as `test_unauthorized_patient_is_blocked`, and keep permission/RAG leakage tests high priority.

## Commit & Pull Request Guidelines
Git history is not available in this workspace, so no existing commit convention can be inferred. Use concise, imperative commits with an optional scope, for example `docs: add deployment checklist` or `backend: enforce patient scope filter`.

Pull requests should summarize the change, link the relevant requirement or test case from `docs/`, include screenshots for UI changes, and call out privacy, PHI, permission, or local-LLM impacts.

## Security & Configuration Tips
Do not commit secrets or real patient data. Local and development environments should use synthetic or de-identified data only. Keep PHI workflows local-first as documented, and filter permissions before retrieval context reaches the LLM.

<!-- KHUYM:START -->
# Khuym Workflow

Use `khuym:using-khuym` first in this repo unless you are resuming an already approved Khuym handoff.

## Startup

1. Read this file at session start and again after any context compaction.
2. If `.khuym/onboarding.json` is missing or outdated, stop and run `khuym:using-khuym` before continuing.
3. If `.codex/khuym_status.mjs` exists, run `node .codex/khuym_status.mjs --json` as the first quick scout step.
4. If `.khuym/HANDOFF.json` exists, do not auto-resume. Surface the saved state and wait for user confirmation.
5. If `history/learnings/critical-patterns.md` exists, read it before planning or execution work.

## Chain

```
khuym:using-khuym
  → khuym:exploring
  → khuym:planning
  → khuym:validating
  → khuym:swarming
  → khuym:executing
  → khuym:reviewing
  → khuym:compounding
```

## Critical Rules

1. Never execute without validating.
2. `CONTEXT.md` is the source of truth for locked decisions.
3. If context usage passes roughly 65%, write `.khuym/HANDOFF.json` and pause cleanly.
4. Treat `.khuym/state.json` as the single runtime state file for routing, current focus, and operator notes.
5. After compaction, re-read `AGENTS.md`, run `node .codex/khuym_status.mjs --json` if present, then re-open `.khuym/HANDOFF.json`, `.khuym/state.json`, and the active feature context before more work.
6. P1 review findings block merge.

## Working Files

```
.khuym/
  onboarding.json     ← onboarding state for the Khuym plugin
  state.json          ← single runtime state file for agents, tools, and humans
  HANDOFF.json        ← pause/resume artifact
  reservations.json   ← local file reservations for same-session Codex swarms

history/<feature>/
  CONTEXT.md          ← locked decisions
  discovery.md        ← research findings
  approach.md         ← approach + risk map

history/learnings/
  critical-patterns.md

.beads/               ← bead/task files when beads are in use
.spikes/              ← spike outputs when validation requires them
```

.codex/
  khuym_status.mjs    ← read-only scout command for onboarding, state, and handoff
  khuym_state.mjs     ← shared state helpers used by the scout command
  khuym_reservations.mjs ← local reservation helper used by swarming, executing, and hooks

## Codex Guardrails

- Repo-local `.codex/` files installed by Khuym are workflow guardrails, not optional decoration.
- Use `node .codex/khuym_status.mjs --json` as the preferred quick scout step when it is available.
- Treat `compact_prompt` recovery instructions as mandatory.
- Use `bv` only with `--robot-*` flags. Bare `bv` launches the TUI and should be avoided in agent sessions.
- If the repo is only partially onboarded, stay in bootstrap/planning mode and surface what is missing before implementation.

## Session Finish

Before ending a substantial Khuym work chunk:

1. Update or close the active bead/task if one exists.
2. Leave `.khuym/state.json` and `.khuym/HANDOFF.json` consistent with the current pause/resume state.
3. Mention any remaining blockers, open questions, or next actions in the final response.
<!-- KHUYM:END -->

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **chat-hospital-system** (6817 symbols, 12048 relationships, 300 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

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
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
