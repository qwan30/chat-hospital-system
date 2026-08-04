# Unified Clinical Document Intelligence, Revisioned OCR, Graph RAG, and Grounded Chat — Design Specification

**Spec ID:** CDI-RAG-V2  
**Repository:** `qwan30/chat-hospital-system`  
**Date:** 2026-08-04  
**Status:** Draft for owner review  
**Delivery scope:** Full integrated target; this is not an MVP specification  
**Candidate successor to:** `docs/superpowers/specs/2026-07-31-clinical-document-intelligence-design.md`

---

## 1. Executive decision

The project will be positioned as a **permission-aware Clinical Document Intelligence system**, not as a general medical chatbot.

The system will use one logical, versioned corpus across the complete product flow:

```text
PDF / image source
→ native extraction or OCR
→ revisioned human correction
→ approval
→ structured facts
→ chunking + BM25 + embeddings
→ revision-aware clinical graph
→ Graph RAG and hybrid retrieval
→ grounded chat with citations and safe refusal
→ one end-to-end benchmark over the same corpus items
```

The same underlying clinical cases must support OCR, correction, retrieval, graph construction, timeline generation, explainability, evidence tracing, and chat evaluation. Separate function-specific datasets may be used only for **model qualification research**, never to inflate the product benchmark.

The source artifact remains authoritative. Machine OCR, human corrections, chunks, embeddings, graph nodes, graph edges, timelines, and answers are derived, versioned representations. No derived representation may silently overwrite source evidence.

---

## 2. Product thesis

The strongest portfolio and interview story is:

> Authorized hospital users upload a PDF or image, inspect and correct OCR output, approve a revision, and then use permission-aware RAG and Graph RAG to explore the patient record. Every retrieved fact, graph relation, timeline event, and chat claim remains traceable to the approved document revision and exact source evidence.

This design deliberately avoids the weaker story of “Gemini chats with PDFs.” It demonstrates:

- asynchronous document processing;
- local OCR and handwriting recognition;
- immutable evidence and version history;
- human-in-the-loop quality control;
- PostgreSQL and pgvector data modeling;
- Cloudflare R2 object storage;
- hybrid and graph-assisted retrieval;
- role- and patient-scoped authorization;
- evidence-linked UI;
- reproducible benchmarking;
- external LLM provider abstraction without claiming clinical autonomy.

---

## 3. Current-state findings

### 3.1 Existing ingestion behavior

The current worker performs OCR, chunking, embedding, PostgreSQL full-text indexing, graph extraction, and document readiness in one pipeline. OCR output is therefore indexed before a user can review and correct the page text.

Current high-level behavior:

```text
Upload
→ OCR/native extraction
→ delete and recreate pages/chunks
→ chunk
→ embed
→ populate tsvector
→ graph extraction
→ ready
```

The revised design must split extraction from approval and indexing.

### 3.2 Existing OCR behavior

The current OCR service:

1. extracts native text from a PDF page when available;
2. renders page images for the frontend;
3. falls back to PaddleOCR for image-only pages;
4. stores page text and confidence.

This is a useful base. The missing capability is an explicit handwriting recognition route and a review gate before downstream indexing.

### 3.3 Existing OCR UI

The document detail page already displays:

- document metadata and processing status;
- original document preview on the left;
- extracted text on the right;
- OCR confidence;
- a separate structured-fact review route.

The extracted text panel is read-only and uses a typewriter presentation component. The existing review route edits extracted structured facts, not the complete page OCR text.

### 3.4 Existing Graph RAG behavior

The graph API already enforces patient permission and source visibility. It currently contains fixed caps and fixed presentation behavior:

- entity query limit: 200;
- relation query limit: 500;
- reasoning path preview: first 5 relations;
- no public query parameters for node count, edge count, hop depth, entity types, relation types, confidence, date range, or document scope.

Graph data is currently useful for display and chat enrichment, but it is not yet a complete explainability and exploration subsystem.

### 3.5 Existing chat safety and streaming behavior

The chat backend already provides meaningful controls:

- patient-scope permission checks;
- prompt-injection guardrail;
- output guardrail;
- evidence threshold;
- safe no-evidence response;
- rejection of citations that reference IDs outside the authorized retrieved evidence set.

