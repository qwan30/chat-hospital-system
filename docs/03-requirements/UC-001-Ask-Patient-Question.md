# UC-001: Ask Patient Question

## Metadata
- **ID:** UC-001
- **Bounded Context:** AI Chat / RAG
- **Related BR:** BR-001, BR-004
- **Status:** draft
- **Owner:** Product Owner
- **Last updated:** 2026-06-07

## Actor
Doctor, Nurse (any staff with patient access scope)

## Trigger
User selects a patient context and submits a natural language question about that patient.

## Preconditions
- User is authenticated (FR-001)
- User has active session with valid role
- Patient exists in the system (via HMS)

## Main Flow
1. User opens chat workspace (SCR-013 or SCR-011)
2. User selects patient context via patient context gate
3. System verifies user has treatment relationship with selected patient (RBAC/ABAC)
4. User types question in prompt composer
5. System classifies task type (question_answer)
6. System retrieves authorized evidence: structured data (PostgreSQL), vector chunks (pgvector), graph relations (if available)
7. System applies permission filter — removes any unauthorized context
8. System reranks and compresses evidence
9. System generates answer via LLM with citation metadata preserved
10. System streams answer to UI with citations, confidence, and disclaimer
11. System creates audit event and metric event
12. User views answer and optionally inspects cited sources

## Alternative Flows
- **3a. General mode (no patient context):** User asks general hospital knowledge question. Skip steps 2–3, retrieve only non-PHI knowledge base content.
- **6a. No structured data available:** System relies on vector chunks only. Answer may have fewer citations.
- **9a. Streaming response:** Answer chunks are delivered incrementally. UI shows typing indicator.

## Exceptions
- **E1. Permission denied (403):** User has no treatment relationship with patient → System returns 403 + shows access denied screen (SCR-021) + creates audit event for denied access.
- **E2. Insufficient evidence (422):** RAG retrieval returns no relevant evidence → System returns safe refusal with explanation (SCR-012) + creates audit event.
- **E3. LLM timeout:** LLM does not respond within 30 sec → System returns timeout error + suggests retry.
- **E4. Patient not found (404):** Patient ID does not exist → System returns 404.
- **E5. Low OCR confidence in source:** Retrieved evidence includes low-confidence OCR text → System includes confidence warning in citation metadata.

## Postconditions
- Answer is displayed with citations (or safe refusal is shown)
- Audit event is created with: actor, action, patient_id, trace_id
- Metric event is created with: latency, documents_retrieved, citations_count

## Acceptance Criteria

### AC-1: Cited answer returned for valid question
**Given:** Doctor is authenticated and has access to patient P1  
**When:** Doctor asks "What allergies does P1 have?"  
**Then:** Answer includes ≥1 citation with source_type, document_id/table, page/field reference  
**And:** Response contains `confidence` field and `disclaimer` text  

### AC-2: Permission denied for unauthorized patient
**Given:** Nurse is authenticated but has NO treatment relationship with patient P2  
**When:** Nurse selects P2 and asks any question  
**Then:** System returns HTTP 403 with error code `FORBIDDEN`  
**And:** Access denied screen (SCR-021) is displayed  
**And:** Audit event is created with action `access_denied`  

### AC-3: Safe refusal when no evidence exists
**Given:** Doctor is authenticated and has access to patient P3  
**When:** Doctor asks a question with no matching evidence in the knowledge base  
**Then:** System returns HTTP 422 with error code `INSUFFICIENT_EVIDENCE`  
**And:** Safe refusal message is displayed (SCR-012)  
**And:** Audit event is created with action `safe_refusal`  

### AC-4: Response latency within target
**Given:** MVP dataset is loaded (synthetic data)  
**When:** Any patient question is submitted  
**Then:** Response is returned within 30 seconds  

### AC-5: Audit trail created for every query
**Given:** Any user submits a patient question (allowed or denied)  
**When:** Question processing completes (success, refusal, or denial)  
**Then:** Exactly one `audit_event` is created with `trace_id`, `actor`, `action`, `patient_id`, `timestamp`  

## Dependencies
- **Upstream UC:** None (this is the primary use case)
- **Downstream UC:** UC-005 (view citations after answer)
- **External Systems:** HMS REST API (patient data), Ollama/vLLM (LLM inference)

## Notes
- The current `HmsApiClient` in the chatbot attempts fragmented endpoint calls. Recommendation: use the unified `GET /api/v1/patient-records/{patientId}` from HMS instead.
- General mode (no patient context) is supported but may have limited evidence.

## History
- v1 (2026-04-27, Original): Basic use case in flat file
- v2 (2026-06-07, Agent): Full UC-TEMPLATE with 5 acceptance criteria, exceptions, flows
