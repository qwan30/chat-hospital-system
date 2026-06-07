# UC-007: View Patient Timeline

## Metadata
- **ID:** UC-007
- **Bounded Context:** AI Summary / RAG
- **Related BR:** BR-002
- **Status:** draft
- **Owner:** Product Owner
- **Last updated:** 2026-06-07

## Actor
Doctor, Nurse

## Trigger
User navigates to patient profile dashboard and selects the "Timeline" view.

## Preconditions
- User is authenticated with Doctor or Nurse role
- User has active treatment relationship and authorized scope to view this patient's records
- Patient has chronological encounter, lab, medication, or document history in the system

## Main Flow
1. User selects the "Timeline" tab on the patient dashboard.
2. System calls HMS and Chatbot backend APIs to fetch chronological events.
3. System aggregates events (encounters, lab results, prescriptions, document uploads).
4. System sorts the aggregated list in descending chronological order (most recent first).
5. System displays events in a visual timeline stream showing event type, title, date/time, and a brief description snippet.
6. User can filter the timeline by event type (e.g., show only Lab Results or only Medications).
7. User clicks on a specific event to expand details or open the linked source item.

## Alternative Flows
- **6a. Empty timeline:** Patient has no recorded history → System displays "No timeline events found for this patient" message.
- **7a. Navigating to source document:** Event is a document upload → User clicks "View Source" → System redirects user to the Document Viewer (SCR-019).

## Exceptions
- **E1. HMS API connection timeout:** System fails to retrieve HMS events → System displays warning banner "Unable to load medical records timeline. Showing document upload history only."
- **E2. Permissions revoked mid-session:** User's patient access scope expires or is revoked → System returns HTTP 403 Forbidden and displays permission error message.

## Postconditions
- Chronicled patient timeline is rendered
- Active filters and scroll position are maintained during review

## Acceptance Criteria

### AC-1: Chronological sorting and event rendering
**Given:** Patient P1 has an encounter on 2026-06-05, a lab result on 2026-06-06, and a document uploaded on 2026-06-07  
**When:** Timeline is requested for Patient P1  
**Then:** System renders three events in the timeline  
**And:** The events are ordered: Document Upload (June 7) -> Lab Result (June 6) -> Encounter (June 5)  

### AC-2: Filtering timeline events
**Given:** Patient P1 has 2 Encounters, 3 Lab Results, and 1 Document Upload in their timeline  
**When:** User selects the "Lab Results" filter option  
**Then:** Timeline updates to show exactly 3 events  
**And:** All displayed events have the type "Lab Result"  

## Dependencies
- **Upstream UC:** UC-001 (patient selection)
- **Downstream UC:** UC-005 (view citations/source page if clicking document event)
- **External Systems:** HMS API, pgvector/Document Database

## Notes
Phase 2 timeline expansion — timeline view aggregates chatbot interactions, summary events, and clinical events.

## History
- v1 (2026-06-07, Agent): Created template with 2 ACs
