# Expanded 10-Relation Clinical Graph RAG Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand the Hospital Knowledge Assistant's Graph RAG ontology from 5 to 10 standard clinical relations using a safe hybrid architecture (Deterministic DDI Catalog Join + Negation-Aware Extraction + Traversal Guard + UI Badges + Fast Backfill).

**Architecture:** Hybrid deterministic-catalog join for drug-drug interactions with symmetric indexing, negation-scoped NLP extraction for diagnoses/allergies, canonical patient anchor `patient:self` with BFS traversal guard to prevent graph hub explosion, and UI filter controls in React.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy 2.0 (async), PostgreSQL / SQLite, React 19, Vite, TanStack Router, Tailwind CSS, Lucide Icons, Pytest, Vitest, Playwright.

## Global Constraints
- Strictly enforce patient-scoped data isolation (Zero PHI leakage).
- All DDI entries from `drug_interaction_matrix.csv` preserve catalog-calibrated severity with symmetric pair matching.
- Negation assertions (e.g. "NKDA", "denies", "no history of", "ruled out") MUST NEVER create affirmative graph edges.
- `patient:self` is non-expandable in BFS traversal to avoid combinatorial hub explosion.
- Minimum backend and frontend test coverage: 80%+.

---

### Task 1: Core Ontology, Schemas & Canonical Patient Anchor

**Files:**
- Modify: `app/backend/src/hospital_ai/services/graph_rag.py:40-100`
- Test: `app/backend/tests/test_graph_rag_ontology.py`

**Interfaces:**
- Produces: `VALID_RELATION_TYPES`, `CANONICAL_PATIENT_ANCHOR = "patient:self"`, `ExtractedRelation` with `severity` and `source_layer`.

- [ ] **Step 1: Write the failing test**
Create `app/backend/tests/test_graph_rag_ontology.py` asserting validation of all 10 relation types and schema fields.

- [ ] **Step 2: Run test to verify it fails**
Run: `cd app/backend && python -m pytest tests/test_graph_rag_ontology.py -v`
Expected: FAIL (missing fields or allowlist)

- [ ] **Step 3: Implement minimal ontology additions**
Update `ExtractedRelation` and define `VALID_RELATION_TYPES` in `services/graph_rag.py`.

- [ ] **Step 4: Run test to verify it passes**
Run: `cd app/backend && python -m pytest tests/test_graph_rag_ontology.py -v`
Expected: PASS

---

### Task 2: Deterministic Drug Interaction Catalog Matcher with Symmetric Indexing

**Files:**
- Create: `app/backend/src/hospital_ai/services/drug_catalog.py`
- Modify: `app/backend/src/hospital_ai/services/graph_rag.py:260-320`
- Test: `app/backend/tests/test_drug_catalog.py`

**Interfaces:**
- Consumes: `app/backend/data/drugs/drug_interaction_matrix.csv`
- Produces: `find_catalog_interactions(text: str) -> list[ExtractedRelation]` and `get_catalog_interaction(drug_a: str, drug_b: str) -> Optional[CatalogInteraction]` with bidirectional matching.

- [ ] **Step 1: Write the failing test**
Create `app/backend/tests/test_drug_catalog.py` testing drug pair matching (Warfarin + Aspirin & Aspirin + Warfarin symmetric lookup).

- [ ] **Step 2: Run test to verify it fails**
Run: `cd app/backend && python -m pytest tests/test_drug_catalog.py -v`
Expected: FAIL

- [ ] **Step 3: Implement `drug_catalog.py`**
Load CSV at startup/cached singleton with sorted tuple keys `(min(d1, d2), max(d1, d2))` and provide fast tokenized drug pair lookups.

- [ ] **Step 4: Run test to verify it passes**
Run: `cd app/backend && python -m pytest tests/test_drug_catalog.py -v`
Expected: PASS

---

### Task 3: Negation-Aware Clinical NLP & Fallback Grammar

**Files:**
- Modify: `app/backend/src/hospital_ai/services/graph_rag.py:100-260`
- Test: `app/backend/tests/test_graph_negation_extraction.py`

