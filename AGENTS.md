# Repository Guidelines

## Project Structure & Module Organization
This repository contains the Sprint 0 documentation pack and application workspace for the AI-Powered Hospital Knowledge Assistant. The main project docs live in `docs/`, ordered from `00_template_usage_guide.md` through `10_design_system_and_metrics.md`.

Application code lives under `app/`. The runnable Next.js frontend is in `app/frontend`; planned backend work belongs in `app/backend`. Frontend App Router pages are in `app/frontend/src/app`, reusable UI components are in `app/frontend/src/components`, and shared helpers are in `app/frontend/src/lib`. Design references live in `docs/design/`: Linear for core UI, Vercel for dashboards, and Notion-lite for document surfaces.

## Build, Test, and Development Commands
Use npm for the frontend workflow:

- `cd app/frontend && npm run dev` - start the Next.js development server.
- `cd app/frontend && npm run build` - create a production build.
- `cd app/frontend && npm run start` - serve the production build.
- `cd app/frontend && npm run typecheck` - run TypeScript without emitting files.
- `cd app/frontend && npm run lint` - run the configured Next.js lint command.

## Coding Style & Naming Conventions
Markdown files use ATX headings, short paragraphs, and pipe tables. Preserve numeric doc prefixes in `docs/` because they define the review sequence. Use lowercase filenames with underscores for new docs, for example `11_security_runbook.md`.

For frontend code, use TypeScript, React function components, `PascalCase` component filenames, and `camelCase` local variables. Keep shadcn-style primitives in `app/frontend/src/components/ui` and compose feature components outside that folder.

## Testing Guidelines
`docs/08_master_test_plan_rtm.md` defines the target strategy: unit, integration, permission, OCR, RAG evaluation, system, UAT, and performance testing. Quality targets include citation rate, retrieval quality, safe refusals, zero unauthorized chunks passed to the LLM, and summary latency under 30 seconds for MVP data.

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
4. Treat `.khuym/state.json` as the routing mirror and `.khuym/STATE.md` as the human-readable narrative; keep them aligned.
5. After compaction, re-read `AGENTS.md`, run `node .codex/khuym_status.mjs --json` if present, then re-open `.khuym/HANDOFF.json`, `.khuym/state.json`, `.khuym/STATE.md`, and the active feature context before more work.
6. P1 review findings block merge.

## Working Files

```
.khuym/
  onboarding.json     ← onboarding state for the Khuym plugin
  state.json          ← machine-readable routing snapshot for agents and tools
  STATE.md            ← current phase and focus
  HANDOFF.json        ← pause/resume artifact

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

## Codex Guardrails

- Repo-local `.codex/` files installed by Khuym are workflow guardrails, not optional decoration.
- Use `node .codex/khuym_status.mjs --json` as the preferred quick scout step when it is available.
- Treat `compact_prompt` recovery instructions as mandatory.
- Use `bv` only with `--robot-*` flags. Bare `bv` launches the TUI and should be avoided in agent sessions.
- If the repo is only partially onboarded, stay in bootstrap/planning mode and surface what is missing before implementation.

## Session Finish

Before ending a substantial Khuym work chunk:

1. Update or close the active bead/task if one exists.
2. Leave `.khuym/state.json`, `.khuym/STATE.md`, and `.khuym/HANDOFF.json` consistent with the current pause/resume state.
3. Mention any remaining blockers, open questions, or next actions in the final response.
<!-- KHUYM:END -->
