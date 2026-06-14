# End-to-End Business Flows

> Project: HOSP-AI-001 · Version: 1.0 · Last Updated: 2026-06-14  

## BF-001: Patient Question → Cited Answer

```
Clinician opens Chat → Selects patient context → Types question
  → BFF checks permission (ABAC: scope + expiration + department)
  → DENIED? → HTTP 403 + audit_logs (outcome=denied)
  → ALLOWED? → Embed question → Retrieve (vector+BM25+Graph)
  → Rerank → Generate (LLM) → Validate citations
  → NO EVIDENCE? → Safe refusal + audit
  → EVIDENCE? → Store ai_query + evidence + chat_message
  → Return answer with citations, confidence, disclaimer
  → Record metrics (latency, docs, citations)
```
**APIs:** POST /chat, POST /chat/stream | **Tables:** ai_queries, retrieved_evidence, chat_messages, audit_logs

## BF-002: Document Upload → OCR → Index

```
Clinician uploads PDF → System stores file (status=uploaded)
  → RQ enqueues OCR → status=ocr_processing
  → Worker: PyMuPDF extracts text → document_pages rows
  → SUCCESS? → ocr_completed → Enqueue indexing
  → FAILURE? → ocr_failed + ocr_error → Retry available
  → Indexing: Chunk text → Generate embeddings → document_chunks
  → status=indexed → Searchable via vector/BM25
```
**APIs:** POST /documents/upload, POST /documents/{id}/retry-ocr | **Tables:** documents, document_pages, document_chunks

## BF-003: Access Request → Approval

```
Clinician lacks treatment relationship
  → Patient access returns 403 + DeniedPanel
  → Opens Access Request → Enters justification + urgency
  → POST /access-requests → Logged + forwarded to HMS
  → HMS admin approves → Temporary patient_permission created
  → Clinician can now query patient → All steps in audit_logs
```
**APIs:** POST /access-requests, GET /patients/{id}/overview | **Tables:** patient_permissions, audit_logs

## BF-004: HMS Sync → Fresh Data

```
Trigger sync (manual or scheduled)
  → POST /hms/sync/patients/{id} → hms_sync_logs (status=pending)
  → Worker: GET HMS snapshot → status=running
  → Update patients table → Sync allergies, meds, labs
  → SUCCESS? → completed + records_synced=N
  → PARTIAL? → partial + records_failed=N
  → FAILURE? → failed + error_message → Dead-letter queue
```
**APIs:** POST /hms/sync/patients/{id}, GET /hms/jobs/{job_id} | **Tables:** patients, hms_sync_logs

## Change Log
| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-06-14 | Agent | 4 critical flows: Chat RAG, Document OCR, Access Request, HMS Sync |
