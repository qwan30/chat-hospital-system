# Clinical Document Intelligence & Evidence-Grounded Ingestion

**Spec ID:** CDI-001  
**Project:** `qwan30/chat-hospital-system`  
**Document type:** Product and technical design specification  
**Date:** 2026-07-31  
**Status:** Draft for owner review  
**Delivery model:** Full integrated scope; this specification does not split the feature into implementation phases

---

## 1. Executive summary

The current document pipeline converts hospital PDFs into text and searchable chunks. This specification upgrades that capability into a complete **Clinical Document Intelligence** subsystem.

The subsystem must not stop at plain OCR. It must:

1. classify each document and page;
2. select the cheapest suitable extraction engine;
3. preserve layout, reading order, tables, forms, and source coordinates;
4. produce raw, normalized, formatted, and structured representations;
5. extract clinical facts with field-level confidence and evidence;
6. route uncertain or high-risk fields into human review;
7. produce FHIR-ready drafts without automatically writing them into an external clinical record;
8. index verified, source-linked content for hybrid RAG, Graph RAG, and CDSS;
9. provide an evidence-grounded user interface where every extracted fact can be traced back to the exact page and region;
10. measure OCR, layout, table, clinical extraction, grounding, latency, reliability, and cost through versioned evaluation artifacts.

The final business outcome is:

> Transform unstructured hospital documents into structured, reviewable, source-grounded clinical knowledge that can safely support search, AI chat, knowledge graphs, and clinical decision-support workflows.

---

## 2. Background and current-system fit

The target repository already follows a hybrid Clean/Pipeline architecture:

- FastAPI backend;
- TanStack Start and React frontend;
- PostgreSQL with pgvector;
- Redis and RQ workers;
- permission-aware RAG;
- Graph RAG or clinical knowledge graph;
- autonomous CDSS processing;
- structured logging and observability;
- source-backed AI evaluation contracts.

This feature must extend those boundaries rather than introduce an unrelated architecture.

The existing high-level pipeline:

```text
Upload
→ parse PDF
→ OCR when needed
→ chunk
→ embed
→ pgvector
→ Graph extraction
→ CDSS
```

becomes:

```text
Upload PDF/Image
→ security and file validation
→ document and page classification
→ adaptive extraction routing
→ native text / OCR / layout-aware vision parsing
→ reading-order and structure reconstruction
→ table, form, checkbox, signature, and image-region extraction
→ clinical fact extraction
→ terminology and unit normalization
→ confidence and consistency validation
→ human review for uncertain or high-risk facts
→ FHIR-ready draft generation
→ section-aware hybrid indexing
→ evidence-linked Graph RAG
→ evidence-gated CDSS
```

### 2.1 Architectural rule

The implementation must preserve the repository’s pipeline-oriented design:

- framework-free contracts in `core`;
- orchestration and business workflows in `services`;
- persistence in `db`;
- RQ entry points in `workers`;
- HTTP and SSE contracts in `api`;
- Pydantic schemas in `schemas`;
- feature components under the existing frontend component structure.

No repository-wide refactor is part of this specification.

---

## 3. Goals

### 3.1 Product goals

The feature must allow authorized clinical users to:

- upload a PDF or image document;
- see processing progress without waiting on a blocking request;
- compare the source document with formatted extracted content;
- view structured diagnoses, medications, allergies, labs, vitals, procedures, dates, and identifiers;
- click any extracted field and jump to the exact source region;
- identify low-confidence or conflicting data;
- confirm, correct, or reject extracted clinical facts;
- export reviewed structured output as JSON, Markdown, and FHIR-ready draft bundles;
- search and chat over the document with page-level and region-level citations;
- understand which CDSS alert was derived from which source evidence.

### 3.2 Engineering goals

The subsystem must demonstrate:

- adaptive multi-engine document parsing;
- asynchronous orchestration with RQ;
- idempotent and revisioned processing;
- layout-aware reconstruction;
- structured clinical information extraction;
- provenance-first data modeling;
- confidence-driven review;
- permission-aware downstream indexing;
- real provider evaluation rather than mocked “passing” claims;
- observability across queue, page, engine, field, and document levels.

### 3.3 Safety goals

The subsystem must:

- never silently invent missing clinical content;
- never overwrite raw extraction evidence;
- never automatically commit OCR-derived FHIR data to an external EHR;
- never trigger high-impact CDSS actions from unsupported or unresolved low-confidence facts;
- never send PHI to an external model provider unless the deployment explicitly enables an approved provider;
- never expose a document, page, fact, overlay, export, or processing event outside existing RBAC and patient-scope rules.

---

## 4. Non-goals

The following are explicitly outside this feature:

- becoming a certified medical device;
- replacing clinician review;
- automatically diagnosing a patient;
- automatically updating an external hospital record without human approval;
- training a custom foundation OCR or multimodal model from scratch;
- guaranteeing accurate handwriting recognition for every writing style;
- supporting arbitrary office formats such as DOCX, PPTX, or XLSX through this OCR route;
- replacing the existing structured CSV ingestion flow;
- performing general-purpose image diagnosis, radiology interpretation, or pathology image classification;
- using document text as executable instructions for an LLM agent.

---

## 5. Supported inputs

### 5.1 Accepted formats

| Format | MIME type | Processing route |
|---|---|---|
| PDF | `application/pdf` | Native PDF extraction plus selective OCR or layout parsing |
| PNG | `image/png` | OCR or layout-aware vision parsing |
| JPEG | `image/jpeg` | OCR or layout-aware vision parsing |
| TIFF | `image/tiff` | Convert pages to supported image representation, then OCR |

### 5.2 Explicit exclusions

- CSV remains in the existing structured-data loader.
- Password-protected or encrypted PDFs are rejected with a clear error.
- Executable files, archives, embedded scripts, malformed polyglot files, and unsupported MIME types are rejected.
- A file extension is never trusted as proof of content type.

### 5.3 Default limits

| Limit | Default |
|---|---:|
| Maximum file size | 50 MB |
| Maximum PDF pages | 300 |
| Maximum image dimensions | 12,000 × 12,000 px |
| Maximum active processing runs per document | 1 |
| Maximum vision-worker concurrency on CPU profile | 1 |
| Maximum retry count per failed stage | 3 |

Limits must be configurable.

---

## 6. Users, roles, and permissions

The feature reuses the project’s existing RBAC and patient-scoped ABAC model.

### 6.1 Capabilities

| Capability | Doctor | Nurse | Pharmacist | Data/records staff | Admin |
|---|---:|---:|---:|---:|---:|
| View assigned patient documents | Yes | Yes | Yes | According to grant | Yes |
| Upload document for authorized patient | Yes | Yes | According to policy | Yes | Yes |
| View raw OCR and formatted output | Yes | Yes | Yes | Yes | Yes |
| Confirm general fields | Yes | Yes | Limited | Limited | Yes |
| Confirm medication fields | Yes | Limited | Yes | No | Yes |
| Confirm allergy fields | Yes | Limited | Yes | No | Yes |
| Confirm lab values | Yes | Yes | Limited | No | Yes |
| Retry processing | Yes | Limited | Limited | Yes | Yes |
| Force reprocess with another engine | Limited | No | No | Limited | Yes |
| Export FHIR-ready draft | Yes | Limited | Limited | No | Yes |
| Delete or quarantine source file | According to retention policy | No | No | Limited | Yes |

The exact role names must map to the current repository’s role enum and permission service.

### 6.2 Permission rules

Every document-intelligence query must enforce:

1. authentication;
2. role permission;
3. patient-scope permission;
4. document status and retention policy;
5. soft-delete and expiry rules.

Permission filtering must occur before content is returned to the client or passed downstream to an AI provider.

---

## 7. User stories

### 7.1 Upload and processing

As an authorized clinician, I can upload a hospital document and immediately receive a document ID and processing run ID so the UI does not block while OCR and indexing execute.

### 7.2 Evidence-grounded extraction

As a clinician, I can click a medication, dose, allergy, lab result, or diagnosis and see the exact page and bounding box from which the value was extracted.

### 7.3 Human review

As a reviewer, I can confirm, correct, or reject uncertain fields while preserving the original machine output and a full audit history.

### 7.4 Search and chat

As a permitted user, I can search or ask questions using reconstructed document sections, and every answer must retain page and block provenance.

### 7.5 CDSS