However, citation validation currently proves only that cited IDs exist in the retrieved evidence. It does **not** prove that each factual claim is supported by the cited text.

The endpoint is named and transported as SSE streaming, but grounded generation currently buffers the complete model answer, validates it, and then emits the validated answer in line chunks. This protects users from unvalidated output but is not true token-by-token generation streaming.

The frontend is already able to accumulate SSE token chunks and show progressive text. This transport can support validated sentence streaming without replacing the frontend architecture.

### 3.6 Existing evidence UI

The evidence rail already shows:

- document title;
- page number;
- snippet preview;
- relevance score;
- detail modal;
- link to the document.

Current gaps:

- the date is hardcoded to `Recent`;
- no revision ID or approval state is shown;
- no exact chunk ID, source offsets, or bounding box is shown;
- no graph path is shown;
- inline citation links use an evidence identifier as the route document parameter instead of consistently using `document_id`;
- evidence numbering is per-response inline but globally reassigned in the rail, which can diverge across a multi-message conversation;
- assistant content is plain text rather than safely rendered Markdown.

### 3.7 Existing evaluation platform

The repository already contains a deterministic source-backed benchmark generator with exactly 300 cases:

| Category | Cases |
|---|---:|
| Single-hop | 70 |
| Multi-document | 50 |
| Temporal conflict | 35 |
| Graph multi-hop | 45 |
| Overlapping patient | 30 |
| Permission adversarial | 45 |
| Safe refusal | 25 |
| **Total** | **300** |

It also defines a 50-case sentinel subset. Cases are generated from the `synthetic-100-v2` canonical patient documents and lab sources, with evidence locators and authorization constraints.

A recorded retrieval ablation reported, on 39 answer-policy sentinel cases and zero model tokens:

| Mode | Recall@5 | MRR | nDCG@5 | Unauthorized cases |
|---|---:|---:|---:|---:|
| Vector | 0.025641 | 0.025641 | 0.025641 | 0 |
| BM25 | 1.000000 | 1.000000 | 1.000000 | 0 |
| Hybrid | 1.000000 | 1.000000 | 1.000000 | 0 |

Those results are a deterministic retrieval baseline, not proof of general clinical quality. The report itself remains conditional because sentinel review, chat parity, image OCR, and graph multi-hop gates were incomplete.

---

## 4. Non-negotiable integrity rule

Benchmark results must never be fabricated, manually improved, or attributed to a model that did not produce them.

The project may use a local open-source model as an auxiliary judge, but every published result must include:

- evaluator model repository;
- pinned revision or artifact hash;
- quantization;
- prompt version;
- decoding configuration;
- input case IDs;
- raw evaluator output;
- metric implementation version;
- Git SHA;
- corpus version;
- execution timestamp;
- known limitations.

Deterministic metrics and human-reviewed sentinel results are release gates. LLM-as-judge results are supplemental analysis and must be labelled as such.

---

## 5. One unified corpus

### 5.1 Definition

The product benchmark will use one logical corpus named:

```text
hospital-ai-unified-clinical-corpus-v3
```

“One corpus” does not mean one file format. It means every representation shares a stable `corpus_item_id` and refers to the same underlying case and source evidence.

A corpus item may contain:

```text
corpus_item_id
├── source PDF/image
├── canonical transcript
├── OCR engine outputs
├── approved corrected transcript
├── structured clinical facts
├── expected graph nodes and edges
├── expected timeline events
├── questions and answer policies
├── allowed/forbidden evidence locators
└── permission scenarios
```

The OCR benchmark, retrieval benchmark, graph benchmark, timeline benchmark, and chat benchmark must reference the same corpus items and approved revisions.

### 5.2 Fairness requirement

No function may select an easier unrelated dataset for its headline score.

Examples:

- OCR score must be calculated on source images belonging to corpus items that are also indexed and queried.
- Graph accuracy must be measured against relations derived from the same approved document revisions used by chat.
- Chat evaluation must retrieve only chunks and graph evidence created from those approved revisions.
- Timeline accuracy must be evaluated against events annotated in the same patient documents.

### 5.3 Dataset partitions

The corpus may have partitions, but not unrelated function-specific benchmarks:

