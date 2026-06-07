# UC-004: Search Documents Semantically

## Metadata
- **ID:** UC-004
- **Bounded Context:** Document Management / Search
- **Related BR:** BR-003
- **Status:** draft
- **Owner:** Product Owner
- **Last updated:** 2026-06-07

## Actor
Doctor, Nurse, Records Staff (any authorized user)

## Trigger
User enters a search query in the document search interface or global command palette.

## Preconditions
- User is authenticated
- At least one document is indexed with status `Indexed`

## Main Flow
1. User opens document dashboard (SCR-015) or global command palette (SCR-020)
2. User types semantic search query
3. System generates embedding from user query
4. System queries pgvector for matching document chunks (filtered by user access scope)
5. System ranks results by relevance
6. System returns results with: document title, chunk text, page number, relevance score
7. User views results and optionally clicks to open source document (→ UC-005)

## Alternative Flows
- **2a. Empty query:** User submits blank search → System shows recent/popular documents instead
- **4a. No matching results:** No chunks exceed relevance threshold → System shows "No results found" with suggestions
- **5a. Cross-type search:** Results span multiple entity types (patients, documents, threads) → Group by type in command palette

## Exceptions
- **E1. Embedding service unavailable:** Cannot generate query embedding → Show error "Search temporarily unavailable"
- **E2. Permission filters eliminate all results:** Results exist but user has no access → Show "No accessible results" (different from "No results")

## Postconditions
- Search results displayed with relevance scores and source references
- Metric event created for search latency and result count

## Acceptance Criteria

### AC-1: Relevant document chunks returned
**Given:** 3 indexed documents about allergies exist  
**When:** User searches "penicillin allergy"  
**Then:** Results include chunks from allergy-related documents ranked by relevance  
**And:** Each result shows document title, page number, and snippet  

### AC-2: Search latency within target
**Given:** MVP dataset is indexed  
**When:** User executes any search query  
**Then:** Results are returned within P95 < 5 seconds  

### AC-3: Permission-scoped results
**Given:** Documents D1 (accessible) and D2 (restricted) both match the query  
**When:** User without D2 access searches  
**Then:** Only D1 appears in results  
**And:** D2 is not revealed in any form  

## Dependencies
- **Upstream UC:** UC-003 (documents must be indexed first)
- **Downstream UC:** UC-005 (view source from result)
- **External Systems:** pgvector (vector search)

## History
- v1 (2026-04-27, Original): Basic use case
- v2 (2026-06-07, Agent): Full template with 3 ACs
