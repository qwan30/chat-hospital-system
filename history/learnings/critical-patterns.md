# Critical Patterns

Promoted learnings from completed features. Read this file at the start of every
planning Phase 0 and every exploring Phase 0. These are the lessons that cost the
most to learn and save the most by knowing.

---

## [20260429] Streaming RAG Requires Explicit Client-Side Abort Contracts
**Category:** pattern
**Feature:** streaming-rag-and-persistent-settings
**Tags:** [streaming, frontend, abort-controller, reliability]

Streaming chat responses (SSE) without explicit client-side lifecycle management lead to orphaned backend context and stale UI "ghost" messages. Every streaming frontend component MUST use an `AbortController` linked to the component lifecycle or user "Stop" action, and the backend MUST monitor the connection close event to terminate reasoning chains.

**Full entry:** history/learnings/20260429-streaming-and-persistent-settings.md

---

## [20260428] RAG Evidence Requires Full Join-Chain Authorization
**Category:** failure
**Feature:** backend-permission-filtered-rag
**Tags:** [permissions, rag, phi]

RAG retrieval is not protected by a single patient permission check. Any evidence query that joins patient, document, page, and chunk data must prove ownership and lifecycle state at every joined layer before ranking or sending context to an LLM. Add adversarial tests for revoked permissions, expired permissions, soft-deleted rows, mismatched document ownership, and mismatched page-document ownership.

**Full entry:** history/learnings/20260428-backend-permission-rag-safety.md

## [20260429] Cited RAG Answers Need Answer-Usefulness Assertions
**Category:** failure
**Feature:** kotaemon-chat-assistant-ui
**Tags:** [rag, uat, testing, hms]

A RAG answer can be safe, permission-filtered, and correctly cited while still failing the user's task if it does not summarize the exact facts requested. Manual UAT exposed this when HMS appointment evidence was cited but the answer text stayed generic. For every seeded RAG acceptance question, assert both evidence fidelity and answer usefulness by checking that requested fields from the cited evidence appear in the answer.

**Full entry:** history/learnings/20260429-chat-uat-feedback-contracts.md

## [20260428] Raw SQL Permission Policy Needs an Executable Contract
**Category:** pattern
**Feature:** backend-permission-filtered-rag
**Tags:** [permissions, sql, testing]

Security policy in raw SQL drifts unless it is generated from the same source as ORM predicates or protected by invariant tests. When a PHI, tenancy, or authorization rule appears in hand-written SQL, import the shared predicate or SQL fragment and test the production SQL path directly.

**Full entry:** history/learnings/20260428-backend-permission-rag-safety.md

## [20260428] Re-index Preservation Needs a Source and Generation Contract
**Category:** decision
**Feature:** backend-permission-filtered-rag
**Tags:** [indexing, workers, reliability]

Preserving old derived data after a failed replacement job is safe only when the worker can prove the source is unchanged. Replacement indexing should compute a source fingerprint, use a generation or locking contract before swapping rows, and fail closed on unknown source identity, embedding count mismatch, or stale worker generation.

**Full entry:** history/learnings/20260428-backend-permission-rag-safety.md

## [20260428] Migration Chains Need One Schema Source of Truth
**Category:** failure
**Feature:** backend-permission-filtered-rag
**Tags:** [database, migrations, testing]

Model metadata can pass while the Alembic chain is broken. Do not back-edit an existing base migration with columns also introduced by a forward migration unless the project intentionally squashes migrations; add migration-chain or migration-content tests when schema changes land.

**Full entry:** history/learnings/20260428-backend-permission-rag-safety.md