- `train`: only for optional OCR fine-tuning;
- `qualification`: model selection and threshold calibration;
- `development`: engineering and prompt iteration;
- `sentinel`: manually reviewed release gate;
- `holdout`: final evaluation.

Patient IDs, document families, and near-duplicate renderings must not cross partitions.

### 5.4 Source strategy

The safest primary corpus remains synthetic/de-identified clinical content because open real handwritten clinical records commonly introduce privacy, licensing, and distribution risk.

The corpus should include multiple source representations of the same controlled facts:

- native-text clinical PDF;
- scanned PDF;
- photographed page;
- manually handwritten version of selected synthetic notes;
- structured lab CSV rendered as a document where appropriate.

Synthetic handwriting fonts alone do not qualify as real handwriting evaluation. The holdout should include manually written and scanned pages created from synthetic facts, with human-verified transcripts.

Public datasets may be used to qualify a handwriting recognizer, but their results must not replace the unified product benchmark.

### 5.5 Git versus R2

The complete corpus and runtime documents will be stored in private Cloudflare R2. Git will contain:

- corpus schema;
- manifest schema;
- license/provenance registry;
- benchmark cases;
- small deterministic smoke subset from the same corpus version;
- checksums;
- no production PHI.

The smoke subset is not a second dataset. It is a fixed slice of `hospital-ai-unified-clinical-corpus-v3` used for offline tests.

---

## 6. Cloudflare R2 storage design

### 6.1 Design constraint

Cloudflare R2 exposes an S3-compatible API and strongly consistent object storage. At the time of this specification, S3 bucket versioning is not implemented. Therefore the application must implement immutable object versioning through unique keys and PostgreSQL metadata instead of overwriting an R2 key.

### 6.2 Bucket layout

```text
hospital-ai-documents/
├── source/{tenant_id}/{patient_id}/{document_id}/{source_sha256}/original.pdf
├── rendered/{document_id}/{source_sha256}/page-{page}.png
├── extraction/{document_id}/{run_id}/raw-pages.jsonl
├── revisions/{document_id}/{revision_id}/approved-pages.jsonl
├── exports/{document_id}/{revision_id}/document.md
└── benchmark/{corpus_version}/{corpus_item_id}/...
```

Every new source or revision writes a new object key. Existing version keys are immutable.

### 6.3 PostgreSQL is authoritative for access and lineage

R2 stores bytes. PostgreSQL stores:

- tenant, patient, and document ownership;
- object key and checksum;
- source MIME type;
- extraction run;
- revision lineage;
- author identity;
- approval state;
- active revision pointer;
- retention state;
- audit events;
- downstream index generation.

### 6.4 Access pattern

- Buckets remain private.
- Backend authorization is evaluated before object access.
- The backend issues short-lived presigned GET/PUT URLs only after RBAC and patient-scope checks.
- Presigned URLs are treated as bearer tokens and must use short expiry.
- Browser uploads bind the expected content type.
- The frontend never receives R2 API credentials.

### 6.5 Integrity

Every stored artifact records:

- SHA-256 calculated by the application;
- byte size;
- content type;
- R2 ETag;
- source or parent revision;
- uploader or generator;
- upload timestamp.

---

## 7. Revisioned OCR and human correction

### 7.1 Raw OCR is immutable

The UI may present editing as replacing the current text, but the database must never physically overwrite the original machine OCR.

“Save” creates a new revision. “Approve” updates the document’s active approved revision pointer.

```text
Machine OCR revision v1
    ↓ human edit
Human draft revision v2
    ↓ further edit
Human draft revision v3
    ↓ approve
Approved revision v3 becomes current
    ↓ restore v1 or v2
New revision v4 copied from selected historical revision
```

Historical revisions remain read-only.

### 7.2 Required tables

#### `document_extraction_runs`

- `id`
- `document_id`
- `source_sha256`
- `engine_family`
- `engine_model`
- `engine_revision`
- `engine_config`
- `started_at`
- `completed_at`
- `status`
- `peak_rss_mb`
- `latency_ms`
- `error_code`

#### `document_page_revisions`