As a clinician, I can see that a clinical alert was generated from reviewed or sufficiently verified facts, with direct links to its source evidence.

### 7.6 Reprocessing

As an administrator or authorized records user, I can create a new extraction revision with changed engine settings without destroying the previous revision.

---

## 8. End-to-end flow

```text
User uploads file
    ↓
API validates auth, patient permission, MIME, size, and file signature
    ↓
Source file is stored and a Document record is created
    ↓
DocumentProcessingRun is created with a stable configuration snapshot
    ↓
RQ jobs are enqueued; API returns HTTP 202
    ↓
Preflight scanner checks corruption, encryption, page count, and document safety
    ↓
Document classifier determines likely type
    ↓
Each page receives a page profile
    ↓
Adaptive router chooses native extraction, OCR, or layout-aware vision parser
    ↓
Raw text, words, blocks, bounding boxes, confidence, and engine metadata are stored
    ↓
Normalizer preserves raw output and creates normalized text
    ↓
Layout reconstruction creates reading order, headings, paragraphs, lists, tables, forms, and code blocks
    ↓
Clinical extractor produces typed facts with source links
    ↓
Terminology and unit normalizer creates canonical candidates
    ↓
Validation engine detects conflicts and assigns review requirements
    ↓
Reviewer confirms/corrects/rejects required items
    ↓
FHIR-ready draft resources are generated
    ↓
Approved and eligible content is chunked by section and structure
    ↓
Embeddings and PostgreSQL full-text vectors are created
    ↓
Clinical graph entities and relations are linked to source facts and blocks
    ↓
CDSS evaluates eligible facts with evidence gates
    ↓
Document becomes ready, ready_with_warnings, or review_required
```

---

## 9. Processing architecture

### 9.1 RQ job graph

The system uses explicit stage jobs with persisted run state.

```text
preflight_document
    ↓
classify_document
    ↓
extract_native_pages
    ↓
extract_vision_pages
    ↓
reconstruct_document
    ↓
extract_clinical_facts
    ↓
validate_and_route_review
    ↓
build_fhir_draft
    ↓
index_document
    ↓
extract_graph
    ↓
run_cdss
    ↓
finalize_document
```

RQ dependencies may be used, but the database is the source of truth for stage state. Redis job state alone is insufficient.

### 9.2 Queues

| Queue | Purpose | Default concurrency |
|---|---|---:|
| `document-fast` | Preflight, classification, native extraction, normalization | 2 |
| `document-vision` | PaddleOCR and layout-aware vision parsing | 1 on CPU profile |
| `document-clinical` | Clinical extraction, validation, FHIR draft | 1 |
| `document-index` | Chunking, embeddings, tsvector, graph linkage | 1 |
| `cdss` | Existing evidence-gated CDSS workflow | Existing configuration |

A deployment may run multiple queue names in one worker process, but vision jobs must remain concurrency-limited.

### 9.3 Stage contract

Every stage must:

- accept `document_id`, `processing_run_id`, and `configuration_version`;
- be idempotent;
- persist start and completion events;
- emit structured logs without document text;
- return a compact stage result;
- support retry without duplicate pages, blocks, facts, or chunks;
- stop if the run has been cancelled;
- preserve completed prior stages;
- classify errors as retryable or terminal.

### 9.4 Revision model

Reprocessing creates a new immutable extraction revision.

Rules:

- the original source file remains stable;
- prior extraction revisions remain auditable;
- only one processing run may be active for a document;
- downstream indexes point to an active extraction revision;
- a new revision becomes active only after mandatory stages succeed;
- activation is atomic;
- failure of a new revision does not destroy the previously active revision.

---

## 10. Processing states

### 10.1 Document states

```text
uploaded
queued
processing
review_required
ready_with_warnings
ready
failed
cancelled
quarantined
soft_deleted
```

### 10.2 Stage states

```text
pending
queued
running
completed
completed_with_warnings
skipped
failed_retryable
failed_terminal
cancelled
```

### 10.3 State rules

- `ready` means all mandatory processing completed and no blocking review item remains.
- `ready_with_warnings` means the document is searchable, but non-blocking low-confidence regions remain.
- `review_required` means one or more high-risk fields cannot enter CDSS or approved structured export until reviewed.
- `failed` means no usable active revision was produced.
- `quarantined` means file validation or security checks require administrator action.
- A stale watchdog must never leave a document in `processing` indefinitely.

---

## 11. Document and page classification

### 11.1 Document types

The classifier should produce one primary type and optional candidates:

```text
clinical_note
discharge_summary
prescription
laboratory_report
imaging_report_text
referral
consent_form
medical_certificate
invoice_or_billing
administrative_form
research_or_guideline
unknown
```

### 11.2 Page profiles

Each page receives one or more labels:

```text
native_text
scanned_printed
handwritten_or_mixed
single_column
multi_column
form
table_dominant
prescription
low_resolution
rotated
skewed
image_dominant
code_or_technical
unknown
```

### 11.3 Classification output

```json
{
  "document_type": "laboratory_report",
  "confidence": 0.94,
  "page_profiles": [
    {
      "page_number": 1,
      "labels": ["scanned_printed", "table_dominant"],
      "native_text_quality": 0.08,
      "rotation_degrees": 0,
      "recommended_engine": "layout_vision"
    }
  ]
}
```

Classification metadata must be versioned with the run.

---

## 12. Adaptive extraction router

### 12.1 Router decision order

For every page:

1. attempt low-cost native PDF inspection;
2. calculate text and layout quality signals;
3. choose the lowest-cost engine capable of preserving required information;
4. escalate only when output quality is insufficient;
5. record the decision and reason.

### 12.2 Native extraction route

Use PyMuPDF when:

- the page contains a usable text layer;
- character and word distributions are plausible;
- reading order is recoverable;
- the page is not dominated by complex tables or forms requiring visual parsing.

Native extraction must preserve:

- spans;
- font size and style when available;
- block coordinates;
- page dimensions;
- reading-order candidates;
- images and drawing regions;
- raw extracted text.

### 12.3 Standard OCR route

Use PaddleOCR for:

- printed scanned pages;
- images with simple or moderate layout;
- pages where native text is missing or corrupted;
- selected page regions rather than the entire document when possible.

### 12.4 Layout-aware vision route

Use a configurable layout-aware parser for:

- complex tables;
- multi-column documents;
- forms and checkboxes;
- mixed text and image regions;
- pages where standard OCR produces an invalid reading order;
- scanned prescriptions or documents with dense spatial relationships.

The default implementation may use PaddleOCR-VL or another adapter behind the same interface. Provider choice must not leak into orchestration code.

### 12.5 Handwriting route

Handwriting recognition is best-effort.

Rules:

- handwritten pages use the configured vision adapter;
- all clinically relevant handwritten fields are marked `review_required` unless explicitly confirmed;
- confidence alone cannot auto-approve a handwritten medication dose, allergy, patient identifier, or lab value;
- illegible regions remain unresolved rather than guessed.

### 12.6 Engine fallback

```text
native extraction succeeds
→ use native result

native extraction weak
→ standard OCR

standard OCR weak or layout invalid
→ layout-aware vision parser

layout parser unavailable
→ preserve best available output
→ mark degraded processing
→ create review items
```

The pipeline must not mark a degraded fallback as a fully verified success.

---

## 13. Extraction quality scoring

### 13.1 Native text signals

The page-quality evaluator considers:

- character count;
- alphanumeric ratio;
- printable-character ratio;
- replacement-character count;
- word-boundary plausibility;
- repeated glyph patterns;
- average word length;
- extraction overlap;
- page coverage by text blocks;
- suspiciously empty or duplicated content;
- reading-order coherence.

### 13.2 Default routing thresholds

| Signal | Default |
|---|---:|
| Minimum useful characters | 80 |
| Minimum alphanumeric ratio | 0.35 |
| Maximum replacement-character ratio | 0.02 |
| Minimum text-block page coverage | 0.03 |
| Native extraction acceptance score | 0.80 |
| OCR escalation score | Below 0.80 |
| Layout-parser escalation score | OCR quality below 0.78 or layout conflict |

Thresholds are configuration values and must be recorded in the run snapshot.

---

## 14. Canonical extraction representations

The system stores four distinct representations.

### 14.1 Raw representation

Unmodified provider output:

- raw text;
- words or tokens;
- provider confidence;
- source coordinates;
- provider-specific metadata;
- engine and model version.

Raw output is immutable.

### 14.2 Normalized representation

Safe mechanical cleanup:

- Unicode NFC normalization;
- control-character removal;
- whitespace normalization;
- conservative line-join repair;
- page-boundary preservation;
- no unsupported medical correction.

### 14.3 Structured block representation

Layout-aware blocks:

```text
title
heading
paragraph
list
list_item
table
form_field
checkbox
signature
stamp
caption
header
footer
page_number
code
formula
image_region
unknown
```

### 14.4 Formatted representation

Markdown or equivalent display representation generated from structured blocks.

The formatted representation must preserve source links and must never replace raw evidence.

---

## 15. Post-OCR reconstruction

### 15.1 Reading order

The reconstruction engine must:

- identify columns;
- prevent cross-column line merging;
- order blocks by layout graph rather than only Y coordinate;
- preserve page boundaries;
- represent ambiguous ordering explicitly.

### 15.2 Paragraph reconstruction

Lines may be joined when:

- they are in the same column;
- font and spacing are compatible;
- the preceding line is not a heading, list item, table row, or code line;
- geometric distance supports a shared paragraph;
- hyphen repair is supported by both text and geometry.

### 15.3 Heading hierarchy

Heading levels are inferred using:

- font size;
- weight;
- numbering patterns;
- whitespace;
- alignment;
- repeated document structure.

The system must not label a line as a heading merely because it is short.

### 15.4 Lists

The system preserves:

- bullets;
- numbered lists;
- alphabetical lists;
- nested indentation;
- check marks;
- clinical plan items.

### 15.5 Headers and footers

Repeated page content is stored and marked as header or footer.

It may be excluded from search chunks, but:

- raw output retains it;
- the UI can display it;
- it remains available for audit.

### 15.6 Code and formula regions

For technical or guideline documents:

- code indentation and line breaks are preserved;
- formulas are stored as a dedicated block when detected;
- the system does not silently rewrite syntax.

---

## 16. Table, form, and spatial data reconstruction

### 16.1 Table output

Each table stores:

- page number;
- table bounding box;
- row count;
- column count;
- headers;
- cells;
- row and column spans;
- cell bounding boxes;
- raw and normalized cell text;
- cell confidence;
- reconstruction confidence.

Example:

```json
{
  "table_id": "tbl_01",
  "page_number": 4,
  "bbox": [0.12, 0.31, 0.91, 0.72],
  "headers": ["Test", "Result", "Unit", "Reference range"],
  "rows": [
    ["Potassium", "3.1", "mmol/L", "3.5–5.1"]
  ],
  "confidence": 0.93
}
```

Coordinates are normalized to the page coordinate system.

### 16.2 Table failure behavior

When row or column structure cannot be verified:

- preserve cell-like blocks and coordinates;
- mark the table `ambiguous`;
- do not invent missing cells;
- create review items for clinically significant values;
- do not flatten the table into a misleading paragraph.

### 16.3 Forms and checkboxes

Forms must preserve:

- label;
- value;
- checked or unchecked state;
- bounding box;
- confidence;
- source page.

Uncertain checkbox state is review-required.

### 16.4 Signatures and stamps

The system detects presence and location only.

It must not claim legal authenticity or identify the signer solely from visual appearance.

---

## 17. Clinical fact extraction

### 17.1 Extraction approach

Clinical extraction uses a layered strategy:

1. deterministic parsers for dates, numeric values, units, identifiers, and common field patterns;
2. table-aware extraction;
3. schema-constrained LLM or vision extraction where enabled;
4. terminology candidate mapping;
5. cross-field validation;
6. confidence and review policy.

The extractor must produce structured JSON matching strict schemas. Free-form model output is not accepted as a clinical fact.

### 17.2 Supported fact types

```text
patient_identifier
patient_name
date_of_birth
sex_or_gender_as_recorded
encounter_date
admission_date
discharge_date
provider
facility
diagnosis
symptom
allergy
adverse_reaction
medication
medication_dose
medication_route
medication_frequency
medication_duration
laboratory_test
laboratory_value
laboratory_unit
reference_range
vital_sign
procedure
medical_history
family_history
treatment_plan
follow_up
clinical_warning
document_signature_presence
```

### 17.3 Clinical fact schema

```json
{
  "id": "fact_uuid",
  "type": "laboratory_result",
  "raw_label": "Kali",
  "raw_value": "3,1",
  "normalized_label": "Potassium",
  "normalized_value": 3.1,
  "unit": "mmol/L",
  "reference_range": {
    "low": 3.5,
    "high": 5.1
  },
  "code_system": "LOINC",
  "code": null,
  "confidence": 0.95,
  "risk_class": "high",
  "validation_status": "requires_review",
  "review_status": "pending",
  "sources": [
    {
      "page_number": 4,
      "block_id": "blk_44",
      "table_id": "tbl_01",
      "cell_path": "rows[0][1]",
      "bbox": [0.41, 0.45, 0.52, 0.49]
    }
  ],
  "extractor_version": "clinical-extractor-v1"
}
```

### 17.4 Medication structure

Medication extraction must separate:

- medication name;
- active ingredient candidate;
- strength;
- dose;
- dose unit;
- route;
- frequency;
- duration;
- start and end date;
- status;
- context such as prescribed, current, discontinued, or historical.

The system must not infer `MedicationRequest` when the source only shows historical use.

### 17.5 Laboratory structure

Lab extraction must preserve:

- test name;
- value;
- comparator;
- unit;
- reference range;
- abnormal flag from the source;
- specimen and timestamp when present;
- table row provenance.

### 17.6 Diagnosis and condition structure

Diagnosis output must preserve:

- exact source phrase;
- normalized candidate;
- suspected, confirmed, historical, or ruled-out context;
- code candidate if available;
- source date;
- evidence.

Negated or ruled-out diagnoses must never be converted into confirmed conditions.

---

## 18. Terminology and unit normalization

### 18.1 Supported code-system candidates

The normalization layer may map to:

- ICD-10 for diagnosis candidates;
- SNOMED CT when an approved terminology source is configured;
- LOINC for laboratory and observation candidates;
- RxNorm or ATC for medication candidates;
- UCUM for units.

A candidate code is not treated as verified unless:

- the mapping meets the configured confidence threshold; or
- a reviewer confirms it.

### 18.2 Unit normalization

The system must:

- preserve the original unit;
- create a canonical UCUM candidate;
- avoid unit conversion when context is insufficient;
- detect impossible or conflicting unit/value combinations;
- never silently replace the source value.

### 18.3 Terminology provider interface

```python
class TerminologyProvider(Protocol):
    def map_diagnosis(self, text: str, context: dict) -> list[CodeCandidate]: ...
    def map_medication(self, text: str, context: dict) -> list[CodeCandidate]: ...
    def map_lab_test(self, text: str, context: dict) -> list[CodeCandidate]: ...
    def normalize_unit(self, value: str) -> UnitCandidate: ...
```

The subsystem must support local vocabulary tables and optional approved external services.

---

## 19. Confidence model

### 19.1 Confidence dimensions

A single OCR percentage is insufficient. The system stores:

- engine confidence;
- text confidence;
- block confidence;
- layout confidence;
- table-structure confidence;
- clinical extraction confidence;
- terminology-mapping confidence;
- consistency-validation result;
- overall fact confidence.

### 19.2 Fact confidence

The overall fact confidence is a calibrated score derived from:

- source text confidence;
- layout or cell confidence;
- extraction-model confidence;
- agreement between deterministic and model extractors;
- consistency checks;
- document-type compatibility;
- terminology mapping quality.

The formula and calibration version must be stored.

### 19.3 Default review policy

| Condition | Outcome |
|---|---|
| General field confidence ≥ 0.95 and no conflict | Auto-eligible |
| General field confidence 0.80–0.949 | Warning or review according to field type |
| General field confidence < 0.80 | Review required |
| Handwritten clinically relevant field | Review required |
| Medication name, dose, route, or frequency with any uncertainty | Review required |
| Allergy or adverse reaction with any conflict | Review required |
| Patient identifier mismatch | Blocking review |
| Lab value/unit ambiguity | Blocking review for CDSS |
| Unsupported or missing source | Reject from structured downstream use |
| Conflicting values from multiple pages | Review required |

