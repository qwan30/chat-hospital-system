# UC-003: Upload and OCR Document

## Metadata
- **ID:** UC-003
- **Bounded Context:** Document Management / OCR
- **Related BR:** BR-003
- **Status:** draft
- **Owner:** Product Owner
- **Last updated:** 2026-06-07

## Actor
Records Staff, Admin

## Trigger
User uploads a PDF or image file via the document upload interface.

## Preconditions
- User is authenticated with Records Staff or Admin role
- File is PDF, PNG, or JPG format
- File size within limits (TBD)

## Main Flow
1. User opens document upload modal (SCR-017)
2. User selects one or more files
3. System validates file format and size
4. System stores original file in object storage
5. System creates document record with status `Uploaded`
6. System enqueues OCR job in Redis queue
7. Worker picks up job and updates status to `OCR Processing`
8. Worker runs PaddleOCR on document pages
9. Worker saves OCR text per page to `document_pages` with confidence scores
10. Worker chunks text and generates embeddings
11. Worker saves chunks to `document_chunks` with vectors
12. System updates status to `Indexed`
13. System notifies user of completion via UI

## Alternative Flows
- **2a. Batch upload:** User selects multiple files → Each file processed independently with individual status tracking
- **8a. Low OCR confidence:** Confidence score < threshold → Status set to `Needs Review` instead of proceeding to chunking (SCR-016)
- **12a. Partial indexing:** Some pages fail OCR but others succeed → Status set to `Partially Indexed` with failed pages flagged

## Exceptions
- **E1. Invalid file format:** System returns 400 + rejects upload
- **E2. OCR failure:** OCR engine crashes → Status set to `OCR Failed` + job marked for retry
- **E3. Embedding failure:** Embedding model unavailable → Status set to `Index Failed` + retry
- **E4. Storage full:** Cannot store original → 500 error + alert admin
- **E5. Duplicate document:** File hash matches existing document → Warn user, allow override or skip

## Postconditions
- Document record exists with final status (Indexed / Needs Review / Failed)
- Original file is preserved in object storage
- OCR text is stored per page with confidence scores
- Chunks with embeddings are stored in pgvector
- Document is discoverable via semantic search (if Indexed)

## Acceptance Criteria

### AC-1: Uploaded document becomes searchable
**Given:** Records staff uploads a clean PDF document  
**When:** OCR and indexing complete  
**Then:** Document status is `Indexed`  
**And:** Document chunks appear in semantic search results for relevant queries  

### AC-2: Document state transitions tracked
**Given:** Records staff uploads a document  
**When:** Processing progresses  
**Then:** Status transitions follow: Uploaded → OCR Processing → Indexed  
**And:** Each transition timestamp is recorded  

### AC-3: Failed OCR creates retry-able state
**Given:** OCR engine encounters a corrupt page  
**When:** OCR processing fails  
**Then:** Document status is set to `OCR Failed`  
**And:** User can trigger retry from the UI  

### AC-4: Low confidence OCR triggers review
**Given:** OCR confidence score < 0.7 (TBD threshold)  
**When:** OCR processing completes  
**Then:** Document status is set to `Needs Review` (SCR-016)  
**And:** Review interface shows original image alongside OCR text  

## Dependencies
- **Upstream UC:** None
- **Downstream UC:** UC-004 (search), UC-005 (view source)
- **External Systems:** PaddleOCR, Redis queue, object storage

## History
- v1 (2026-04-27, Original): Basic use case
- v2 (2026-06-07, Agent): Full template with 4 ACs, state machine alignment
