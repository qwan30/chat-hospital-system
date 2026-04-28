## Candidate: shared-chat-workspace-state
Category: pattern
Tags: [frontend, chat, state, shared-threads, react]
Summary: Chat workspace slices that look independent still need one active workspace model once thread selection, transcript, patient context, evidence, and composer behavior affect each other. Local component state is acceptable for static mock display, but it becomes a bug as soon as the sidebar claims an active thread while the transcript and evidence panel still read a separate sample active thread.
Evidence: Code-quality and architecture findings overlap on the same root issue: `ConversationSidebar` owns `activeThreadId` locally while `ChatTranscript` reads `sampleWorkspaceState.activeThreadId`, and `AssistantShell` renders independent children with no shared active-thread or patient-context model. Locked D8 requires shared chat threads, and `approach.md` already marks shared conversation threads as high risk because persistence and sharing can leak patient-linked evidence if scoped badly.
Recommended title: 20260428-shared-chat-workspace-state.md

## Candidate: citation-evidence-fidelity-boundary
Category: failure
Tags: [frontend, citations, evidence, permissions, phi, rag]
Summary: Citation adapters and evidence panels must preserve backend evidence detail and permission status instead of thinning citations into display-only chips or sample-bound panels. The UI can otherwise look safe while losing the document/page/chunk/score/content/metadata needed to verify claims and enforce patient-linked evidence boundaries.
Evidence: Architecture found that `BackendChatCitation` includes document, page, chunk, score, content, and metadata, but `mapBackendCitation` returns only thin chip fields and `EvidencePanel` remains sample-bound. This directly matches the promoted learning "RAG Evidence Requires Full Join-Chain Authorization": evidence and citation flows are authorization-chain problems, not just visual source labels. Because Phase 1 is still UI/sample-heavy and security found no direct leak, this stays P2 rather than escalating to P1, but it should be treated as a known-risk review bead.
Recommended title: 20260428-citation-evidence-fidelity-boundary.md

## Candidate: executable-chat-contract-tests
Category: pattern
Tags: [testing, contracts, frontend, backend-adapter, permissions]
Summary: Contract adapters around patient-scoped chat should get executable tests before more UI is built on top of them. Validation helpers that allow whitespace-only questions or invalid `topK` values are small bugs now, but they become harder to unwind once composer submission, patient scope, citation rendering, and failure states are wired together.
Evidence: Code-quality found that `prepareVerifiedBackendChatRequest` does not trim or reject whitespace-only questions or invalid `topK`; test-coverage separately called for unit tests around patient-scoped chat request and response adapters plus composer submit-flow tests. The previous learning "Optional Production-Path Tests Are Not Enough for PHI Boundaries" applies by analogy: fast UI/unit tests are useful, but patient-scoped request and evidence behavior must be executable, not assumed from types.
Recommended title: 20260428-executable-chat-contract-tests.md

## Candidate: general-chat-retrieval-separation
Category: pattern
Tags: [backend, rag, permissions, phi, general-knowledge]
Summary: General-mode chat must be retrieval-separated from patient evidence. A general hospital question should not call patient retrieval, should not create a patient-scoped `AiQuery`, should keep `patient_id` null, and should cite only explicitly approved non-PHI sources.
Evidence: The Phase 1/2 review found a positive match with the promoted "RAG Evidence Requires Full Join-Chain Authorization" pattern. The new general path avoids patient retrieval entirely and the added leak test indexes a patient allergy document before proving the general answer path does not return patient chunks.
Recommended title: 20260428-general-chat-retrieval-separation.md

## Candidate: hms-evidence-lineage-before-ranking
Category: decision
Tags: [hms, rag, permissions, evidence-lineage, phi]
Summary: Before HMS-derived data reaches ranking or an LLM context, the integration must define approval state, patient ownership, lifecycle state, source lineage, and permission gates as executable checks. Treat HMS integration as a join-chain authorization problem from the start.
Evidence: The reviewing learnings pass flagged Phase 3 as the next place where the existing "RAG Evidence Requires Full Join-Chain Authorization" failure mode can recur. This should shape the Phase 3 plan before any HMS import/API path is implemented.
Recommended title: 20260428-hms-evidence-lineage-before-ranking.md