Thresholds are configurable and versioned.

---

## 20. Validation and consistency rules

### 20.1 Patient identity

- compare extracted identifiers with the document’s assigned patient;
- never silently reassign a document;
- mismatch creates a blocking review item;
- exact patient identifiers must not be written to logs.

### 20.2 Dates

Detect:

- discharge before admission;
- medication date outside encounter context;
- impossible dates;
- ambiguous date formats;
- date-of-birth conflicts.

### 20.3 Medication

Detect:

- dose without unit;
- unit without numeric dose;
- frequency parsed as dose;
- duplicated medication rows;
- contradictory active and discontinued status;
- allergy-medication conflicts only after facts satisfy evidence policy.

### 20.4 Laboratory

Detect:

- numeric value with incompatible unit;
- reference range parse failure;
- decimal-comma ambiguity;
- OCR confusion such as `1` versus `I`, `0` versus `O`;
- table row misalignment;
- abnormal flag inconsistent with value and range.

### 20.5 Negation and uncertainty

The extractor must preserve terms such as:

- no;
- denies;
- ruled out;
- suspected;
- possible;
- history of;
- family history of.

Negation and temporality are part of the fact, not post-processing decoration.

---

## 21. Human-review workflow

### 21.1 Review item types

```text
low_confidence
patient_identity_mismatch
medication_ambiguity
allergy_ambiguity
lab_value_ambiguity
table_structure_ambiguity
handwriting
terminology_mapping
conflicting_sources
unsupported_fact
provider_failure
```

### 21.2 Review actions

A permitted reviewer can:

- confirm machine output;
- correct value;
- correct label or type;
- select terminology code;
- reject fact;
- mark unreadable;
- defer with comment.

### 21.3 Audit behavior

Each action stores:

- actor ID;
- role;
- timestamp;
- previous value;
- new value;
- reason;
- source revision;
- correlation or trace ID.

Machine output remains immutable. Human corrections create reviewed values and do not erase original output.

### 21.4 Concurrency

Review items use optimistic locking.

If two reviewers edit the same item:

- the second write receives a conflict response;
- the UI shows the latest reviewed version;
- no action is silently overwritten.

### 21.5 Completion rule

A document exits `review_required` when all blocking review items are:

- confirmed;
- corrected;
- rejected;
- or explicitly marked unreadable with downstream exclusion.

---

## 22. FHIR-ready draft generation

### 22.1 Resource candidates

| Extracted content | FHIR draft resource |
|---|---|
| Original document | `DocumentReference` |
| Lab report grouping | `DiagnosticReport` |
| Lab or vital value | `Observation` |
| Diagnosis | `Condition` |
| Allergy or adverse reaction | `AllergyIntolerance` |
| Current or historical medication | `MedicationStatement` |
| Prescription or order when source semantics prove it | `MedicationRequest` |
| Procedure | `Procedure` |
| Encounter metadata | `Encounter` |

### 22.2 Draft rules

- output is a draft bundle;
- each resource contains source provenance;
- unreviewed high-risk fields are excluded or marked as unverified;
- no bundle is posted to an external FHIR server automatically;
- generation is deterministic from the active reviewed revision;
- regenerating a draft creates a new draft version.

### 22.3 Provenance

Every draft resource must link to:

- `DocumentReference`;
- document ID;
- extraction revision;
- source page;
- source block or table cell;
- reviewer when human-confirmed.

---

## 23. RAG and indexing behavior

### 23.1 Indexable representations

The system indexes:

- formatted section text;
- structured table rows;
- approved clinical fact summaries;
- permitted metadata;
- source page and block links.

It does not use raw provider JSON as retrieval content.

### 23.2 Chunking strategy

Chunks are structure-aware rather than fixed-token-only.

Preferred boundaries:

- document section;
- heading hierarchy;
- paragraph group;
- complete table row or logical table section;
- medication group;
- lab panel;
- clinical plan item.

Token size remains bounded, but structure is primary.

### 23.3 Chunk metadata

```json
{
  "document_id": "uuid",
  "processing_run_id": "uuid",
  "extraction_revision": 3,
  "patient_id": "uuid",
  "document_type": "laboratory_report",
  "section_path": ["Laboratory Results", "Electrolytes"],
  "page_start": 4,
  "page_end": 4,
  "block_ids": ["blk_40", "blk_44"],
  "fact_ids": ["fact_12"],
  "review_status": "approved",
  "minimum_source_confidence": 0.93,
  "content_hash": "sha256",
  "permissions": {}
}
```

### 23.4 Hybrid retrieval

Each eligible chunk receives:

- embedding vector;
- PostgreSQL `tsvector`;
- document and patient permission metadata;
- source pointers;
- extraction and review status.

The current permission-aware SQL filter remains mandatory.

### 23.5 Reindexing

Activating a new extraction revision:

1. creates revision-specific chunks;
2. builds vector and keyword indexes;
3. validates counts and source links;
4. atomically marks the new revision active;
5. retires prior revision chunks from retrieval without deleting audit history.

---

## 24. Graph RAG integration

### 24.1 Graph entities

Graph nodes may represent:

- patient;
- encounter;
- diagnosis;
- medication;
- allergy;
- laboratory observation;
- procedure;
- provider;
- document;
- reviewed clinical fact.

### 24.2 Graph evidence

Every graph node and edge derived from a document must link to:

- fact ID;
- document ID;
- extraction revision;
- page;
- block or table cell;
- confidence;
- review status.

### 24.3 Graph safety

- unresolved low-confidence facts do not create active clinical relationships;
- rejected facts are excluded;
- graph extraction failure does not delete the searchable document revision;
- graph processing can be retried independently;
- duplicate entities are reconciled using current graph identity rules.

---

## 25. CDSS integration

### 25.1 Evidence eligibility

CDSS may use a fact when:

- it has a valid source;
- it passes field-specific confidence policy;
- no blocking validation conflict exists;
- required human review is complete;
- the requesting or background context has patient permission.

### 25.2 Supported trigger candidates

```text
drug–allergy conflict
drug–drug interaction
duplicate medication
abnormal lab result
contraindication
dose anomaly
follow-up risk
documented warning
```

### 25.3 Alert provenance

A clinical alert stores:

- source fact IDs;
- source document;
- page and block evidence;
- rule or model version;
- confidence;
- reviewed status;
- explanation;
- severity;
- acknowledgement state.

### 25.4 Failure isolation

CDSS failure:

- does not invalidate successful OCR or indexing;
- sets the CDSS stage to failed or warning;
- allows independent retry;
- is visible in processing diagnostics;
- never fabricates a successful alert state.

---

## 26. API specification

All paths are shown under `/api`. They may be adapted to the current router prefix without breaking existing clients.

### 26.1 Upload

`POST /documents`

Multipart fields:

- `file`;
- `patient_id`;
- `document_type_hint` optional;
- `processing_profile` optional: `auto`, `native_only`, `standard_ocr`, `layout_vision`;
- `metadata` optional JSON.

Response:

```http
HTTP/1.1 202 Accepted
```

```json
{
  "document_id": "uuid",
  "processing_run_id": "uuid",
  "job_ids": ["rq-id"],
  "status": "queued",
  "status_url": "/api/documents/{id}/intelligence",
  "events_url": "/api/documents/{id}/events"
}
```

### 26.2 Intelligence summary

`GET /documents/{document_id}/intelligence`

Returns:

- document metadata;
- active revision;
- current processing state;
- page and engine counts;
- extraction quality;
- fact counts;
- review counts;
- indexing and CDSS status;
- available exports.

### 26.3 Processing events

`GET /documents/{document_id}/processing-events`

Supports pagination and stage filters.

### 26.4 SSE events

`GET /documents/{document_id}/events`

Event types:

```text
processing.progress
processing.warning
processing.failed
page.completed
review.created
review.updated
index.completed
graph.completed
cdss.completed
document.ready
heartbeat
```

Example:

```text
event: processing.progress
data: {"stage":"vision_extraction","progress":42,"page":6,"total_pages":24}
```

### 26.5 Pages

`GET /documents/{document_id}/pages`

Query parameters:

- `page`;
- `page_size`;
- `representation=raw|normalized|formatted|blocks`;
- `minimum_confidence`;
- `review_status`.

### 26.6 Single-page detail

`GET /documents/{document_id}/pages/{page_number}`

Returns:

