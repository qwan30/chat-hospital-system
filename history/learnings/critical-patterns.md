# Critical Patterns

Promoted learnings from completed features. Read this file at the start of every
planning Phase 0 and every exploring Phase 0. These are the lessons that cost the
most to learn and save the most by knowing.

---

## [20260428] RAG Evidence Requires Full Join-Chain Authorization
**Category:** failure
**Feature:** backend-permission-filtered-rag
**Tags:** [permissions, rag, phi]

RAG retrieval is not protected by a single patient permission check. Any evidence query that joins patient, document, page, and chunk data must prove ownership and lifecycle state at every joined layer before ranking or sending context to an LLM. Add adversarial tests for revoked permissions, expired permissions, soft-deleted rows, mismatched document ownership, and mismatched page-document ownership.

**Full entry:** history/learnings/20260428-backend-permission-rag-safety.md

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
