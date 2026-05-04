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

## [20260502] Streaming Endpoints Must Re-Implement RAG Safety Contracts End-to-End
**Category:** failure
**Feature:** codebase-audit-2026-05
**Tags:** [rag, streaming, citations, phi, safety]

A non-streaming `/chat` endpoint can correctly enforce citation validation, evidence filtering, retrieval audit, and rag-trace persistence while an SSE `/chat/stream` endpoint built later silently bypasses every one of those contracts. The streaming endpoint emitted raw LLM tokens with no citation check, dumped all retrieved chunks (not only the cited ones), wrote no `RetrievedEvidence` rows, recorded no success audit, and surfaced raw exception strings to the client. Whenever a parallel transport is added (SSE, WebSocket, gRPC), enumerate every safety contract enforced in the canonical handler and mirror it — citation validation, cited-only evidence, audit-on-success, rag-trace persistence, sanitized error events, and threshold logic. Keep that enumeration in the handler's docstring so the next audit catches drift.

**Full entry:** history/codebase-audit-2026-05/findings.md (F-RAG-001, F-RAG-004, F-SEC-004)

## [20260502] Score-Based Thresholds Must Be Tagged With Their Scoring Scale
**Category:** failure
**Feature:** codebase-audit-2026-05
**Tags:** [rag, retrieval, hybrid, configuration]

`evidence_threshold = 0.2` was correct for cosine and BM25 scores in `[0, 1]` but silently broke the moment Reciprocal Rank Fusion was introduced — RRF produces `~0.03` ceilings, so every hybrid query routed to "no evidence". Mixing scoring scales under one threshold is a silent-correctness bug class: the system returns clinically-safe refusals while RAG quietly stops working. Whenever a new retrieval mode is added, either (a) normalize all paths to a comparable score scale, or (b) make the threshold check mode-aware via a helper that consults the scoring scale used to produce each result, and add a regression test asserting the threshold passes a representative high-quality result for that mode.

**Full entry:** history/codebase-audit-2026-05/findings.md (F-RAG-002)

## [20260428] Migration Chains Need One Schema Source of Truth
**Category:** failure
**Feature:** backend-permission-filtered-rag
**Tags:** [database, migrations, testing]

Model metadata can pass while the Alembic chain is broken. Do not back-edit an existing base migration with columns also introduced by a forward migration unless the project intentionally squashes migrations; add migration-chain or migration-content tests when schema changes land.

**Full entry:** history/learnings/20260428-backend-permission-rag-safety.md