- page image or file URL;
- dimensions;
- extraction engine;
- quality metrics;
- raw text;
- normalized text;
- formatted Markdown;
- blocks;
- tables;
- low-confidence regions.

### 26.7 Original file

`GET /documents/{document_id}/file`

Requirements:

- authorization;
- correct MIME;
- byte-range support for PDF;
- no physical storage-path disclosure;
- audit event;
- safe content-disposition filename.

### 26.8 Clinical facts

`GET /documents/{document_id}/facts`

Filters:

- fact type;
- confidence;
- validation status;
- review status;
- page;
- risk class.

### 26.9 Review items

`GET /documents/{document_id}/review-items`

`PATCH /documents/{document_id}/review-items/{review_item_id}`

Request example:

```json
{
  "action": "correct",
  "value": {
    "normalized_value": 3.1,
    "unit": "mmol/L"
  },
  "reason": "Verified against source table",
  "version": 2
}
```

### 26.10 Complete review

`POST /documents/{document_id}/review/complete`

The server validates that no blocking item remains.

### 26.11 Retry

`POST /documents/{document_id}/retry`

Optional body:

```json
{
  "from_stage": "vision_extraction"
}
```

### 26.12 Reprocess

`POST /documents/{document_id}/reprocess`

Request:

```json
{
  "processing_profile": "layout_vision",
  "engine_overrides": {},
  "reason": "Table reconstruction quality was insufficient"
}
```

Creates a new processing run and revision.

### 26.13 Cancel

`POST /documents/{document_id}/processing-runs/{run_id}/cancel`

Cancellation is cooperative. Active provider calls may finish, but no later stage may start.

### 26.14 Export

`GET /documents/{document_id}/export?format=markdown|json|fhir`

FHIR export returns a draft bundle and review metadata.

---

## 27. Database design

Existing tables should be extended where practical. New tables are justified when they provide versioning, provenance, or review boundaries.

### 27.1 `documents`

Add or confirm:

```text
id
patient_id
original_filename
mime_type
file_size
content_hash
page_count
status
active_processing_run_id
active_extraction_revision
uploaded_by
uploaded_at
soft_deleted_at
retention_until
quarantine_reason
metadata JSONB
```

### 27.2 `document_processing_runs`

```text
id
document_id
revision_number
status
processing_profile
configuration_snapshot JSONB
engine_versions JSONB
current_stage
progress_percent
started_at
completed_at
cancelled_at
failure_code
failure_message_safe
created_by
created_at
```

Unique constraint:

```text
one active run per document
```

### 27.3 `document_processing_events`

```text
id
document_id
processing_run_id
stage
event_type
status
progress_percent
page_number nullable
message_safe
metrics JSONB
error_code nullable
created_at
completed_at nullable
trace_id
```

### 27.4 `document_pages`

```text
id
document_id
processing_run_id
revision_number
page_number
width
height
rotation
page_profile JSONB
native_quality_score
extraction_engine
engine_version
raw_text
normalized_text
formatted_markdown
text_confidence
layout_confidence
processing_time_ms
low_confidence_region_count
created_at
```

Unique:

```text
(document_id, revision_number, page_number)
```

### 27.5 `document_blocks`

```text
id
document_id
processing_run_id
revision_number
page_id
block_type
reading_order
text_raw
text_normalized
bbox JSONB
confidence
style_metadata JSONB
parent_block_id nullable
provider_metadata JSONB
created_at
```

### 27.6 `document_tables`

```text
id
document_id
processing_run_id
revision_number
page_id
bbox JSONB
row_count
column_count
structure JSONB
markdown
confidence
status
created_at
```

The JSON structure stores cells, row spans, column spans, cell bounding boxes, raw text, normalized text, and confidence.

### 27.7 `clinical_facts`

```text
id
document_id
processing_run_id
revision_number
patient_id
fact_type
raw_label
raw_value JSONB
normalized_label
normalized_value JSONB
unit
code_system
code
temporality
negation_status
confidence
risk_class
validation_status
review_status
extractor_version
created_at
updated_at
```

### 27.8 `clinical_fact_sources`

```text
id
clinical_fact_id
page_id
block_id nullable
table_id nullable
cell_path nullable
bbox JSONB
source_text_hash
created_at
```

### 27.9 `document_review_items`

```text
id
document_id
processing_run_id
revision_number
clinical_fact_id nullable
page_id nullable
review_type
severity
status
machine_payload JSONB
reviewed_payload JSONB nullable
reason
assigned_to nullable
version
created_at
reviewed_at nullable
reviewed_by nullable
```

### 27.10 `document_review_actions`

```text
id
review_item_id
actor_id
actor_role
action
before_payload JSONB
after_payload JSONB
reason
created_at
trace_id
```

### 27.11 `fhir_drafts`

```text
id
document_id
processing_run_id
revision_number
bundle JSONB
status
generation_version
created_at
created_by
```

### 27.12 `document_chunks`

Extend existing chunks with:

```text
processing_run_id
revision_number
section_path JSONB
page_start
page_end
block_ids JSONB
fact_ids JSONB
review_status
minimum_source_confidence
content_hash
is_active
search_vector
```

### 27.13 Indexes

Required:

- B-tree on document and run foreign keys;
- unique page and revision indexes;
- GIN on JSON fields used for filtering;
- GIN on `search_vector`;
- HNSW or the repository’s active pgvector index;
- partial index on active chunks;
- partial index on pending review items;
- index on patient, document status, and active revision;
- unique content-hash protections where idempotency requires them.

---

## 28. Provider abstractions

### 28.1 Native document extractor

```python
class NativeDocumentExtractor(Protocol):
    def inspect(self, source: DocumentSource) -> DocumentInspection: ...
    def extract_page(self, source: DocumentSource, page_number: int) -> PageExtraction: ...
```

### 28.2 OCR provider

```python
class OcrProvider(Protocol):
    def extract_page(self, image: PageImage, options: OcrOptions) -> PageExtraction: ...
```

### 28.3 Layout parser

```python
class LayoutParser(Protocol):
    def parse_page(self, image: PageImage, options: LayoutOptions) -> StructuredPage: ...
```

### 28.4 Clinical extractor

```python
class ClinicalFactExtractor(Protocol):
    def extract(self, document: StructuredDocument, schema: ClinicalSchema) -> list[ClinicalFactCandidate]: ...
```

### 28.5 Confidence calibrator

```python
class ConfidenceCalibrator(Protocol):
    def score_fact(self, candidate: ClinicalFactCandidate, evidence: EvidenceSet) -> CalibratedConfidence: ...
```

Provider implementations must be selected through configuration and dependency injection.

---

## 29. Frontend design

### 29.1 Route

The document intelligence page uses the current document route convention:

```text
/documents/{documentId}
```

### 29.2 Desktop layout

```text
┌─────────────────────────────────────────────────────────────────────┐
│ Document metadata             Processing activity and quality       │
├─────────────────────────────────────────────────────────────────────┤
│ Original document             Intelligence workspace                │
│                               ┌───────────────────────────────────┐ │
│ PDF/Image viewer              │ Formatted document                │ │
│ with bounding overlays        │ Clinical facts                   │ │
│                               │ Raw OCR                           │ │
│                               │ Review queue                      │ │
│                               │ Processing diagnostics            │ │
│                               └───────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────┤
│ Detected facts: diagnoses · medications · allergies · labs · plans  │
└─────────────────────────────────────────────────────────────────────┘
```

### 29.3 Metadata and quality card

Display:

- upload time;
- uploader;
- patient;
- document type;
- file type;
- page count;
- active revision;
- document status;
- extraction profile;
- engine distribution;
- average text and layout confidence;
- low-confidence page count;
- facts detected;
- blocking review count;
- indexing status;
- Graph status;
- CDSS status.

Never show `OCR confidence: 100%` for a page that used native extraction.

### 29.4 Processing timeline

Stages:

```text
Upload
Preflight
Classification
Native extraction
Vision extraction
Reconstruction
Clinical extraction
Validation
Review
FHIR draft
Indexing
Graph
CDSS
Ready
```

Stage visual states:

- pending;
- queued;
- running;
- completed;
- warning;
- skipped;
- failed.

### 29.5 Original document viewer

Must support:

