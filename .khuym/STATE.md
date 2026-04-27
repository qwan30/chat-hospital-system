# STATE
focus: backend permission-filtered RAG review
phase: executed-review-p1-p2-hardening
last_updated: 2026-04-28

notes:
- Khuym onboarding is complete.
- Full review bead workflow is degraded because `br` and `bv` are not available.
- No `history/<feature>/CONTEXT.md` or `history/<feature>/approach.md` exists for this review.
- Review was performed against the current backend artifacts and local verification output.
- Direct execution fixed the P1/P2 review findings for active permissions, failed re-index preservation, and pgvector migration fail-fast behavior.
- Verification: `python -m pytest` passed with 18 tests; `python -m ruff check .` could not run because `ruff` is not installed.
- Reviewing found a P1 blocker: retrieval does not filter soft-deleted documents, pages, or chunks before returning RAG evidence.
- Review beads could not be created because `br`/`bv` are unavailable; learnings candidates are recorded in `.khuym/findings/learnings-candidates.md`.
- Direct execution fixed the P1 blocker by filtering soft-deleted documents, pages, and chunks in both retrieval paths.
- Verification: `python -m pytest` passed with 21 tests; `python -m ruff check .` could not run because `ruff` is not installed.
- Direct execution fixed P2 review items for raw SQL scope drift, re-index generation races, changed-source stale index exposure, indexing-failure coverage, PostgreSQL integration-test scaffolding, and active patient-search coverage.
- Verification: `python -m pytest` passed with 25 tests and 2 optional PostgreSQL tests skipped; `python -m ruff check .` could not run because `ruff` is not installed.
- Direct execution fixed the P3 drift-prevention item by centralizing active patient-permission filters and sharing the raw SQL permission fragment with PostgreSQL retrieval.
- Verification: focused permission and retrieval tests passed with 15 tests and 2 optional PostgreSQL tests skipped; full `python -m pytest` passed with 26 tests and 2 optional PostgreSQL tests skipped.
- `khuym:reviewing` automated specialist review found 2 P1 blockers: duplicate Alembic column additions across `0001`/`0002`, and RAG retrieval not enforcing document/page ownership against the requested patient when chunk ownership drifts.
- `khuym:reviewing` also found P2 follow-ups: embedding count mismatch can mark incomplete indexes as successful; unknown source hash can preserve stale indexed content; PostgreSQL retrieval lacks the portable null-embedding guard; source hashing reads raw `storage_uri` paths; PostgreSQL/Alembic/concurrency coverage remains optional or simulated.
- Review beads could not be created because `br`/`bv` remain unavailable; Phase 2 artifact verification and Phase 3 UAT are blocked by P1 gate and missing `history/<feature>/CONTEXT.md` / `approach.md`.
- Direct execution fixed the P1 blockers and adjacent P2 runtime issues: Alembic column duplication, document/page ownership checks in both retrieval paths, PostgreSQL null-embedding guard, embedding count mismatch detection, storage-root-constrained source hashing, and unknown-source failure handling.
- Verification: focused review-fix tests passed with 20 tests and 2 optional PostgreSQL tests skipped; full `python -m pytest` passed with 31 tests and 2 optional PostgreSQL tests skipped; `python -m ruff check .` could not run because `ruff` is not installed.
