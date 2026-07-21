# Implementation Plan: RAG Ingestion, Graph Filtering, and Citations Hardening

This document outlines a detailed multi-phase plan to upgrade the parsing, graph retrieval, and citation validation capabilities of the **AI-Powered Hospital Knowledge Assistant (HOSP-AI-001)**.

---

## Phase 1: Advanced Document and Table Ingestion (RAGFlow-Inspired)
**Goal:** Improve chunk semantics for structured data (tables, grids, Excel, CSV) by adopting layout-aware parsing concepts without bringing in RAGFlow's full infrastructure stack.

### Task 1.1: Layout-Aware PDF & DOCX Parsing
*   **Goal:** Replace plain text extraction with layout-aware text block segmentation to handle double-column medical records, footers, headers, and floating text boxes correctly.
*   **Proposed Implementation:**
    *   Integrate a lightweight layout parsing library (such as `pdfplumber` or `pypdf` with structural grouping) into [pdf_loader.py](file:///D:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/services/loaders/pdf_loader.py).
    *   Identify and strip repeated headers/footers to avoid polluting the vector index.
*   **Acceptance Criteria:**
    *   Double-column clinical notes are parsed in correct reading order (left column then right column) instead of interleaving lines.
    *   All parsing is completed locally without external API calls.
*   **Exceptions:**
    *   Large scanned images within PDFs that require heavy OCR engines (PaddleOCR will still handle basic text, but layout analysis will fallback to text-position heuristics for performance).

### Task 1.2: Structured Table & Grid Preserving Parser
*   **Goal:** Reconstruct tabular data from Excel (`.xlsx`) and PDF tables into semantic Markdown/HTML table blocks instead of converting them into disjointed text lines.
*   **Proposed Implementation:**
    *   Upgrade [table_parser.py](file:///D:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/services/loaders/table_parser.py) and [excel_loader.py](file:///D:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/services/loaders/excel_loader.py) to read rows and columns structured as Markdown tables.
    *   Store table headers alongside each row chunk during indexing so that individual rows retain context (e.g., instead of just embedding `Value: 1.5`, embed `Analyte: Creatinine; Value: 1.5; Unit: mg/dL; Reference Range: 0.7-1.3`).
*   **Acceptance Criteria:**
    *   Tabular files are indexed as readable Markdown tables.
    *   A vector search query for a specific cell value retrieves the context of its header (column name) and row descriptor.
*   **Exceptions:**
    *   Merged cells spanning multiple rows/columns will be simplified to repeat values in all spanned cells rather than complex HTML rendering.

### Task 1.3: Table-Specific Chunking Strategy
*   **Goal:** Prevent table splits across arbitrary token boundaries that render rows unreadable.
*   **Proposed Implementation:**
    *   Modify [chunking.py](file:///D:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/services/chunking.py) to recognize table markdown tags (`|---|`) and treat tables as atomic chunking units or split them strictly by rows, appending the header row to each split chunk.
*   **Acceptance Criteria:**
    *   Zero chunks contain partial, broken markdown tables.
    *   Every split table chunk contains the column headers.
*   **Exceptions:**
    *   Tables exceeding 100 rows will be batched into chunks of 10 rows, each prepended with the header row.

### Phase 1 Checkpoint: Commit & Review
*   **Verification:** Run linting and unit tests (`bun run test` / `pytest`).
*   **Code Review:** Review loader class changes to check memory footprint and table parsing correctness.
*   **Commit:** Git commit changes with message `feat(RAG): layout-aware PDF and structured table ingestion`.

---

## Phase 2: Enhanced Graph RAG Retrieval and Filtering
**Goal:** Add dynamic entity/role-based filtering to the SQL-backed graph database and expose these filters to the API and visual graph layout.

### Task 2.1: Dynamic Entity & Relation Filtering in Graph RAG Service
*   **Goal:** Support filtering by entity type (`drug`, `condition`, `lab`) and relation type (`treats`, `indicates`, `monitored_by`) during graph traversal.
*   **Proposed Implementation:**
    *   Extend `find_related_entities()` in [graph_rag.py](file:///D:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/services/graph_rag.py#L270) to accept optional lists of allowed entity types and relation types.
    *   Update the BFS SQL query to filter `GraphEntity` and `GraphRelation` records at each hop based on these filters.
*   **Acceptance Criteria:**
    *   Executing a graph search with `entity_types=["drug"]` returns only drug nodes and relations connected to them.
    *   BFS traversal respects these constraints at every hop.
*   **Exceptions:**
    *   Root patient node is always returned regardless of the entity type filters.

### Task 2.2: Expose Graph Filters to API Route
*   **Goal:** Add query parameters to `/api/graph/patients/{patient_id}` to allow clients to filter the returned graph payload dynamically.
*   **Proposed Implementation:**
    *   Update [graph.py](file:///D:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/api/routes/graph.py#L33) to accept optional query parameters: `types: list[str] = Query(None)` and `relations: list[str] = Query(None)`.
    *   Pass these filters to the database query logic and compute coordinates only for active nodes.
*   **Acceptance Criteria:**
    *   API returns a `GraphDataResponse` containing only nodes matching the selected type list.
    *   Edges connecting excluded nodes are omitted from the response.
*   **Exceptions:**
    *   If no entities match the filters, return the root patient node with an empty node/edge list instead of raising an error.

### Task 2.3: User-Role Permission Filtering on Graph Nodes
*   **Goal:** Ensure that users with specific roles (e.g., non-clinical administrative staff) cannot see clinical nodes (e.g., `lab` results, sensitive `diagnosis` nodes) even if they have general read access to the patient's record.
*   **Proposed Implementation:**
    *   Integrate [PermissionService](file:///D:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/services/permissions.py) checks into the entity extraction and retrieval query, masking or excluding nodes based on user scope.
*   **Acceptance Criteria:**
    *   An admin user querying the graph receives a graph visualization with `lab` nodes filtered out, while a cardiologist user receives all nodes.
*   **Exceptions:**
    *   General non-PHI nodes (such as appointment dates or basic demographic fields) are visible to all authorized roles.

### Phase 2 Checkpoint: Commit & Review
*   **Verification:** Verify the graph API endpoint and test parameter filtering via query parameters.
*   **Code Review:** Run a security code review on the SQL filters to prevent SQL injection and ensure patient scope isolation.
*   **Commit:** Git commit changes with message `feat(graph): dynamic filters and role permission checks on graph nodes`.

---

## Phase 3: Citations Hardening and Rich UI Rendering
**Goal:** Harden citation validation to eliminate LLM hallucinations and support rich visual references (document names, page numbers, and tabular data view) on the frontend.

### Task 3.1: Strict Citation Text Validation
*   **Goal:** Prevent LLMs from citing sources for facts not contained in the cited chunk.
*   **Proposed Implementation:**
    *   In the citation validation pipeline in [chat_stream.py](file:///D:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/api/routes/chat_stream.py#L179), run an automated check to ensure that the sentence/phrase containing `[E1]` has semantic overlap or keyword match with the actual text in chunk `E1`.
    *   If the LLM makes an assertion (e.g., "Creatinine is 2.5 [E2]") but the text in `E2` does not contain the value "2.5" or "Creatinine", raise a `CitationHallucinationException`.
*   **Acceptance Criteria:**
    *   Any mismatch of medical values (numbers, drug names) between the cited sentence and the source chunk triggers an immediate fallback or warning.
*   **Exceptions:**
    *   Minor grammatical variations or synonym matching (e.g., "sugar level" vs "glucose") are permitted to avoid excessive false positives.

### Task 3.2: Extended Citation Metadata Payload
*   **Goal:** Expose document layout details (such as page number, document name, and whether the cited source is a table) in the API response.
*   **Proposed Implementation:**
    *   Ensure the citation payload returned by the chat API includes structural flags: `is_table: bool`, `source_file: str`, and `page_number: int`.
    *   Update [chat_utils.py](file:///D:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/services/chat_utils.py#L168) to map these fields correctly.
*   **Acceptance Criteria:**
    *   The `/api/chat` and `/api/chat/stream` endpoints return a `citations` array containing metadata for every cited chunk.
*   **Exceptions:**
    *   Dynamic chat messages (e.g., greetings) do not require citations or return an empty array.

### Task 3.3: Rich Citation UI Popover on Frontend
*   **Goal:** Render citations as clickable badges that open a clean side-panel or popover displaying the exact source document, page, and highlighted snippet.
*   **Proposed Implementation:**
    *   Implement a citation component in the frontend using Tailwind/CSS.
    *   If `is_table` is True, render the citation snippet as a formatted table grid instead of markdown source code.
*   **Acceptance Criteria:**
    *   Clicking a citation badge (e.g., `[1]`) opens a modal/drawer showing the document title, page number, and the exact verified chunk text.
    *   Tables are rendered with clear grid borders.
*   **Exceptions:**
    *   If the original document is deleted or missing, display a fallback message stating "Source document is no longer available."

### Task 3.4: Integrate Clinical System Prompt and Formatting Rules (Backend)
*   **Goal:** Standardize LLM responses to use user-friendly clinical language instead of raw database structures or verbatim file dumps.
*   **Proposed Implementation:**
    *   Import and actively use the [RAG_SYSTEM_PROMPT](file:///D:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/core/prompts/rag_system_prompt.py) (which is currently defined but unused in the codebase) or integrate its rules into all reasoning pipelines.
    *   Instruct the LLM to convert raw database rows and unformatted text blocks into clear, clinician-oriented sentences, utilizing markdown headings, bold accents, and list structures.
*   **Acceptance Criteria:**
    *   The LLM no longer dumps raw DB row keys (e.g. `patient_id=...`) and instead writes clean prose.
*   **Exceptions:**
    *   Standard medical abbreviations (e.g. eGFR, BP, BID) should be preserved to align with clinical standard practices.

### Task 3.5: Support Markdown Rendering in Chat Message UI (Frontend)
*   **Goal:** Render markdown formats (such as bolding, lists, and tables) within chat bubbles instead of displaying them as raw string segments.
*   **Proposed Implementation:**
    *   Implement a basic markdown parser or component inside [ChatMessage.tsx](file:///D:/projects/chatbot-hospital-system/app/frontend/src/components/hms/ChatMessage.tsx) to handle formatting tags (`**`, `-`, `###`, etc.) dynamically alongside citation badge replacement.
*   **Acceptance Criteria:**
    *   Markdown syntax is converted to visual HTML layouts, rendering clean bulleted lists, bold headings, and inline emphasis tags on screen.
*   **Exceptions:**
    *   Complex custom tables will be rendered in the citation details sidebar or drawer rather than cluttering the chat bubble.

### Phase 3 Checkpoint: Commit & Review
*   **Verification:** Verify the citation validation pipeline handles hallucinated references correctly and check the markdown parser UI rendering.
*   **Code Review:** Perform a security review of input sanitization in the markdown renderer to prevent XSS.
*   **Commit:** Git commit changes with message `feat(chat): strict citation validator and frontend markdown rendering`.

---

## Phase 4: Advanced RAG Strategies (Learning from LightRAG & RAGFlow)
**Goal:** Implement advanced optimization techniques inspired by LightRAG's graph retrieval mechanisms and RAGFlow's indexing/retrieval pipeline.

### Task 4.1: Incremental Graph Updates (Inspired by LightRAG)
*   **Goal:** Support updating the SQL-backed graph incrementally when a new patient document is uploaded, rather than fully re-indexing the entire patient graph.
*   **Proposed Implementation:**
    *   Update [graph_rag.py](file:///D:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/services/graph_rag.py) to support upserts for `GraphEntity` and `GraphRelation` tables.
    *   When a new document chunk is processed, extract entities and merge them with existing entities (updating confidence/weights) instead of deleting old graph entries.
*   **Acceptance Criteria:**
    *   Uploading a new medical record adds new nodes/edges and increments weights of existing relationships dynamically without modifying unrelated nodes.
*   **Exceptions:**
    *   If a document is deleted, all entities and relationships derived *exclusively* from its chunks must be soft-deleted or cleaned up.

### Task 4.2: Local vs. Global Graph Query Routing (Inspired by LightRAG)
*   **Goal:** Optimize graph-assisted retrieval by distinguishing between detail-specific queries (Local Graph Search) and general trend queries (Global Graph Search).
*   **Proposed Implementation:**
    *   Implement a router inside `find_related_entities()`.
    *   **Local Search:** Focuses on immediate neighbors of extracted seed entities (e.g., "What is the dosage of Aspirin for this patient?").
    *   **Global Search:** Focuses on summarizing high-level diagnoses and timelines across all documents (e.g., "Summarize the patient's medical history over the past 3 years").
*   **Acceptance Criteria:**
    *   The retrieval service automatically detects the query intent and selects either Local Graph Search (BFS depth 1-2) or Global Graph Search (BFS summarizing main nodes) to compile the context.
*   **Exceptions:**
    *   If the LLM cannot confidently determine query intent, it defaults to a hybrid search mode.

### Task 4.3: Visual Citation Bounding Boxes (Inspired by RAGFlow)
*   **Goal:** Store text block coordinates during OCR/parsing to highlight the exact cited paragraph on the source PDF document.
*   **Proposed Implementation:**
    *   Modify [pdf_loader.py](file:///D:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/services/loaders/pdf_loader.py) to capture text bounding boxes (x, y, width, height) returned by the parser.
    *   Save these coordinates as metadata in the `document_chunks` database table.
    *   Pass the coordinates in the citation metadata payload to the frontend.
*   **Acceptance Criteria:**
    *   The frontend PDF viewer draws a colored outline overlay on the exact paragraph corresponding to the cited evidence chunk.
*   **Exceptions:**
    *   Non-PDF formats (such as Excel or raw text files) do not have coordinates; they will display text/table snippets instead.

### Task 4.4: Multi-Recall Search Optimization & Reranking (Inspired by RAGFlow)
*   **Goal:** Balance keyword and semantic matches using Reciprocal Rank Fusion (RRF) and fine-tuned reranker thresholds.
*   **Proposed Implementation:**
    *   Optimize [retrieval.py](file:///D:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/services/retrieval.py) and [reranking.py](file:///D:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/services/reranking.py) to dynamically adjust RRF constants and reranker score cutoffs based on the query type (e.g., higher keyword weight for drug names, higher semantic weight for symptoms).
*   **Acceptance Criteria:**
    *   Queries for specific clinical codes or drug names yield 100% recall of matching documents.
    *   Reranked results show higher clinical relevance in test datasets.
*   **Exceptions:**
    *   General chit-chat queries bypass this multi-recall pipeline entirely.

### Phase 4 Checkpoint: Commit & Review
*   **Verification:** Run RAG evaluation test scripts to verify the recall rates and check the visual highlights in the PDF viewer.
*   **Code Review:** Check the incremental graph update logic to ensure soft-deletion handles deleted documents correctly.
*   **Commit:** Git commit changes with message `feat(RAG): incremental graph updates and multi-recall search optimization`.
