# Clinical Graph RAG: Expanded 10-Relation Ontology & Hybrid Extraction System

- **Status**: Draft (In Review)
- **Author**: AI Architecture Council & Engineering Team
- **Date**: 2026-08-17
- **Target Release**: Sprint 1 / Graph RAG V2.1

---

## 1. Problem Statement & Objectives

### Current State
The existing Graph RAG implementation in the Hospital AI Knowledge Assistant extracts a closed vocabulary of **5 relations** (`treats`, `causes`, `contraindicates`, `prescribed_for`, `has_symptom`) alongside labeled lab observations (`has_observation`, `has_status`).

While safe, this schema lacks critical clinical semantic capabilities:
1. **Drug-Drug & Drug-Allergy Interactions**: Clinical staff cannot trace known interactions or patient allergy contraindications directly within the clinical knowledge graph.
2. **Diagnostic Indications**: Cannot explicitly link abnormal lab findings or vitals to suspected clinical conditions (`indicates`).
3. **Patient History & Diagnosis Attribution**: Cannot anchor confirmed diagnoses (`diagnosed_with`) or past medical history (`history_of`) directly to the patient's longitudinal record.

### Objectives
Expand the relational vocabulary from 5 to **10 standard relations**:
- **Drug & Pharmacology**: `treats`, `causes`, `contraindicates`, `prescribed_for`, `has_symptom`, `indicates`, `interacts_with`
- **Patient Anchor**: `diagnosed_with`, `history_of`, `allergic_to`
- **Lab Grammar**: `has_observation`, `has_status`

Maintain 100% adherence to:
- **Zero PHI Leakage**: Strict patient-scoped authorization and evidence bounds.
- **Zero Hallucination on Negation**: Avoid false-positive allergies/diagnoses from sentences like *"No known drug allergies (NKDA)"* or *"Denies chest pain"*.
- **No BFS Traversal Explosions**: Protect graph traversal from "super-node / hub-node" explosion when passing through patient entities.
- **High Determinism & Calibrated Severity**: Integrate `drug_interaction_matrix.csv` (500 rows) as a primary deterministic source for drug interactions.

---

## 2. Architectural Design

```
+----------------------------------------------------------------------------------------------------+
|                                    INGESTION & EXTRACTION PIPELINE                                 |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|    Document Chunk Content                                                                          |
|              │                                                                                     |
|              ├───► [1] Deterministic Drug Catalog Matcher                                         |
|              │          │ (Scans drug names -> Joins with drug_interaction_matrix.csv)             |
|              │          ▼                                                                          |
|              │     Produces: ExtractedRelation("warfarin", "aspirin", "interacts_with",            |
|              │                                severity="high", source_layer="catalog")             |
|              │                                                                                     |
|              ├───► [2] Negation-Aware Clinical NLP / Grammar Fallback                              |
|              │          │ (Extracts: treats, causes, contraindicates, indicates, diagnosed_with)   |
|              │          ▼ (Filters out negated statements: "denies", "no history", "NKDA")         |
|              │     Produces: ExtractedRelation("patient:self", "type_2_diabetes", "diagnosed_with",|
|              │                                source_layer="nlp")                                  |
|              │                                                                                     |
|              └───► [3] Labeled Lab Observation Grammar                                             |
|                         ▼                                                                          |
|                    Produces: ExtractedRelation("patient:<mrn>", "analyte:<name>", "has_observation")|
|                                                                                                    |
+----------------------------------------------------------------------------------------------------+
                                               │
                                               ▼
+----------------------------------------------------------------------------------------------------+
|                                      POSTGRES GRAPH STORAGE                                        |
+----------------------------------------------------------------------------------------------------+
|   • graph_entities (patient_id, entity_type, normalized_label, lifecycle_status)                    |
|   • graph_relation_assertions (patient_id, subject_id, object_id, relation_type, normalized_value)  |
|   • graph_relation_evidence (patient_id, assertion_id, chunk_id, generation_id, document_id...)    |
+----------------------------------------------------------------------------------------------------+
                                               │
                                               ▼
+----------------------------------------------------------------------------------------------------+
|                                GRAPH TRAVERSAL & QUERY ENGINE                                      |
+----------------------------------------------------------------------------------------------------+
|   • Traversal Guard: BFS expands concept nodes (hops <= 2).                                        |
|     'patient:self' is marked NON-EXPANDABLE to prevent combinatorial hub explosions.                |
|   • DrugCheckService: Scans query drugs, fetches 'interacts_with' & 'allergic_to' edges directly.   |
|   • GraphFilters UI: Supports toggling/filtering all 10 relation types with dedicated color badges. |
+----------------------------------------------------------------------------------------------------+
```

---

## 3. Data Models & Schema Updates

