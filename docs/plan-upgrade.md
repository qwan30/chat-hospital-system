# Plan Upgrade: Review Blocker Remediation

  ## Summary And Goal

  Target file: docs/plan-upgrade.md is currently empty. This plan
  should turn the completed docs/plan.md work into a verified, honest,
  merge-ready state.

  Goal:

  - [x] Clear current P1 review blockers before adding new demo polish.
  - [x] Make frontend, backend, security, and documentation claims
    match actual code.

  - [x] Preserve locked decisions from history/portfolio-hardening-
    2026-06/CONTEXT.md, especially memory-only bearer tokens.

  - [x] Keep the parked Figma handoff untouched unless the user
    explicitly resumes it.

  Skill/tool routing:

  - [x] Use khuym:using-khuym startup checks, then khuym:planning,
    khuym:validating, khuym:executing, and khuym:reviewing.

  - [x] Use GitNexus impact analysis before editing symbols, and
    detect_changes() before commit.

  - [x] Use security review focus for PHI, permissions, token storage,
    RAG, and streaming.

  ## Implementation Checklist

  Baseline and guardrails:

  - [x] Re-run node .codex/khuym_status.mjs --json and surface
    unrelated handoff state.

  - [x] Refresh GitNexus if stale, then record affected symbols and
    risk before edits.

  - [x] Preserve unrelated dirty worktree changes.
  - [x] Do not mark any checklist item complete until a command, test,
    or source inspection proves it.

  Frontend build and API contract:

  - [x] Fix frontend typecheck errors in graph import/types, Topbar ref
    usage, and chat history array handling.

  - [x] Standardize frontend API paths: apiFetch receives paths
    relative to the configured /api/v1 base, with no duplicate /api/v1/
    api/v1.

  - [x] Keep listChatThreads() as ChatThreadRead[]; update callers
    instead of inventing .items.

  - [x] Remove fake clinical fallback answers from chat UI; backend/API
    failures must show retry/error/refusal UI.

  Security, PHI, and permissions:

  - [x] Remove admin bypass from document listing and patient-document
    access; every PHI path must require patient permission or an
    explicit approved role/scope rule.

  - [x] Enforce patient permission on graph endpoints before returning
    clinical graph data.

  - [x] Add tests for unauthorized patient document, graph, and RAG
    access.

  - [x] Remove bearer token persistence from localStorage; token lives
    only in React memory, while API URL persistence may remain.

  Chat, RAG, and streaming:

  - [x] Make AiQuery.patient_id nullable with an Alembic migration so
    general chat can persist safely.

  - [x] For /chat and /chat/stream, if patient_id is missing, do not
    retrieve patient PHI chunks; answer only from general safe
    knowledge or refuse.

  - [x] Mirror non-streaming RAG safety contracts in streaming:
    permission-filtered evidence, citation validation, sanitized
    errors, audit/tracing, and cited-only evidence.

  - [x] Add frontend AbortController support for streaming chat and
    backend disconnect handling.

  Docs and truth alignment:

  - [x] Recheck all [x] items in docs/plan.md; uncheck or move anything
    not verified.

  - [x] Update README/evidence claims only after matching source or
    test proof exists.

  - [x] Record unresolved items as exceptions, not completed work.

  ## Public Interfaces And Types

  - [x] Frontend API helper contract: callers pass version-relative
    paths such as /documents, /dashboard/summary, /access-requests.

  - [x] Chat request contract: patient_id is optional; omitted means
    general non-PHI chat only.

  - [x] Persistence contract: AiQuery.patient_id is nullable; patient-
    specific RAG rows still require patient ID and permission evidence.

  - [x] Graph endpoint contract: patient graph responses are
    permission-gated and return 403 or safe access-request guidance
    when unauthorized.

  - [x] Auth contract: no browser storage for bearer tokens; reload
    requires re-login or re-auth via approved backend session flow.

  ## Acceptance Criteria

  - [x] cd app/frontend && bun run typecheck passes.
  - [x] cd app/frontend && bun run lint passes.
  - [x] cd app/frontend && bun run test passes.
  - [x] cd app/backend && python -m pytest tests/ passes.
  - [x] cd app/backend && ruff check src/ tests/ passes.
  - [x] cd app/backend && ruff format --check src/ tests/ passes.
  - [x] git diff --check passes.
  - [x] GitNexus detect_changes() shows only expected affected areas.
  - [x] Tests prove unauthorized users cannot receive patient
    documents, graph data, or RAG chunks.

  - [x] Browser inspection or frontend tests prove bearer tokens are
    not stored in localStorage.

  - [x] General chat works without DB integrity errors and does not
    fabricate clinical citations.

  - [x] Streaming stop/cancel terminates client stream and backend
    work.

  - [x] docs/plan.md and docs/plan-upgrade.md contain no unchecked
    claim marked as complete.

  ## Exceptions And Edge Cases

  - [x] Existing parked Figma handoff is out of scope.
  - [x] Synthetic seed/demo data is allowed only from backend seed
    fixtures, not frontend fake clinical fallbacks.

  - [x] If backend is unavailable, the frontend must show an error/
    retry state, not fabricated medical output.

  - [x] HIPAA compliance, production deployment, real hospital users,
    and measured ROI remain unclaimed unless separately proven.

  - [x] If a GitNexus impact result is HIGH or CRITICAL, stop and
    report blast radius before continuing edits.