- PDF.js or existing PDF viewer;
- page navigation;
- zoom;
- fit width and fit page;
- fullscreen;
- lazy rendering;
- page range loading;
- overlay bounding boxes;
- overlay filter by block, fact, confidence, or review state;
- click overlay to select the matching fact or block;
- scroll to page from a selected fact;
- byte-range PDF loading where available.

### 29.6 Intelligence workspace tabs

#### Formatted document

- rendered headings, paragraphs, lists, and tables;
- page separators;
- source-hover behavior;
- search and highlight;
- copy with page citations.

#### Clinical facts

Grouped by:

- patient and encounter;
- diagnoses;
- symptoms;
- medications;
- allergies;
- laboratory results;
- vitals;
- procedures;
- treatment plan;
- dates and providers.

Each fact card shows:

- normalized value;
- raw source value;
- confidence;
- review state;
- source page;
- validation warnings;
- terminology candidate;
- actions.

#### Raw OCR

- provider output by page;
- line numbers;
- engine and model version;
- no automatic formatting;
- copy and search.

#### Review queue

- filter by type, risk, confidence, page, and status;
- side-by-side source region and machine result;
- confirm, correct, reject, unreadable;
- keyboard navigation;
- optimistic-lock conflict handling.

#### Processing diagnostics

- page route decisions;
- stage durations;
- provider failures;
- retry history;
- quality metrics;
- no raw PHI in diagnostics logs.

### 29.7 Evidence interaction

Selecting a fact must:

1. navigate the source viewer to the page;
2. scroll to its bounding box;
3. highlight the exact region;
4. show the original text or table cell;
5. display extraction and review history.

Selecting a source overlay must select the corresponding fact or block on the right.

### 29.8 Mobile and tablet

Tablet:

- resizable split view;
- collapsible timeline.

Mobile:

- tabs for `Source`, `Formatted`, `Facts`, `Review`, and `Progress`;
- no side-by-side requirement;
- touch-friendly bounding overlays;
- PDF viewer must not overflow viewport.

---

## 30. Real-time updates

SSE is the preferred client update mechanism.

### 30.1 Behavior

- the UI subscribes after upload or document-page load;
- events update timeline, counters, and page readiness;
- heartbeat prevents silent connection expiry;
- reconnect uses `Last-Event-ID`;
- missed events are recovered from persisted processing events;
- polling every 2–3 seconds is the fallback.

### 30.2 Security

The SSE stream must:

- recheck authentication;
- enforce patient/document permission;
- avoid including raw PHI;
- close when the user loses access or the token becomes invalid.

---

## 31. File storage and page rendering

### 31.1 Source storage

The storage adapter must support local filesystem or object storage.

Stored metadata includes:

- content hash;
- size;
- MIME;
- creation time;
- retention state;
- encryption or storage policy metadata.

### 31.2 Temporary images

- page images are generated only when needed;
- temporary files use non-user-controlled names;
- temporary images are deleted after processing or retained only under a configured cache policy;
- paths are never returned directly to clients;
- image rendering uses configurable DPI, default 250.

### 31.3 Page previews

Preview images may be cached for the UI.

They are access-controlled and tied to the document’s permission rules.

---

## 32. Security, privacy, and prompt-injection controls

### 32.1 Upload security

- validate magic bytes;
- sanitize filename;
- reject path traversal;
- detect malformed PDF;
- reject embedded executable content where detectable;
- apply optional malware scan adapter;
- quarantine suspicious files;
- enforce limits before expensive processing.

### 32.2 PHI protection

- do not log extracted text;
- do not log patient identifiers;
- use masked or internal IDs in metrics;
- local providers are the default for PHI;
- external providers require an explicit deployment policy;
- provider requests must be traceable without storing raw prompts in logs.

### 32.3 Document prompt injection

Document content is untrusted data.

Rules:

- instructions found inside documents cannot change system behavior;
- extracted text is wrapped as quoted evidence;
- indexing marks source content as untrusted;
- model prompts distinguish instructions from document evidence;
- suspicious instruction-like content may be tagged for evaluation but remains searchable as content;
- no document can request tools, secrets, permission changes, or system-prompt disclosure.

### 32.4 Authorization

Every API, file stream, overlay, export, SSE event, fact, and review action uses existing permission services.

### 32.5 Audit events

Audit:

- upload;
- view;
- file download;
- raw OCR view;
- review action;
- export;
- retry;
- reprocess;
- cancellation;
- deletion;
- permission denial.

Audit metadata must not contain raw clinical text.

---

## 33. Error handling and recovery

### 33.1 Error classes

```text
invalid_file
unsupported_format
file_too_large
too_many_pages
encrypted_pdf
corrupted_pdf
malware_suspected
storage_unavailable
redis_unavailable
worker_unavailable
native_extraction_failed
ocr_provider_unavailable
layout_provider_unavailable
clinical_extractor_failed
terminology_provider_failed
embedding_provider_failed
database_failure
graph_failure
cdss_failure
job_timeout
cancelled
permission_denied
```

### 33.2 Retry policy

Retryable:

- transient provider timeout;
- Redis or database connection interruption;
- temporary storage failure;
- rate limit;
- worker interruption.

Terminal:

- invalid file;
- encrypted PDF;
- unsupported format;
- security quarantine;
- deterministic schema failure caused by corrupt source.

### 33.3 Partial success

- one failed page does not necessarily fail the whole document;
- failed pages create warnings or review items;
- mandatory source or database failure fails the revision;
- Graph and CDSS failures do not erase successful extraction and indexing;
- the final status truthfully reflects degraded processing.

### 33.4 Stale-run watchdog

A scheduled watchdog:

- identifies runs without heartbeat beyond the configured timeout;
- marks active stage failed-retryable;
- releases the active-run lock;
- optionally re-enqueues within retry policy;
- records a processing event.

---

## 34. Idempotency and data integrity

### 34.1 Upload idempotency

The API accepts an optional idempotency key.

Duplicate requests with the same key and source hash return the existing document and processing run.

### 34.2 Stage idempotency

Each stage uses:

- document ID;
- run ID;
- revision;
- stage name;
- input content hash;
- provider version;
- configuration hash.

Completed outputs are reused when hashes match.

### 34.3 Upsert rules

- pages unique by document, revision, and page number;
- blocks unique by deterministic block key within page and revision;
- facts unique by extraction candidate key, while conflicting facts remain separate candidates;
- chunks unique by revision and content hash;
- review actions are append-only.

### 34.4 Atomic activation

A transaction activates a revision only after:

- mandatory page results exist;
- reconstruction integrity checks pass;
- source links resolve;
- index counts match expected counts;
- permission metadata is present.

---

## 35. Observability

### 35.1 Structured logs

Required fields:

```text
trace_id
document_id
processing_run_id
revision_number
stage
queue
job_id
page_number nullable
engine
engine_version
duration_ms
status
error_code nullable
retry_count
```

Do not log raw text, facts, names, identifiers, or document images.

### 35.2 Metrics

```text
document_upload_total
document_processing_total
document_processing_failed_total
document_processing_duration_seconds
document_stage_duration_seconds
document_queue_depth
document_queue_wait_seconds
document_pages_total
document_native_pages_total
document_ocr_pages_total
document_layout_vision_pages_total
document_degraded_pages_total
document_low_confidence_regions_total
document_facts_extracted_total
document_review_items_total
document_review_completion_seconds
document_index_duration_seconds
document_graph_duration_seconds
document_cdss_duration_seconds
document_retry_total
document_cost_estimate_total
provider_request_total
provider_failure_total
provider_latency_seconds
```

Labels must avoid unbounded cardinality. Document IDs must not be Prometheus labels.

### 35.3 Tracing

Create spans for:

- upload;
- each pipeline stage;
- provider calls;
- page processing batches;
- database writes;
- embedding batches;
- graph extraction;
- CDSS.

### 35.4 Dashboards

Grafana views:

- queue health;
- documents by state;
- stage latency;
- extraction route distribution;
- provider errors;
- review backlog;
- low-confidence rate;
- throughput and cost;
- evaluation gate status.

---

## 36. Performance and resource controls

### 36.1 API targets

| Operation | Target |
|---|---:|
| Upload validation and enqueue, excluding file transfer | P95 < 500 ms |
| Intelligence summary | P95 < 500 ms |
| Paginated facts or blocks | P95 < 700 ms |
| SSE event delivery after database event | P95 < 1 s |

### 36.2 Processing targets

