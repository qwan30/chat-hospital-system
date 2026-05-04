# CONTEXT — Codebase Audit 2026-05

**Feature slug:** `codebase-audit-2026-05`
**Epic:** standalone (prior epic `br-dyy` handoff paused)
**Started:** 2026-05-02
**Skill chain:** `using-khuym → exploring → planning → validating → executing → reviewing → compounding → dream`

## Purpose

Run a full-codebase audit using GitNexus as the primary navigation layer (not grep) to surface:

1. **Security issues** — auth, PHI leakage, permission filters, token handling, CORS, input validation, secrets.
2. **Bugs & edge cases** — null paths, race conditions, abort lifecycle, error swallowing, citation mismatches.
3. **Structure & cleanliness** — dead code, duplicate logic, circular deps, layering violations.
4. **RAG / clinical safety** — unauthorized chunks reaching LLM, empty-evidence honesty, citation fidelity.
5. **Testing gaps** — missing permission tests, missing RAG leakage tests.

Ends with `khuym:compounding` learnings + Dream memory persistence.

## Locked Decisions

- Prior handoff (`kotaemon-chat-assistant-ui`, phase `compounding-complete-human-signoff-pending`) is **paused**, not cancelled. UAT sign-off remains a separate downstream step.
- Scope is **full codebase** (not security-only).
- Execute phase is **in-scope**: minimal upstream fixes for confirmed P1/P2 findings per repo bug-fixing discipline.
- GitNexus index must be refreshed with `--embeddings` (904 embeddings currently present) before exploration begins.
- All symbol edits require prior `gitnexus_impact` analysis per repo rules.

## Tooling Deviation (acknowledged 2026-05-02)

GitNexus MCP server is configured in `.codex/config.toml` for Codex CLI but is **not reachable from this Cascade session**. The `gkg` binary is not on PATH. As a result:

- Repo rules requiring `gitnexus_impact` before edits and `gitnexus_detect_changes` before commits are **substituted** with manual tracing: `grep_search` for callers, `code_search` for execution flows, and `git diff --stat` / `git status` for change scope.
- This is a weaker safety contract than the rule requires. Each fix records its manual impact trace inline in the bead/finding so the deviation is auditable.
- After audit completes, the user is encouraged to re-run `npx gitnexus analyze --embeddings` and verify findings via the proper GitNexus tools in Codex CLI.

GitNexus baseline (post-reindex 2026-05-02): 2392 nodes | 6488 edges | 90 clusters | 197 flows | 904 embeddings preserved.

## Out of Scope

- Production auth/session redesign (tracked separately).
- General knowledge provider abstraction (P3 `br-2o5`, existing bead).
- Full UAT re-run (handled by paused feature's handoff).

## Risk / Clinical-Safety Invariants (must hold through all fixes)

- Zero unauthorized patient chunks reach the LLM.
- Citation rate preserved; no orphaned citation paths.
- Permission filter runs **before** retrieval context is assembled.
- No PHI or real patient data committed; synthetic/de-identified only.

## Artifact Map

- `discovery.md` — raw findings from GitNexus exploration (Phase 1).
- `approach.md` — grouped findings, severity, proposed fixes (Phase 2).
- `findings.md` — final consolidated report (post Phase 5).
- `.spikes/codebase-audit-2026-05/` — reproduction spikes for P1/P2.

## Success Criteria

- All P1 findings fixed with regression tests, or justified as out-of-scope.
- `gitnexus_detect_changes` confirms change scope matches plan on every commit.
- Learnings file in `history/learnings/`, critical patterns promoted.
- Dream memory entries created for durable insights.
