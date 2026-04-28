---
date: 2026-04-28
feature: backend-permission-filtered-rag
categories: [pattern, decision, failure]
severity: critical
tags: [backend, permissions, rag, phi, indexing, migrations, testing, khuym]
last_dream_consolidated_at: 2026-04-28T00:23:02+07:00
---

# Learning: RAG Evidence Requires Full Join-Chain Authorization

**Category:** failure
**Severity:** critical
**Tags:** [permissions, rag, phi]
**Applicable-when:** Any retrieval path joins patient, document, page, chunk, or evidence rows before sending context to an LLM.

## What Happened

The retrieval hardening initially fixed active patient permissions, but later review found more PHI leakage paths. Soft-deleted documents, pages, and chunks needed explicit filters, and a mismatched `document_chunks.patient_id` could still point to another patient's document or page. The original backend-slice planning prompt included a permission-filtered SQL shape, but that plan only covered the first-order patient permission and chunk patient filters; the final fix had to expand both PostgreSQL SQL and portable SQLAlchemy retrieval to prove the full evidence chain: active permission, requested chunk patient, matching document patient, matching page-document relationship, indexed document state, lifecycle filters, and non-null embedding.

## Root Cause / Key Insight

RAG retrieval is not protected by a single patient permission check. It is an evidence-chain authorization problem, and denormalized ownership fields can drift through migrations, repair scripts, worker races, or compromised internal writes.

## Recommendation for Future Work

Always enforce ownership and lifecycle predicates at every joined evidence layer before ranking or passing context to an LLM. During planning, reject "canonical SQL" examples that do not already include adversarial PHI cases. Add tests for revoked permissions, expired permissions, soft-deleted rows, mismatched document ownership, and mismatched page-document ownership before implementation.

---

# Learning: Raw SQL Permission Policy Needs an Executable Contract

**Category:** pattern
**Severity:** critical
**Tags:** [permissions, sql, testing]
**Applicable-when:** Any security, tenancy, or PHI boundary is implemented in raw SQL as well as ORM queries.

## What Happened

The ORM permission helper was the canonical active permission check, but PostgreSQL retrieval used hand-written SQL and drifted from that policy. The work centralized active permission logic in `services/permissions.py`, reused a raw SQL fragment from retrieval, and added SQL contract tests for active scope, soft-delete, expiry, and accepted scope binding.

## Root Cause / Key Insight

Shared constants are not enough when the behavior lives in separate query languages. Raw SQL must either be generated from a shared source or protected by explicit invariant tests that fail when security predicates drift.

## Recommendation for Future Work

When a policy appears in raw SQL, import or generate it from the same module as the ORM predicate, then add tests that inspect and execute the production SQL path. Do not rely on a portable ORM test to prove a raw PostgreSQL query is safe.

---

# Learning: Re-index Preservation Needs a Source and Generation Contract

**Category:** decision
**Severity:** critical
**Tags:** [indexing, workers, reliability]
**Applicable-when:** Any background job replaces searchable rows, derived data, or cached evidence after an earlier successful index exists.

## What Happened

Re-indexing originally deleted existing chunks before proving that OCR and embeddings would succeed. The fix added `index_generation`, `indexed_source_sha256`, row locking, and failure behavior that preserves old searchable chunks only when the source hash is known and unchanged. Later review tightened the rule so unknown or out-of-storage source hashes fail closed instead of preserving stale searchable evidence.

## Root Cause / Key Insight

Preserving old derived data is safe only when the worker can prove it still represents the current source. Async retries also need a generation check so stale workers cannot overwrite newer index output.

## Recommendation for Future Work

For any replacement index or derived-data job, compute a source fingerprint before work starts, lock or version the target before swapping rows, and preserve old rows only when the source fingerprint is known and matches. Treat unknown source identity, embedding count mismatch, and stale generation as indexing failures.

---

# Learning: Migration Chains Need One Schema Source of Truth

**Category:** failure
**Severity:** critical
**Tags:** [database, migrations, testing]
**Applicable-when:** Adding columns or constraints after an initial Alembic migration already exists.

## What Happened

`index_generation` and `indexed_source_sha256` were added to the initial migration and also added again in a forward migration. Review caught this as a P1 because a clean `alembic upgrade head` could create the columns in `0001` and fail on duplicate columns in `0002`. The fix removed the columns from `0001`, kept the forward migration as the source of truth, and added a regression test that prevents the duplication from returning.

## Root Cause / Key Insight

Model metadata tests can pass while the deployed migration chain is broken. Editing a base migration and adding a forward migration for the same schema change creates two incompatible histories.

## Recommendation for Future Work

Never back-edit an existing base migration with fields also introduced by a later revision unless the project is explicitly squashing migrations. Add migration-chain or migration-content tests whenever schema changes are made during a feature.

---

# Learning: Optional Production-Path Tests Are Not Enough for PHI Boundaries

**Category:** failure
**Severity:** standard
**Tags:** [testing, postgres, rag]
**Applicable-when:** A feature has a fast portable test path and a separate production database or integration path.

## What Happened

The backend suite passed locally while PostgreSQL retrieval tests were skipped unless `HOSPITAL_AI_TEST_POSTGRES_URL` was configured. SQLite tests and SQL string assertions caught many regressions, but they cannot fully prove pgvector operators, PostgreSQL bind behavior, row locking, or Alembic upgrades.

## Root Cause / Key Insight

Fast local tests are useful for feedback, but production-only behavior remains unverified without a required integration environment. This matters more when the code path is the PHI boundary.

## Recommendation for Future Work

Keep portable tests for fast iteration, but require PostgreSQL and pgvector integration tests in CI before merging retrieval, migration, or worker-locking changes. If the environment is unavailable locally, report it as an explicit verification gap rather than treating skipped tests as proof.

---

# Learning: Degraded Khuym Runs Need Durable State Immediately

**Category:** pattern
**Severity:** standard
**Tags:** [khuym, process, coordination]
**Applicable-when:** Khuym bead tools, feature context files, or Agent Mail coordination are unavailable during execution or review.

## What Happened

The feature ran in degraded Khuym mode because `br` and `bv` were unavailable and `history/backend-permission-filtered-rag/CONTEXT.md` / `approach.md` did not exist. Progress was still recoverable because `.khuym/STATE.md`, `.khuym/state.json`, `.khuym/findings/learnings-candidates.md`, commits, and verification output recorded the current state.

## Root Cause / Key Insight

When the normal work graph is absent, chat history alone is too fragile. State files become the only durable routing mirror for review, execution, and compounding.

## Recommendation for Future Work

At the first sign of degraded Khuym tooling, record the missing prerequisites, active phase, review findings, verification commands, and current blockers in `.khuym/STATE.md` and `.khuym/state.json`. Keep fixes narrow and commit each hardening slice with tests so later agents can reconstruct the feature from git and state files.