Reference profiles:

| Route | Target |
|---|---:|
| Native text extraction | P95 ≤ 0.5 s/page |
| Standard printed OCR on 4 vCPU CPU profile | P95 ≤ 8 s/page |
| Layout-aware parser using approved GPU or remote provider | P95 ≤ 25 s/page |
| Embedding | Batched; no per-chunk serial calls |
| 50-page mixed document | Asynchronous completion target ≤ 10 minutes on configured reference profile |

Targets are measured on versioned reference hardware and stored with evaluation artifacts.

### 36.3 Resource controls

- page images processed in bounded batches;
- no entire large PDF rendered into memory;
- vision concurrency configurable;
- default CPU vision concurrency is 1;
- embedding batching configurable;
- temporary-file cleanup guaranteed;
- provider timeouts and circuit breakers;
- queue backpressure;
- per-user or organization upload rate limits.

---

## 37. Evaluation and release gates

### 37.1 Evaluation dataset

Use synthetic or de-identified documents only.

The versioned benchmark contains at least 200 pages across:

| Category | Minimum share |
|---|---:|
| Native text PDF | 15% |
| Clean printed scan | 15% |
| Low-resolution or noisy scan | 10% |
| Rotated or skewed page | 10% |
| Multi-column document | 10% |
| Laboratory table | 15% |
| Prescription or medication list | 10% |
| Forms and checkboxes | 5% |
| Mixed or handwritten content | 5% |
| Headers, footers, stamps, signatures, or complex layout | 5% |

The benchmark must include Vietnamese text and clinically relevant numeric/unit cases.

### 37.2 Ground truth

Ground truth includes:

- page text;
- reading order;
- block types;
- table structure;
- clinical facts;
- negation and temporality;
- source page;
- source bounding boxes;
- review requirement;
- expected downstream eligibility.

### 37.3 Metrics

#### Text

- Character Error Rate;
- Word Error Rate;
- native-text fidelity;
- Vietnamese diacritic error rate.

#### Layout

- block detection precision, recall, and F1;
- block-type accuracy;
- reading-order accuracy;
- heading hierarchy accuracy.

#### Tables and forms

- table detection F1;
- cell value exact match;
- row and column alignment;
- checkbox-state accuracy;
- key-value pairing accuracy.

#### Clinical extraction

- exact match and token F1 by field;
- medication-name recall;
- medication dose and unit accuracy;
- allergy recall;
- lab test/value/unit accuracy;
- diagnosis negation accuracy;
- patient-identifier mismatch detection.

#### Grounding

- correct page citation rate;
- correct block-link rate;
- bounding-box overlap;
- unsupported fact rate;
- stale-revision citation rate.

#### System

- stage latency;
- page throughput;
- queue wait;
- memory;
- provider failure;
- retry success;
- cost per page;
- review workload per document.

### 37.4 Minimum release gates

| Gate | Requirement |
|---|---:|
| Unauthorized content returned | 0 cases |
| Unsupported clinical fact rate | ≤ 1% |
| Correct page citation | 100% for accepted facts |
| Broken source link | 0 cases |
| Clean printed OCR median CER | ≤ 5% |
| Low-quality scan median CER | ≤ 12% |
| Reading-order accuracy | ≥ 95% |
| Laboratory table cell exact match | ≥ 92% |
| High-risk clinical field recall | ≥ 97% |
| High-risk field precision | ≥ 95% |
| Diagnosis negation accuracy | ≥ 97% |
| Patient mismatch detection recall | 100% |
| Retry creates duplicate active chunks | 0 cases |
| Active revision atomicity failures | 0 cases |
| Real adapter execution artifacts | Required |
| Mock-only provider result reported as pass | Forbidden |

### 37.5 Evaluation artifacts

Every evaluation run emits:

```text
run.json
cases.jsonl
metrics.json
errors.jsonl
junit.xml
summary.md
provider-manifest.json
hardware-profile.json
```

Release evaluation must fail when the requested real adapter is unavailable. It cannot pass by skip.

---

## 38. Testing strategy

### 38.1 Unit tests

- native quality scoring;
- routing decisions;
- selective page OCR;
- rotation and skew handling;
- Unicode normalization;
- conservative hyphen repair;
- reading-order reconstruction;
- table reconstruction;
- form key-value pairing;
- decimal comma parsing;
- unit normalization;
- medication field separation;
- negation and temporality;
- confidence calibration;
- review policy;
- FHIR resource selection;
- source-link integrity;
- idempotency hashes;
- permission checks.

### 38.2 Integration tests

- upload returns HTTP 202;
- RQ dependencies execute in order;
- native document skips vision;
- scanned document runs OCR;
- mixed document processes only required pages;
- layout document preserves table structure;
- provider timeout retries;
- new revision does not replace active revision before success;
- facts retain page and block evidence;
- approved facts become indexable;
- blocking facts remain excluded from CDSS;
- Graph failure preserves active RAG index;
- retry does not duplicate pages, facts, or chunks;
- stale watchdog recovers abandoned run.

### 38.3 API contract tests

- upload;
- summary;
- pages and blocks;
- facts;
- review;
- events;
- retry;
- reprocess;
- cancellation;
- exports;
- errors;
- pagination;
- optimistic-lock conflict;
- authorization.

### 38.4 Frontend tests

- timeline state rendering;
- SSE updates and reconnect;
- polling fallback;
- page and fact synchronization;
- bounding-box overlay;
- low-confidence filters;
- review confirm/correct/reject;
- optimistic-lock conflict UI;
- raw versus formatted tabs;
- mobile tabs;
- PDF range loading;
- permission denial;
- degraded provider state;
- keyboard and accessibility behavior.

### 38.5 Security tests

- MIME spoofing;
- path traversal;
- oversized file;
- encrypted PDF;
- malformed PDF;
- document access across patient boundaries;
- export access;
- SSE access;
- raw OCR access;
- prompt-injection content;
- audit logs do not contain PHI;
- external-provider policy is enforced.

### 38.6 End-to-end clinical scenario

Required scenario:

1. upload a mixed laboratory report;
2. native pages use PyMuPDF;
3. scanned table page uses layout-aware parsing;
4. potassium is extracted with value, unit, range, and evidence;
5. a low-confidence medication dose creates a blocking review item;
6. reviewer corrects the dose;
7. active FHIR draft regenerates;
8. hybrid chunks use the reviewed value;
9. Graph links facts to source document;
10. CDSS creates an evidence-linked alert;
11. the UI opens the alert’s exact source region.

---

## 39. Configuration

Suggested variables:

```text
DOCUMENT_INTELLIGENCE_ENABLED=true
DOCUMENT_MAX_SIZE_MB=50
DOCUMENT_MAX_PAGES=300
DOCUMENT_STORAGE_BACKEND=local
DOCUMENT_STORAGE_PATH=
DOCUMENT_TEMP_PATH=
DOCUMENT_RENDER_DPI=250

REDIS_URL=
RQ_DOCUMENT_FAST_QUEUE=document-fast
RQ_DOCUMENT_VISION_QUEUE=document-vision
RQ_DOCUMENT_CLINICAL_QUEUE=document-clinical
RQ_DOCUMENT_INDEX_QUEUE=document-index
RQ_STAGE_TIMEOUT_SECONDS=1800
RQ_MAX_RETRIES=3
RQ_STALE_RUN_SECONDS=3600

NATIVE_EXTRACTOR=pymupdf
OCR_PROVIDER=paddleocr
LAYOUT_PROVIDER=paddleocr_vl
CLINICAL_EXTRACTOR_PROVIDER=
TERMINOLOGY_PROVIDER=local
EXTERNAL_PHI_PROVIDER_ALLOWED=false

NATIVE_ACCEPTANCE_SCORE=0.80
OCR_ACCEPTANCE_SCORE=0.78
GENERAL_AUTO_ACCEPT_CONFIDENCE=0.95
GENERAL_REVIEW_CONFIDENCE=0.80
HIGH_RISK_AUTO_ACCEPT_ENABLED=false

EMBEDDING_PROVIDER=
EMBEDDING_MODEL=
EMBEDDING_BATCH_SIZE=32

DOCUMENT_SSE_HEARTBEAT_SECONDS=15
DOCUMENT_EVENT_RETENTION_DAYS=30
DOCUMENT_SOURCE_RETENTION_DAYS=
DOCUMENT_PREVIEW_CACHE_DAYS=7

OCR_EVAL_REAL_ADAPTER_REQUIRED=true
OCR_EVAL_DATASET_VERSION=
OCR_EVAL_RELEASE_GATE_ENABLED=true
```