- `id`
- `document_id`
- `page_number`
- `parent_revision_id`
- `extraction_run_id`
- `revision_number`
- `revision_type`: `machine_ocr | human_edit | restored`
- `raw_text_snapshot`
- `corrected_text`
- `confidence`
- `status`: `machine_draft | human_draft | approved | rejected | superseded`
- `created_by_user_id`
- `created_at`
- `approved_by_user_id`
- `approved_at`
- `edit_reason`
- `content_sha256`
- `version`

#### `document_revision_sets`

A document-wide revision set pins one selected page revision for every page so indexing cannot mix unrelated page versions.

- `id`
- `document_id`
- `revision_number`
- `status`
- `created_by_user_id`
- `created_at`
- `approved_by_user_id`
- `approved_at`
- `index_generation`

#### `document_revision_pages`

- `revision_set_id`
- `page_revision_id`
- `page_number`

#### `document_revision_events`

Append-only audit event:

- actor;
- action;
- timestamp;
- previous status;
- next status;
- reason;
- request trace ID;
- IP address;
- changed page IDs.

### 7.3 Document processing states

```text
uploaded
→ extracting
→ ocr_draft
→ review_required
→ approved
→ indexing
→ ready
```

Additional states:

- `ready_with_warnings`
- `reprocessing`
- `failed_extraction`
- `failed_indexing`
- `quarantined`
- `superseded`

A document cannot become `ready` unless an approved revision set exists.

### 7.4 Optimistic concurrency

Every save includes the revision `version`. A stale editor receives HTTP 409 and must compare before retrying. Concurrent edits never silently replace another user’s work.

### 7.5 Downstream invalidation

Approving a new revision set performs an atomic generation transition:

1. mark prior chunks, embeddings, graph nodes, graph edges, facts, and timeline events as superseded;
2. enqueue indexing for the new approved revision set;
3. create new derived rows linked to the new revision set;
4. activate the new generation only after all required stages succeed;
5. preserve the previous active generation if re-indexing fails.

---

## 8. OCR engine architecture

### 8.1 Adaptive routing

```text
Page preflight
├── native PDF text available and credible → native extraction
├── printed/image page → PaddleOCR route
├── handwriting probability above threshold → handwriting route
└── mixed page → detector splits regions and routes per region
```

The router stores its decision and confidence. A reviewer may force a different engine and create a new extraction run.

### 8.2 Recommended handwriting architecture for the current VPS

The VPS target has 4 GB RAM and is intended for staging/demo. PostgreSQL, pgvector, Redis, backend services, and OCR must share limited memory. OCR worker concurrency defaults to one.

#### Primary Vietnamese handwriting candidate

`DungHugging/vietocr-handwritten-finetune`

- architecture: VietOCR VGG Transformer;
- approximately 37.65M parameters;
- model artifact: approximately 152 MB;
- license: MIT;
- intended input: one handwritten Vietnamese text line;
- self-reported CPU inference: approximately 1–2 seconds per line image;
- reported metrics are inconsistent between the README validation figures and the committed test evaluation artifact.

This candidate must not become the default until the unified corpus qualification run confirms its accuracy, memory, latency, and failure modes.

#### English handwriting fallback

`microsoft/trocr-small-handwritten`

- approximately 61M parameters;
- approximately 247 MB PyTorch repository;
- fine-tuned on IAM English handwriting;
- intended input: cropped single text-line images;
- official model lineage is clear;
- quantized ONNX/GGUF derivatives exist, but third-party conversion quality must be verified locally before deployment.

#### Rejected as default on this VPS

`stepfun-ai/GOT-OCR2_0`

- approximately 0.7B parameters;
- approximately 1.43 GB model weights;
- official usage is GPU-oriented;
- excessive risk of memory pressure and latency on a 4 GB shared CPU VPS.

OCR-VLMs around 0.9B–1.2B parameters are also excluded from the default VPS profile. They may be evaluated on separate hardware but are not deployment assumptions.

### 8.3 Full-page handwriting processing

Line recognizers cannot process an arbitrary full page directly. The pipeline must include:

```text
Page image
→ orientation and dewarp
→ text-region detection
→ line segmentation
→ printed/handwritten region classification
→ recognizer per line
→ reading-order reconstruction
→ page confidence aggregation
```

