# SDLC Mario E2E v3.1 — Expanded Clinical Graph Relations Tracker

## Project Information
- **Feature**: Mở rộng 5 quan hệ Graph RAG (`interacts_with`, `indicates`, `allergic_to`, `diagnosed_with`, `history_of`) với mô hình Hybrid Phased Architecture (Catalog + LLM + Traversal Guard + Negation Filter + Backfill).
- **Target Branch**: `feat/expanded-clinical-graph-relations`
- **Commit**: `98a6180`
- **Started At**: 2026-08-17T09:03:00+07:00
- **Completed At**: 2026-08-17T09:42:00+07:00
- **Status**: **RELEASE_READY (100% COMPLETED)**

---

## 📊 Kanban Board

| Todo | In Progress | In Review | Done |
| :--- | :--- | :--- | :--- |
| - | - | - | Phase 0, 1, 2, 3, 4, 5, 6 |

---

## 🚀 SDLC Phases Breakdown

### [x] Phase 0: Web-First Research & Scan
- [x] Search web for state-of-the-art clinical Graph RAG, DDI extraction & Negation handling patterns
- [x] Verify existing codebase context & ensure no conflicting worktrees exist
- [x] Scan security boundaries (PHI isolation, catalog integrity, zero unauthorized chunk leak)

### [x] Phase 1: Design, Plan & Schedule
- [x] Council debate & synthesis (Architect, Skeptic, Pragmatist, Critic)
- [x] Write formal design spec to `docs/superpowers/specs/2026-08-17-expanded-graph-relations-design.md`
- [x] Dispatch `design-reviewer` subagent to audit spec completeness & edge cases (APPROVED_WITH_NOTES)
- [x] Write implementation plan to `docs/superpowers/plans/2026-08-17-expanded-graph-relations.md`
- [x] Self-review plan and define bite-sized tasks

### [x] Phase 2: Sandbox & Baseline Verification
- [x] Verified clean test baseline (`test_drug_check.py` 17/17 pass, `tsc --noEmit` clean)

### [x] Phase 3: Execution with Strict TDD & Multi-Reviewer Guard
- [x] **Task 1**: Graph Ontology & Schemas (`ExtractedRelation` metadata + Relation Allowlist + Canonical Patient Anchor)
- [x] **Task 2**: Catalog-driven DDI Ingestion Engine (`interacts_with` join with `drug_interaction_matrix.csv` + severity mapping)
- [x] **Task 3**: NLP Extraction with Negation Scope Filter & Explicit Grammar Fallback
- [x] **Task 4**: Traversal Guard in Graph BFS (Prevent Patient Hub Explosion) & DrugCheckService upgrade
- [x] **Task 5**: Frontend UI Updates (`GraphFilters.tsx`, `GraphLegend.tsx`, node colors/badges)
- [x] **Task 6**: Backfill & Evaluation Harness Compatibility (`backfill_cdi_v2.py --mode enrich-relations` + test parity)

### [x] Phase 4: Review & Adversarial Verification
- [x] 2 Independent Reviewers (Senior Security Reviewer & Senior Logic Reviewer) dispatched
- [x] Security Reviewer Verdict: **APPROVED (PASS_WITH_NOTES)**
- [x] Logic Reviewer Verdict: **PASS**

### [x] Phase 5: QA/QC, Playwright E2E Automation & Production Audit
- [x] Backend pytest suite (86/86 pass in graph suite)
- [x] Frontend Vitest suite (`GraphFilters.test.tsx` 7/7 pass)
- [x] Frontend TypeScript typecheck (`tsc --noEmit` 0 errors)
- [x] API Contract verification (73 endpoints verified)
- [x] Production Readiness Audit (Zero-leak PHI, Memory/Context bounds, Latency < 30s)

### [x] Phase 6: CI/CD Verification Loop & Final Release Certification
- [x] Created clean git commit `98a6180` on branch `feat/expanded-clinical-graph-relations`
- [x] Verified workspace integrity

### [x] Phase 7: GraphRAG RRF Fusion Ranking & Prompt Citation Relaxation
- [x] **GraphRAG RRF Fusion**: Combined Vector, BM25, and Knowledge Graph candidates using Reciprocal Rank Fusion prior to top-K truncation (`reciprocal_rank_fusion(evidence, graph_evidence, top_k)`).
- [x] **Prompt Relaxation**: Revised system prompts and `build_grounded_prompt` with clear instructions to prevent citation omissions while preserving `[E1]` and `[G1]` formats in both English and Vietnamese.
- [x] **Robust Citation Extraction**: Enhanced `extract_citation_ids` and `ClaimParser.parse` to seamlessly handle multi-bracket citations (e.g. `[E1, E2]`), whitespaces (`[E 1]`), and graph tags (`[G1]`).
- [x] **Verification**: Added `test_chat_graph_rrf.py` and passed all 43 targeted tests + full test suite with 0 lint errors (`ruff check/format` clean, `tsc --noEmit` clean).