Secrets must use the repository’s current secret-management approach and must never be committed.

---

## 40. Suggested module boundaries

These are design boundaries, not a mandatory exact file list.

### 40.1 Backend

```text
src/hospital_ai/
  core/
    interfaces/
      document_extractor.py
      layout_parser.py
      clinical_extractor.py
      terminology_provider.py
      confidence_calibrator.py
    document_intelligence/
      types.py
      states.py
      policies.py
      exceptions.py

  services/
    document_intelligence/
      orchestrator.py
      preflight.py
      classifier.py
      router.py
      normalization.py
      reconstruction.py
      clinical_extraction.py
      validation.py
      review_service.py
      fhir_draft.py
      indexing.py
      provenance.py

  workers/
    document_intelligence_jobs.py

  api/
    routes/
      document_intelligence.py

  schemas/
    document_intelligence.py

  db/
    models/
      document_intelligence.py
```

### 40.2 Frontend

```text
src/
  routes/
    documents/
      $documentId.tsx

  components/hms/document-intelligence/
    DocumentMetadataCard.tsx
    ProcessingTimeline.tsx
    DocumentQualitySummary.tsx
    SourceDocumentViewer.tsx
    EvidenceOverlay.tsx
    IntelligenceWorkspace.tsx
    FormattedDocumentView.tsx
    ClinicalFactsView.tsx
    RawOcrView.tsx
    ReviewQueue.tsx
    ProcessingDiagnostics.tsx

  hooks/
    useDocumentIntelligence.ts
    useDocumentEvents.ts
    useEvidenceSelection.ts

  lib/
    document-intelligence-api.ts
```

Module names must be adapted to existing repository conventions discovered during implementation.

---

## 41. Migration and backward compatibility

### 41.1 Existing documents

Existing documents remain readable.

A migration may mark them:

```text
intelligence_status = legacy
```

They can be reprocessed into a revision on demand.

### 41.2 Existing chunks

Existing chunks remain active until a successful intelligence revision is activated.

The migration must not delete or invalidate the current knowledge base.

### 41.3 Existing APIs

Existing upload and document-detail contracts should remain compatible where practical.

New intelligence fields are additive. Breaking changes require:

- API versioning;
- contract updates;
- frontend migration;
- documented deprecation.

### 41.4 Existing evaluation

The new OCR and document-intelligence suite integrates with the current source-backed evaluation runner rather than creating an unrelated test harness.

---

## 42. UX copy

### 42.1 Queued

> Document is waiting to be processed.

### 42.2 Native extraction

> Reading embedded PDF text.

### 42.3 OCR

> Running OCR on page 6 of 24.

### 42.4 Layout parsing

> Reconstructing tables and document layout.

### 42.5 Clinical extraction

> Identifying clinical facts and source evidence.

### 42.6 Review required

> Some clinically important fields require verification before they can be used for decision support.

### 42.7 Ready with warnings

> The document is searchable. Some low-confidence regions remain available for review.

### 42.8 Ready

> The document is ready for evidence-grounded search and clinical review.

### 42.9 Failed

> Document processing could not be completed. Review the failed stage or retry processing.

---

## 43. Risks and mitigations

| Risk | Mitigation |
|---|---|
| OCR appears correct but changes a medication dose | High-risk review policy, raw evidence, source overlay, no silent correction |
| Tables flatten into misleading text | Dedicated table structure, cell evidence, ambiguity state |
| External provider receives PHI | Local-first default, explicit provider policy, audited configuration |
| Vision model exceeds VPS resources | Queue isolation, concurrency 1, selective routing, configurable remote/GPU adapter |
| Reprocessing duplicates chunks | Revision-specific hashes, unique constraints, atomic activation |
| Low-confidence facts trigger CDSS | Evidence eligibility gate and blocking review |
| LLM invents unsupported facts | Strict schema, source requirement, unsupported-fact rejection |
| Prompt injection inside a document | Treat document as untrusted evidence, never as instructions |
| Review edits overwrite each other | Optimistic locking and append-only review actions |
| Evaluation passes using mocks | Real-adapter release gate and provider manifest |
| New revision fails mid-process | Keep previous active revision until atomic success |
| Raw OCR is lost after formatting | Immutable raw representation plus versioned normalized output |

---

## 44. Definition of done

The feature is complete only when all conditions below are satisfied.

### 44.1 Processing

- upload returns HTTP 202;
- RQ executes the complete pipeline asynchronously;
- native extraction is preferred when appropriate;
- OCR is selective at page or region level;
- complex layouts use a real layout-aware adapter;
- every engine decision is recorded;
- raw, normalized, structured, and formatted outputs are stored;
- retries are idempotent;
- reprocessing creates a revision;
- active revision activation is atomic;
- stale jobs are recoverable.

### 44.2 Structure and clinical intelligence

- headings, paragraphs, lists, tables, forms, and reading order are reconstructed;
- tables retain row, column, cell, and coordinate information;
- clinical facts use strict schemas;
- negation and temporality are preserved;
- terminology and unit candidates are separated from source values;
- every accepted fact has a valid source page and region;
- high-risk uncertainty creates a review item;
- human corrections retain original machine output;
- FHIR-ready draft output is generated from the active reviewed revision.

### 44.3 Downstream systems

- section-aware chunks are created;
- pgvector and PostgreSQL full-text indexes are updated;
- permission metadata is present before activation;
- Graph nodes and edges link to fact evidence;
- CDSS consumes only eligible facts;
- CDSS alerts link back to exact document evidence;
- downstream failures are isolated and retryable.

### 44.4 UI

- metadata and quality summary are visible;
- processing timeline updates through SSE;
- original PDF or image displays correctly;
- formatted, structured, raw, review, and diagnostic views exist;
- fact selection highlights exact source evidence;
- review workflow supports confirm, correct, reject, and unreadable;
- mobile and tablet layouts work;
- loading, empty, warning, failure, and degraded states are implemented;
- accessibility checks pass.

### 44.5 Security and quality

- all endpoints enforce role and patient scope;
- no PHI appears in logs or metric labels;
- file validation and quarantine behavior work;
- document prompt injection cannot alter agent instructions;
- audit events cover sensitive actions;
- real-adapter evaluation artifacts are generated;
- release gates meet the thresholds in this specification;
- backend lint, format, tests, migrations, and contract checks pass;
- frontend lint, typecheck, unit tests, build, and E2E tests pass;
- no success claim is made for an adapter that was skipped or mocked.

---

## 45. Required implementation deliverables

The implementation handoff must include:

1. database migrations;
2. backend provider contracts and implementations;
3. RQ queues and worker commands;
4. API and SSE contracts;
5. frontend document-intelligence workspace;
6. human-review workflow;
7. FHIR-ready export;
8. hybrid RAG and Graph integration;
9. evidence-gated CDSS integration;
10. structured logs, metrics, traces, and dashboards;
11. benchmark dataset manifest and ground-truth format;
12. evaluation runner integration and release gates;
13. unit, integration, contract, security, frontend, and E2E tests;
14. local and production configuration documentation;
15. migration and rollback procedure;
16. list of real adapters exercised;
17. known limitations that remain after verification.

---

## 46. Locked design decisions

The following decisions are part of this specification:

1. The feature is named **Clinical Document Intelligence**, not only OCR.
2. PDF and image inputs are supported; CSV remains a separate structured ingestion path.
3. Extraction is adaptive and page-level.
4. PyMuPDF is the preferred native extractor.
5. PaddleOCR is the standard printed OCR adapter.
6. A layout-aware vision adapter is required for complex documents.
7. Raw output is immutable.
8. Structured blocks and provenance are first-class database records.
9. Clinical facts require exact source links.
10. High-risk uncertain fields require human review.
11. FHIR output is a draft and is not automatically written to an external EHR.
12. RAG chunks are structure-aware and revisioned.
13. CDSS uses evidence-eligible facts only.
14. Reprocessing is revisioned and atomically activated.
15. Real adapters are mandatory for release evaluation.
16. Permission checks apply before every content read and every AI downstream operation.
17. The current repository architecture is extended, not replaced.