The existing PaddleOCR detector can be reused for text-region and line detection where qualification proves acceptable. The recognizer is selected per line.

### 8.4 Resource controls

- dedicated OCR worker process;
- concurrency `1` on 4 GB profile;
- lazy model load;
- idle unload after configurable interval;
- memory limit and OOM telemetry;
- page-level retries, not full-document retries;
- model artifact cached outside the application source tree;
- approximately 2 GB swap may protect against transient failure, but steady-state design must not depend on swap;
- OCR queue depth and per-page latency exposed in observability.

### 8.5 Model artifact lifecycle

Model weights are not committed into normal Git history.

A controlled model-sync process will:

1. download a pinned Hugging Face repository revision;
2. verify expected SHA-256;
3. record repository, revision, license, and file hashes in a model registry;
4. mirror the verified artifact into private R2 or a versioned deployment artifact store;
5. allow runtime workers to load only the approved mirrored artifact.

Production runtime must not silently pull `latest` from Hugging Face.

---

## 9. OCR review UI

### 9.1 Page layout

The current document detail route will become a revision-aware workspace.

```text
┌────────────────────────────────────────────────────────────────────┐
│ Document title | Status | Engine | Confidence | Revision dropdown │
│ Save draft | Compare | Reject | Approve & Re-index                │
├───────────────────────────────┬────────────────────────────────────┤
│ Source document viewer        │ OCR editor                         │
│                               │ Tabs: Corrected | Raw | Diff       │
│ Page thumbnails               │ Page text editor                   │
│ Zoom and rotate               │ Low-confidence markers            │
│ Bounding-box highlights       │ Structured facts panel            │
├───────────────────────────────┴────────────────────────────────────┤
│ Processing/revision history drawer                                │
└────────────────────────────────────────────────────────────────────┘
```

### 9.2 Revision dropdown

Each item displays:

```text
v3 · Approved · Trần Thanh Quân · 04 Aug 2026 20:12
v2 · Human draft · Trần Thanh Quân · 04 Aug 2026 20:03
v1 · Machine OCR · vietocr-handwritten@<revision> · 04 Aug 2026 19:58
```

Selecting an old version makes the editor read-only. `Restore as new revision` creates a new child revision; it never changes history.

### 9.3 Editor behavior

- raw OCR is always accessible and immutable;
- corrected text is editable in draft state;
- unsaved changes are clearly shown;
- diff view compares selected revisions;
- confidence highlights are preserved after editing;
- save requires a reason for high-risk clinical field changes;
- approve requires explicit confirmation;
- approving starts re-indexing and displays progress;
- user cannot chat against an unapproved draft by default.

### 9.4 Structured facts

The existing fact review UI remains a second review layer:

1. page text review;
2. structured fact review.

Facts must link to page revision, bounding box, raw value, normalized value, confidence, reviewer, and status.

---

## 10. Revision-aware indexing

### 10.1 Source of truth

Only an approved document revision set is eligible for the active retrieval index.

### 10.2 Chunk metadata

Every chunk must include:

- tenant ID;
- patient ID;
- document ID;
- document revision set ID;
- page revision ID;
- page number;
- text offsets;
- bounding boxes where available;
- section type;
- source text SHA-256;
- approval state;
- index generation;
- access-control tags.

### 10.3 Retrieval stores

- PostgreSQL rows remain authoritative;
- `tsvector` supports lexical/BM25-style retrieval;
- pgvector supports semantic retrieval;
- graph tables support entity/relation traversal;
- all three retrieval paths enforce the same active-revision and permission filters.

---

## 11. Graph RAG as a product capability

Graph RAG must support five explicit jobs:

1. explainability;
2. relationship exploration;
3. clinical timeline;
4. evidence trace-back;
5. retrieval enrichment for chat.

### 11.1 Graph model

Every node and edge stores:

- patient ID;
- canonical entity ID;
- entity/relation type;
- normalized label;
- confidence;
- source document ID;
- source revision set ID;
- source page revision ID;
- source chunk ID;
- evidence locator;
- effective date or observed date where applicable;
- extraction run/model;
- status: active, superseded, rejected.

### 11.2 Explainability

A graph-assisted answer returns an explanation object:

```json
{
  "query_entities": ["Metformin", "HbA1c"],
  "paths": [
    {
      "nodes": ["Patient", "Type 2 Diabetes", "Metformin", "HbA1c"],
      "relations": ["has_diagnosis", "treated_by", "monitored_by"],
      "evidence_ids": ["E1", "E2"]
    }
  ]
}
```

The UI must distinguish graph reasoning support from final source evidence. Graph edges do not replace citations to source documents.

### 11.3 Relationship exploration controls

Graph API and UI support:

- node limit: 25, 50, 100; backend hard cap 200;
- edge limit: 50, 100, 250; backend hard cap 500;
- hop depth: 1, 2, 3; default 2;
- entity-type multi-select;
- relation-type multi-select;
- minimum confidence;
- document filter;
- approved revision filter;
- date range;
- layout mode;
- include/exclude superseded evidence, restricted to authorized audit users.

### 11.4 Clinical timeline

Timeline events are derived from approved source facts and graph relations. Each event includes:

- event type;
- clinical date;
- recorded date;
- source evidence;
- confidence;
- reviewer state;
- conflict state;
- supersession lineage.

Conflicting dates or values are displayed as conflicts, not silently merged.

### 11.5 Retrieval enrichment

The chat query planner selects retrieval strategies:

| Query type | Primary retrieval |
|---|---|
| Exact value/code/date | BM25/lexical |
| Narrative symptom question | vector/hybrid |
| Relation or medication interaction | graph + hybrid |
| Timeline or change over time | temporal + graph + lexical |
| Multi-document summary | hybrid + reranking |
| No patient evidence | safe refusal |

Graph evidence is fused with lexical/vector candidates, deduplicated, permission-filtered, and reranked. The final prompt contains source chunks, not unsupported graph labels alone.

---

## 12. Grounded chat, validation, and streaming

### 12.1 Scope modes

Chat exposes explicit scopes:

- `Patient`: approved documents for one authorized patient;
- `Document`: selected approved document revisions;
- `Knowledge base`: approved public/hospital references;
- `System help`: product guidance and greetings only.

“General” must not imply unrestricted medical knowledge from model memory.

### 12.2 Current validation that remains

- authentication;
- patient-scope authorization;
- document allow-list filtering;
- input guardrail;
- output guardrail;
- evidence threshold;
- safe refusal;
- citation ID allow-list;
- audit persistence.

### 12.3 New claim-evidence validation

For each factual sentence:

1. extract claims and attached evidence IDs;
2. require at least one authorized evidence ID;
3. compare critical entities, dates, doses, units, values, and negations with cited evidence;
4. run deterministic contradiction checks;
5. optionally run an auxiliary local entailment/judge model;
6. reject, regenerate, or replace unsupported claims with a safe statement;
7. persist validation results per claim.

Medical numbers and negations receive stricter validation than stylistic paraphrases.

### 12.4 Validated sentence streaming

The new backend flow is:

```text
Model token stream
→ private sentence buffer
→ sentence boundary
→ claim/citation validation
→ emit validated sentence as small SSE chunks
→ continue
```

Unvalidated model tokens never reach the client.

The frontend may render validated chunks with a short typing cadence for readability, but telemetry and UI labels must not falsely claim that visual animation equals raw model token streaming.

Required SSE events:

- `status`;
- `validated_chunk` or backward-compatible `token`;
- `citations`;
- `graph_explanation`;
- `metadata`;
- `done`;
- `error`.

### 12.5 Evidence UI corrections

- inline citation links use `document_id`, not `evidence_id`, as route parameter;
- citation identity remains stable per message;
- rail numbering must match inline numbering for the selected message;
- conversation-wide evidence uses stable labels such as message ID plus evidence ID;
- display real document date where available;
- display page, revision, approval status, score, and retrieval method;
- clicking a citation opens the exact page and bounding box;
- graph path evidence appears in a separate explanation panel;
- safe Markdown rendering uses sanitization and disallows executable HTML.

---

## 13. LLM provider strategy

The project keeps a provider abstraction.

### 13.1 Demo profile

