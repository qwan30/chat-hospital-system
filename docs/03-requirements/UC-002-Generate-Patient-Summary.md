# UC-002: Generate Patient Summary

## Metadata
- **ID:** UC-002
- **Bounded Context:** AI Summary / RAG
- **Related BR:** BR-002
- **Status:** draft
- **Owner:** Product Owner
- **Last updated:** 2026-06-07

## Actor
Doctor (primary), Nurse (limited sections)

## Trigger
User opens patient overview and clicks "Generate Summary" or navigates to summary tab.

## Preconditions
- User is authenticated with Doctor or Nurse role
- User has treatment relationship with the patient
- Patient exists in HMS with at least partial data

## Main Flow
1. User navigates to patient overview (SCR-007)
2. User clicks "Generate Summary"
3. System verifies patient access permission
4. System retrieves patient data from HMS: history, encounters, diagnoses, medications, allergies, labs
5. System retrieves relevant document chunks from vector store
6. System generates structured summary via LLM with citations
7. System streams summary to UI with section headers and citation links (SCR-010)
8. System creates metric event with generation latency
9. User reviews summary and optionally inspects cited sources

## Alternative Flows
- **4a. Partial HMS data:** Some data categories are empty (e.g., no lab results) → Summary notes missing sections with "No data available"
- **5a. No document chunks:** Summary relies on structured data only → Fewer citations
- **7a. Summary refresh:** User clicks "Refresh" → System regenerates with latest data

## Exceptions
- **E1. Permission denied:** User lacks patient access → 403 + redirect to access denied
- **E2. LLM timeout:** Generation exceeds 30 sec → Show timeout error + partial result if available
- **E3. HMS unavailable:** Cannot retrieve patient data → Show error + suggest retry
- **E4. Empty patient record:** Patient exists but has no clinical data → Summary says "Insufficient data to generate summary"

## Postconditions
- Summary is displayed with section headers: history, medications, allergies, labs, documents
- Each section includes citations to source records
- Metric event records generation latency and citation count

## Acceptance Criteria

### AC-1: Summary includes required sections
**Given:** Doctor has access to patient P1 with full clinical data  
**When:** Doctor clicks "Generate Summary"  
**Then:** Summary includes sections: history, medications, allergies, labs  
**And:** Each section cites its data source (table/document/page)  

### AC-2: Summary generation under latency target
**Given:** MVP dataset is loaded  
**When:** Summary is generated for any patient  
**Then:** Complete summary is displayed within 30 seconds  

### AC-3: Streaming progress visible
**Given:** Doctor clicks "Generate Summary"  
**When:** Summary is being generated  
**Then:** UI shows streaming progress (SCR-010) with citation retrieval status  
**And:** User can see partial content before generation completes  

### AC-4: Missing data sections handled gracefully
**Given:** Patient P4 has medications but no lab results  
**When:** Summary is generated  
**Then:** Labs section shows "No lab results available" instead of omitting the section  
**And:** Summary is still generated with available data  

## Dependencies
- **Upstream UC:** UC-001 (patient context selection reused)
- **Downstream UC:** UC-005 (view citations from summary)
- **External Systems:** HMS REST API, Ollama/vLLM

## History
- v1 (2026-04-27, Original): Basic use case
- v2 (2026-06-07, Agent): Full template with 4 ACs
