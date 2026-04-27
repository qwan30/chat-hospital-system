# STATE
focus: backend permission-filtered RAG review
phase: executed-p2-retrieval-indexing-hardening
last_updated: 2026-04-27

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