- OCR and handwriting recognition run locally;
- embeddings may run locally or through an approved configured provider;
- grounded answer generation may use Gemini or DeepSeek API;
- only synthetic or explicitly de-identified content is used in the public demo;
- provider name, model, latency, and request result are logged;
- provider failure returns a safe service-unavailable response, not a fabricated answer.

### 13.2 Local open-source evaluator

A local model may be used for auxiliary evaluation. Recommended profiles:

- `judge-lite`: quantized `Qwen/Qwen3-0.6B` for smoke and structured rubric output;
- `judge-reference`: quantized `Qwen/Qwen2.5-1.5B-Instruct` on a development machine with more headroom.

Neither replaces deterministic checks or human review. Judge scores are published separately from release-gate metrics.

---

## 14. Unified benchmark v3

### 14.1 Benchmark identity

Every run is bound to:

- corpus version;
- source object hashes;
- approved revision IDs;
- model and embedding versions;
- graph extractor version;
- prompt version;
- evaluator version;
- Git SHA;
- run ID.

### 14.2 OCR metrics

- character error rate (CER);
- word error rate (WER);
- exact line match;
- clinical field exactness;
- numeric value accuracy;
- negation accuracy;
- page success rate;
- correction distance after human review;
- latency per page;
- peak RSS;
- manual review time.

### 14.3 Retrieval metrics

- Recall@k;
- MRR;
- nDCG@k;
- permission leakage count;
- wrong-patient evidence count;
- superseded-revision retrieval count;
- no-evidence precision and recall;
- latency.

### 14.4 Graph metrics

- node precision, recall, F1;
- edge precision, recall, F1;
- path recall for multi-hop cases;
- provenance coverage;
- timeline ordering accuracy;
- date conflict detection recall;
- superseded-edge exclusion;
- graph-assisted retrieval gain against hybrid-only retrieval.

### 14.5 Chat metrics

- answer fact recall;
- unsupported claim rate;
- citation precision;
- citation recall;
- claim-to-evidence entailment rate;
- numeric consistency;
- refusal precision and recall;
- unauthorized disclosure count;
- patient-scope isolation;
- end-to-end latency;
- time to first validated chunk;
- completion persistence success.

### 14.6 Release gates

Minimum release conditions:

- zero unauthorized evidence cases;
- zero wrong-patient citations;
- zero active retrieval from superseded revisions;
- all sentinel cases reviewed by two independent reviewers;
- benchmark data and output hashes reproducible;
- no fabricated metric or model attribution;
- graph provenance coverage at 100% for displayed active nodes and edges;
- all factual chat claims either validated and cited or safely refused;
- OCR performance reported separately for native, printed, English handwriting, and Vietnamese handwriting strata.

The exact numeric quality thresholds are calibrated from the qualification split and then frozen before the holdout run. They are not selected after viewing holdout results.

---

## 15. Error handling

### 15.1 OCR failures

- fail per page where possible;
- preserve successful pages;
- permit engine retry;
- route unresolved pages to review;
- never index an incomplete document as fully ready without warning.

### 15.2 R2 failures

- checksum before metadata commit;
- idempotent object keys;
- retry safe operations;
- do not create a database pointer to a missing object;
- preserve previous active revision.

### 15.3 Re-index failures

- old approved generation remains active;
- new generation remains failed/inactive;
- user receives actionable status;
- no mixed-generation graph or retrieval.

### 15.4 Model resource failures

- catch OOM explicitly;
- record peak memory and model identity;
- unload recognizer;
- retry with configured lighter route only when policy permits;
- never silently switch models without recording it.

---

## 16. Security and privacy

- all source, revision, chunk, graph, timeline, and citation endpoints enforce tenant and patient scope;
- R2 is private;
- presigned URLs use short expiry;
- raw OCR and historical revisions are treated as patient data;
- audit access is role-restricted;
- no real PHI is sent to Gemini, DeepSeek, Hugging Face, or another external provider in the demo profile;
- prompt injection inside document text is treated as untrusted content, not system instruction;
- deleted or quarantined documents are removed from active retrieval and graph views immediately;
- retention and hard-delete operations include R2 objects and all derived generations.

---

## 17. Testing strategy

### 17.1 Unit tests

