# UC-005: View Citations / Source Page

## Metadata
- **ID:** UC-005
- **Bounded Context:** AI Chat / Evidence Viewer
- **Related BR:** BR-001
- **Status:** draft
- **Owner:** Product Owner
- **Last updated:** 2026-06-07

## Actor
Doctor, Nurse, Pharmacist (any user who received an AI answer)

## Trigger
User clicks a citation link in an AI answer or summary.

## Preconditions
- User is viewing an AI answer with citations
- User has access to the cited source (same access scope as original query)

## Main Flow
1. User clicks citation link in answer (e.g., "[Source: Discharge Summary p.3]")
2. System resolves citation to document ID + page number (or table/field reference)
3. System retrieves the source page/record
4. System displays source in evidence viewer panel (SCR-019)
5. System highlights the specific chunk that was cited
6. User reviews source for verification

## Alternative Flows
- **2a. Structured data citation:** Source is a database record (e.g., medication table) → Show record view instead of document viewer
- **4a. Multi-page citation:** Citation spans multiple pages → Show page navigation with highlighted chunks
- **5a. Source no longer available:** Document was deleted after answer was generated → Show "Source no longer available" with original citation metadata

## Exceptions
- **E1. Citation metadata corrupted:** Cannot resolve citation → Show error "Unable to load source" with original answer text
- **E2. Permission revoked since answer:** User no longer has access to cited document → Show access denied for this specific source

## Postconditions
- Source document/record is displayed with highlighted citation
- User can verify AI claim against original source
- Audit event created for source access

## Acceptance Criteria

### AC-1: Citation resolves to correct source page
**Given:** AI answer cites "Discharge Summary, page 3, chunk_id=abc123"  
**When:** User clicks the citation  
**Then:** Evidence viewer (SCR-019) opens showing page 3 of the discharge summary  
**And:** The cited text chunk is highlighted  

### AC-2: Structured data citation shows record view
**Given:** AI answer cites "medications table, record_id=42"  
**When:** User clicks the citation  
**Then:** Record view shows the specific medication record with all fields  

### AC-3: Unavailable source handled gracefully
**Given:** Cited document was deleted after answer generation  
**When:** User clicks the citation  
**Then:** UI shows "Source document no longer available"  
**And:** Original citation metadata (document name, page, date) is still displayed  

## Dependencies
- **Upstream UC:** UC-001 (answer with citations), UC-002 (summary with citations)
- **Downstream UC:** None
- **External Systems:** Object storage (original documents)

## History
- v1 (2026-04-27, Original): Basic use case
- v2 (2026-06-07, Agent): Full template with 3 ACs