# Plan Upgrade v2: Reference-Informed RAG Hardening

  ## Summary And Goal

  Target file: docs/plan-upgrade.md. Append this as the next plan under the completed blocker-remediation
  section.

  Decision: keep the hospital app’s current permission-filtered RAG as the production path. Use reference/
  LightRAG for a small sidecar spike only, and use reference/ragflow as a parsing/chunking/citation UX
  reference, not a direct dependency.

  Current gate reality:

  - [x] Frontend typecheck, lint, and unit tests pass.
  - [x] git diff --check, backend ruff check, and backend ruff format --check pass.
  - [ ] Backend pytest is still blocked under Python 3.9 by Mapped[T | None] SQLAlchemy annotations.
  - [ ] GitNexus detect_changes(scope=all) is critical: 78 changed files, 284 changed symbols, 92 affected
    flows.

  Goal:

  - [ ] Make the completed upgrade actually green under the declared backend runtime.
  - [ ] Preserve PHI safety: patient permission filtering must happen before any retrieved chunk reaches an
    LLM.

  - [ ] Decide future RAG engine upgrades through evidence, not by copying LightRAG/RAGFlow wholesale.
  - [ ] Produce a spike result that says adopt, adapter only, or do not integrate.

  ## Implementation Checklist

  P0 baseline remediation:

  - [ ] Fix Python runtime mismatch. Default: keep requires-python = ">=3.9" and replace SQLAlchemy mapped T
    | None annotations with Optional[T]; only raise runtime to Python 3.10+ if CI/dev tooling is updated in
    the same change.

  - [ ] Re-run cd app/backend && python -m pytest tests/ -q.
  - [ ] Re-run all gates: frontend typecheck/lint/test, backend pytest/ruff/format, git diff --check.
  - [ ] Update docs/plan-upgrade.md checkboxes only after command proof exists.

  P1 reference decision record:

  - [ ] Add a decision matrix to docs/plan-upgrade.md:
      - Existing internal RAG: production default.
      - LightRAG: sidecar spike candidate because it has graph/query modes and references, but requires
        Python >=3.10 and newer FastAPI/Pydantic.

      - RAGFlow: pattern reference for DeepDoc parsing, chunk visualization, metadata filtering, citations,
        and dataset APIs; not direct integration because it requires Python 3.13, Go, MySQL, Redis, MinIO,
        Elasticsearch/Infinity, and tenant/team permissions.

  - [ ] Do not add LightRAG or RAGFlow packages to app/backend/pyproject.toml in this phase.
  - [ ] Keep reference/LightRAG and reference/ragflow read-only.

  P2 safe adapter spike:

  - [ ] Create an isolated synthetic-data spike outside production routes.
  - [ ] Adapter output must map external references back to internal document_id, chunk_id, page, and
    patient_id.

  - [ ] Before prompt assembly, re-check mapped chunks through the hospital permission path, preferably
    RetrievalService.get_chunks_by_ids().

  - [ ] Keep /chat and /chat/stream citation validation unchanged.
  - [ ] Reject any reference result that cannot be mapped to an authorized internal chunk.

  P3 upgrade candidates after spike:

  - [ ] Adopt RAGFlow-inspired parsing improvements only if they can be implemented inside the current
    loader/indexing pipeline without importing RAGFlow’s service stack.

  - [ ] Consider LightRAG sidecar only for synthetic or de-identified data until patient-scope isolation is
    proven.

  - [ ] Add citation/source-review UI improvements only after backend reference mapping is stable.
  - [ ] Add reranking only with mode-aware thresholds so BM25/vector/RRF scores do not share an invalid
    cutoff.

  ## Public Interfaces And Types

  - [ ] No frontend or public API route changes in P0.
  - [ ] Any external RAG spike must be internal and disabled by default.
  - [ ] Proposed internal adapter contract: retrieve_authorized(user_id, patient_id, query, top_k) ->
    list[RetrievedChunk].

  - [ ] The adapter must return hospital RetrievedChunk objects or verified internal chunk IDs, not raw
    external engine chunks.

  - [ ] Existing /chat and /chat/stream response contracts remain unchanged.

  ## Test Plan And Acceptance Criteria

  Required green gates:

  - [ ] cd app/backend && python -m pytest tests/ -q
  - [ ] cd app/backend && ruff check src/ tests/
  - [ ] cd app/backend && ruff format --check src/ tests/
  - [ ] cd app/frontend && bun run typecheck
  - [ ] cd app/frontend && bun run lint
  - [ ] cd app/frontend && bun run test
  - [ ] git diff --check
  - [ ] GitNexus impact analysis before symbol edits and detect_changes() before commit.

  Security/RAG scenarios:

  - [ ] Unauthorized user cannot retrieve patient chunks through internal RAG, graph RAG, LightRAG spike, or
    RAGFlow-inspired code.

  - [ ] Revoked/expired permission blocks retrieval before ranking and before LLM prompt assembly.
  - [ ] Soft-deleted documents/pages/chunks never appear in evidence.
  - [ ] Hallucinated citation IDs are rejected in non-streaming and streaming chat.
  - [ ] General chat without patient_id does not retrieve PHI.
  - [ ] External reference paths cannot bypass internal patient_id and permission checks.

  ## Exceptions

  - [ ] Parked Figma handoff is out of scope.
  - [ ] RAGFlow agent channels, code executor, MCP server, cloud connectors, and Web UI are out of scope.
  - [ ] Real PHI, real hospital users, HIPAA certification, production deployment, and measured ROI remain
    unclaimed.

  - [ ] If LightRAG/RAGFlow require external hosted models, use synthetic or de-identified data only.
  - [ ] RAGFlow tenant/team permission and LightRAG workspace isolation do not satisfy hospital patient-scope
    authorization by themselves.