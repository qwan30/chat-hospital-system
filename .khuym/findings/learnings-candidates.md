# Learnings Candidates

## Candidate: permission-filtered-rag-soft-delete-filters
Category: failure
Tags: backend, permissions, rag, phi, soft-delete
Summary: Permission-filtered RAG retrieval must filter lifecycle state at every joined layer, not only patient permissions.
Evidence: `app/backend/src/hospital_ai/services/retrieval.py`
Recommended title: 20260427-permission-filtered-rag-soft-delete-filters.md

## Candidate: raw-sql-permission-policy-drift
Category: pattern
Tags: backend, permissions, sql, rag
Summary: Shared permission constants are insufficient when raw SQL hardcodes the same policy in a separate source of truth.
Evidence: `app/backend/src/hospital_ai/services/retrieval.py`
Recommended title: 20260427-raw-sql-permission-policy-drift.md

## Candidate: reindex-source-version-contract
Category: decision
Tags: backend, indexing, workers, reliability
Summary: Reindexing needs a source/version ownership contract before preserving stale searchable chunks after failure.
Evidence: `app/backend/src/hospital_ai/workers/jobs.py`
Recommended title: 20260427-reindex-source-version-contract.md