- state transitions;
- immutable revision creation;
- optimistic concurrency;
- source hash verification;
- page selection in revision sets;
- graph source lineage;
- query planner;
- claim validator;
- citation routing;
- evidence numbering.

### 17.2 Integration tests

- R2-compatible storage adapter;
- PostgreSQL revision transaction;
- OCR worker resource controls;
- approve and re-index flow;
- graph generation replacement;
- chat retrieval against active revision only;
- permission filtering across vector, lexical, and graph paths.

### 17.3 End-to-end tests

```text
Upload source
→ OCR
→ edit
→ save revision
→ inspect dropdown history
→ approve
→ re-index
→ open graph
→ filter and inspect evidence
→ ask patient question
→ receive validated streamed answer
→ open exact citation page/region
```

### 17.4 Benchmark tests

- corpus split leakage detection;
- duplicate and near-duplicate detection;
- raw output retention;
- metric recomputation;
- model/version pinning;
- sentinel reviewer requirements;
- no manually edited aggregate outputs.

---

## 18. Migration from the current system

1. Keep existing source documents and page images.
2. Convert current `DocumentPage.ocr_text` values into immutable machine revision v1 rows.
3. Create one document revision set referencing all v1 pages.
4. Mark existing indexed documents as migrated and approved only for synthetic/demo records that meet migration policy.
5. Attach current chunks and graph rows to migrated revision sets and generation IDs.
6. Add active-generation filters before enabling new revision editing.
7. Replace direct page/chunk deletion with generation supersession.
8. Update chat citations and evidence UI before enabling revision switching.

---

## 19. Full-scope acceptance criteria

The feature is complete only when all of the following are demonstrated:

1. One versioned logical corpus drives OCR, RAG, Graph RAG, timeline, chat, and benchmark cases.
2. Original PDF/image bytes are stored in private R2 with application-level immutable version keys.
3. Raw machine OCR is never destroyed.
4. The UI provides revision dropdown, author, timestamp, status, diff, restore-as-new, and approval.
5. Only approved revision sets become active retrieval and graph evidence.
6. Vietnamese handwriting and English handwriting routes are benchmarked locally and selected by evidence, not model popularity.
7. OCR runs within the 4 GB VPS deployment profile with one-worker concurrency or fails safely with measured evidence.
8. Graph RAG supports explainability, exploration, timeline, evidence trace-back, filters, and chat retrieval enrichment.
9. Graph nodes and edges link to exact approved source evidence.
10. Chat validates patient access, evidence threshold, citation identity, and claim support.
11. The UI displays progressive validated output without exposing unvalidated model text.
12. Inline citations and the evidence rail route to the correct document, page, revision, and bounding box.
13. Existing 300-case and 50-case evaluation assets are incorporated or migrated without misrepresenting their conditional status.
14. All reported benchmark values are reproducible and bound to raw outputs, model versions, corpus versions, and Git SHA.
15. No benchmark value is fabricated or retroactively adjusted.

---

## 20. External technical references reviewed for this design

- Hugging Face `microsoft/trocr-small-handwritten` model card and files.
- Hugging Face `Xenova/trocr-small-handwritten` quantized ONNX derivative.
- Hugging Face `DungHugging/vietocr-handwritten-finetune` model card, weights, and evaluation artifact.
- Hugging Face `stepfun-ai/GOT-OCR2_0` model card and files.
- Hugging Face `Qwen/Qwen3-0.6B` and `Qwen/Qwen2.5-1.5B-Instruct` model cards.
- Cloudflare R2 S3 API compatibility, presigned URL, object lifecycle, and storage behavior documentation as of 2026-08-04.

---

## 21. Design review checklist

- No placeholder requirements remain.
- The full target is specified; implementation may be staged by dependency but may not redefine completion as a reduced MVP.
- The one-corpus requirement is explicit and testable.
- Raw evidence and derived representations have clear ownership.
- R2 versioning does not rely on unsupported S3 bucket versioning.
- OCR model recommendations are conditional on local qualification.
- Existing benchmark limitations are documented.
- Benchmark fabrication is explicitly prohibited.
- Graph RAG has product responsibilities beyond visualization.
- Chat streaming preserves validation before display.
- UI requirements cover document review, evidence, graph explanation, and history.