### 3.1 `ExtractedRelation` Dataclass
```python
@dataclass(frozen=True)
class ExtractedRelation:
    subject_label: str
    object_label: str
    relation_type: str
    normalized_value: str = ""
    weight: float = 1.0
    severity: Optional[str] = None  # critical | high | medium | low
    source_layer: str = "nlp"  # catalog | nlp | grammar
```

### 3.2 Canonical Patient Anchor
For all patient-attributed assertions (`diagnosed_with`, `history_of`, `allergic_to`):
- `subject_label` is strictly normalized to `"patient:self"`.
- `entity_type` is `"patient_anchor"`.
- This avoids entity fragmentation across synonyms (`"the patient"`, `"patient"`, `"55yo male"`).

### 3.3 Validated Relation Allowlist
```python
VALID_RELATION_TYPES = frozenset([
    "treats",
    "causes",
    "contraindicates",
    "prescribed_for",
    "has_symptom",
    "indicates",
    "interacts_with",
    "diagnosed_with",
    "history_of",
    "allergic_to",
    "has_observation",
    "has_status",
])
```

---

## 4. Extraction & Ingestion Engine

### 4.1 Deterministic Catalog Ingestion
During `index_chunk_entities`:
1. Parse known drug mentions in chunk text.
2. If two or more drugs appear in `drug_interaction_matrix.csv`, insert `interacts_with` relations with `severity`, `mechanism_action`, and `clinical_recommendation`.
3. Provenance is linked to the document chunk where both medications were co-identified or prescribed.

### 4.2 Negation-Aware LLM Extraction
The extraction prompt is updated with explicit clinical negation guards:
```text
CRITICAL NEGATION RULES:
1. Do NOT extract relations if the sentence indicates negation, denial, absence, or ruling-out:
   - "NKDA", "No known drug allergies", "No history of diabetes" -> DO NOT extract allergic_to / history_of
   - "Patient denies chest pain" -> DO NOT extract has_symptom
   - "Ruled out myocardial infarction" -> DO NOT extract diagnosed_with
2. For confirmed patient conditions:
   - Current active diagnosis -> ("patient:self", "<condition>", "diagnosed_with")
   - Past medical history -> ("patient:self", "<condition>", "history_of")
   - Confirmed drug allergy -> ("patient:self", "<drug>", "allergic_to")
```

### 4.3 Fallback Regex Grammar
Updated regex patterns in `_extract_explicit_relations_fallback` to detect:
- `(?P<source>...)\s+(indicates|interacts_with|allergic_to|diagnosed_with|history_of)\s+(?P<target>...)`
- Negation prefix check (`no`, `denies`, `without`, `ruled out`) to skip negated matches.

---

## 5. Graph Traversal & Query Protections

### 5.1 Traversal Guard (Anti-Hub Explosion)
In `services/graph_rag.py` and `services/graph_query.py`:
- In `retrieve_graph_context`: When BFS expands neighbors from an entity node, if the neighbor is `patient:self`, the traversal **does not expand outward from `patient:self`** into all other diseases of the patient.
- `patient:self` edges are only fetched when specifically querying the patient profile or checking allergies in `DrugCheckService`.

### 5.2 Enhanced `DrugCheckService`
- Queries `GraphRelationAssertion` for `relation_type.in_(["interacts_with", "contraindicates", "allergic_to"])`.
- Reads `severity` directly from assertion or fallback map.
- Formats structured clinical warnings with actionable recommendations.

---

## 6. Frontend UI Adaptations

### 6.1 `GraphFilters.tsx` & `GraphLegend.tsx`
- Add relation filter toggles:
  - `Interacts With` (Orange badge)
  - `Indicates` (Purple badge)
  - `Diagnosed With` (Blue badge)
  - `History Of` (Slate badge)
  - `Allergic To` (Red badge)
- Add entity category `Patient Anchor` with distinct patient avatar node icon.

---

## 7. Migration & Backfill Strategy

1. **Backfill Script**: `app/backend/scripts/backfill_cdi_v2.py --enrich-all`
   - Re-scans chunks in database.
   - Applies deterministic drug catalog joins and regex/NLP extractors.
   - Populates new relations in seconds for all synthetic patient documents without breaking generation IDs.
2. **Testing & Parity Protection**:
   - `tests/test_graph_rag.py` and `tests/test_drug_check.py` updated with 10-relation test cases.
   - `test_legacy_parity.py` isolated using source tags.

---

## 8. Verification & Acceptance Criteria
- [ ] 100% unit & integration test pass rate across backend test suite.
- [ ] Zero false-positive allergy edges on "No known drug allergies (NKDA)" test cases.
- [ ] BFS graph traversal latency remains under 50ms with BFS Traversal Guard enabled.
- [ ] Frontend graph canvas cleanly renders and filters all 10 relation types.
- [ ] End-to-end Playwright tests verify UI interactions and graph rendering.
