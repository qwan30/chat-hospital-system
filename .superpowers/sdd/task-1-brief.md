# Task 1: Apply the Unified Clinical Document Intelligence V2 Spec Amendment

## Scope

Update only:

`docs/superpowers/specs/2026-08-04-unified-clinical-document-intelligence-v2-design.md`

The plan is a spec-only revision. Do not implement database, API, frontend, worker, OCR, R2, Graph RAG, migration, or chat code. Do not modify `AGENTS.md`, `CLAUDE.md`, the plan file, `docs/superpowers/plans/New Text Document.txt`, or any other file.

## Required amendment

Make the document a normative V2 amendment that preserves the current V1 architecture and closes the following blockers:

- Define an authority map: V1 remains authoritative for roles, input formats, observability, and deployment; V2 replaces or extends revision, generation, Graph RAG, R2 versioning, streaming/evidence, and benchmark behavior.
- Remove `tenant_id` from V2. Keep patient permission, existing roles, and deployment boundary as the security boundary; do not add a new role.
- Separate `approved_revision_set_id`, `active_index_generation_id`, and mutable `document_draft_heads` with `lock_version`. Page saves create immutable page revisions; submit freezes a revision set; approval builds a generation and only supersedes the prior generation after the new one is active.
- Define `document_index_generations` with revision-set FK, `building | active | failed | superseded` states, stage results, hashes, timestamps, and failure behavior that preserves the old active pointer.
- Define `ocr_blocks`, `ocr_lines`, and `ocr_spans` with offsets, polygon, confidence, reading order, and `alignment_status = aligned | partially_aligned | stale`; edited text must not reuse stale geometry as exact evidence.
- Define patient-scoped `graph_entities`, `graph_mentions`, `graph_relation_assertions`, and `graph_relation_evidence`; canonical entities must support multiple independent provenance sources.
- Define upload lifecycle `pending_upload → uploaded_unverified → quarantined | verified → finalized | rejected`; only finalized objects can enter OCR.
- Require immutable unique object keys, conditional PUT `If-None-Match: *`, HEAD verification, SHA-256, byte size, magic-byte MIME validation, malware/quarantine result, and atomic finalization. Clarify raw OCR retention versus authorized hard-delete with a non-PHI audit tombstone.
- Define capability grants using existing roles only: `document_revision.view_raw`, `.edit`, `.reject`, `.approve`, `.restore`, `ocr_engine.override`, and `superseded_evidence.read`, including patient-permission gating, production `editor_id != approver_id`, and the constrained synthetic-data self-approval flag.
- Define all `/api/v1` upload, revision-set, draft, approval/rejection/restore, retry, graph, and timeline contracts named by the plan. All write APIs require `Idempotency-Key`; draft writes also require `If-Match`; document 201/202/403/409/422 and audit/retry behavior.
- Preserve SSE event `token` as validated output chunks, add `sequence`, `validation_mode: sentence_buffered`, fixed event ordering, terminal `done`, interrupted persistence, and a prohibition on raw model tokens reaching clients.
- Specify migration order, legacy read-path preservation until backfill/parity checks pass, active-generation rollback by pointer only, and no automatic approval of real data.
- Add the acceptance scenarios in the plan: stale editor conflict, no self-approval, failed generation preserving A, stale edited geometry, multi-source canonical entity, cross-path wrong-patient/superseded filtering, upload validation/finalization, validated SSE sequencing/interrupted persistence, and legacy synthetic citation/retrieval parity.
- Require benchmark threshold artifacts to be versioned and frozen after qualification and before holdout; remove any claim that the checklist has no placeholders until that artifact exists.
- Preserve the locked assumptions: spec-only revision, V2 remains an amendment rather than V3, multi-tenancy out of scope, existing roles only, and PR #87 remains closed with no mutation to it.

## Quality and delivery

- Preserve the existing spec's useful architecture and references; resolve contradictions and vague authority/status language instead of deleting needed requirements.
- Do not claim that any behavior is implemented or production-ready.
- Run `git diff --check` and a focused Markdown/link/heading sanity check if available. No application test suite is required for a documentation-only change.
- Commit only the target spec file with an imperative `docs:` commit message. Do not stage unrelated dirty or untracked files.

## Report

The repository already contains an unrelated stale report at `.superpowers/sdd/task-1-report.md`; preserve it. Write the detailed report for this task to:

`.superpowers/sdd/task-1-report-v2.md`

Include changed file, summary of the amendment, checks and exact results, commit SHA/subject, self-review, and any concerns. Return only status, commit, one-line check summary, concerns, and report path in the final message.