**Interfaces:**
- Consumes: Raw clinical text
- Produces: Filtered affirmative relations, rejecting NKDA, denials, and ruled-out diagnoses while extracting confirmed diagnoses/allergies.

- [ ] **Step 1: Write the failing test**
Test cases:
- "Patient has no known drug allergies (NKDA)" -> 0 allergy edges.
- "Denies history of asthma" -> 0 history_of edges.
- "Ruled out myocardial infarction" -> 0 diagnosed_with edges.
- "Diagnosed with COPD; denies chest pain" -> 1 diagnosed_with edge, 0 has_symptom edges.
- "Confirmed allergy to penicillin" -> 1 allergic_to edge (`patient:self` -> `penicillin`).

- [ ] **Step 2: Run test to verify it fails**
Run: `cd app/backend && python -m pytest tests/test_graph_negation_extraction.py -v`
Expected: FAIL

- [ ] **Step 3: Implement negation guards & regex/prompt updates**
Add negation prefix analysis to fallback grammar and updated prompt for NLP extractor.

- [ ] **Step 4: Run test to verify it passes**
Run: `cd app/backend && python -m pytest tests/test_graph_negation_extraction.py -v`
Expected: PASS

---

### Task 4: Traversal Guard & DrugCheckService Upgrade

**Files:**
- Modify: `app/backend/src/hospital_ai/services/graph_rag.py:400-550`
- Modify: `app/backend/src/hospital_ai/services/drug_check.py:30-150`
- Test: `app/backend/tests/test_graph_traversal_guard.py`
- Test: `app/backend/tests/test_drug_check.py`

**Interfaces:**
- Consumes: Graph queries
- Produces: Safe BFS results without hub explosion, plus structured drug warnings with catalog-calibrated severity.

- [ ] **Step 1: Write the failing test**
Create `app/backend/tests/test_graph_traversal_guard.py` asserting that BFS traversing through `patient:self` does not fan out to all unrelated conditions.

- [ ] **Step 2: Run test to verify it fails**
Run: `cd app/backend && python -m pytest tests/test_graph_traversal_guard.py -v`
Expected: FAIL

- [ ] **Step 3: Implement Traversal Guard and upgrade DrugCheckService**
Skip expanding `patient:self` neighbors in BFS query loops (`find_related_entities`).

- [ ] **Step 4: Run test to verify it passes**
Run: `cd app/backend && python -m pytest tests/test_graph_traversal_guard.py tests/test_drug_check.py -v`
Expected: PASS

---

### Task 5: Frontend Graph Visualization & Filter Controls

**Files:**
- Create: `app/frontend/src/components/hms/GraphLegend.tsx`
- Modify: `app/frontend/src/components/hms/GraphFilters.tsx`
- Modify: `app/frontend/src/components/hms/GraphCanvas.tsx`
- Test: `app/frontend/src/components/hms/__tests__/GraphFilters.test.tsx`

**Interfaces:**
- Consumes: Graph API response with 10 relation types
- Produces: Color badges, toggleable filters, clean canvas styling.

- [ ] **Step 1: Write the failing test**
Add tests asserting that all 10 relation types can be toggled in `GraphFilters`.

- [ ] **Step 2: Run test to verify it fails**
Run: `cd app/frontend && bun run test`
Expected: FAIL

- [ ] **Step 3: Update React components and styles**
Add badge colors for `interacts_with`, `indicates`, `diagnosed_with`, `history_of`, `allergic_to` and create `GraphLegend.tsx`.

- [ ] **Step 4: Run test to verify it passes**
Run: `cd app/frontend && bun run test`
Expected: PASS

---

### Task 6: Backfill Engine & Full Suite Verification

**Files:**
- Modify: `app/backend/scripts/backfill_cdi_v2.py`
- Modify: `app/backend/scripts/seed_dev.py`
- Test: `app/backend/tests/test_legacy_parity.py`
- Test: Playwright E2E automation

- [ ] **Step 1: Implement backfill CLI option `--enrich-all`**
- [ ] **Step 2: Run full backend pytest suite (260+ tests)**
- [ ] **Step 3: Run full frontend typecheck and unit tests**
- [ ] **Step 4: Verify E2E smoke tests**
