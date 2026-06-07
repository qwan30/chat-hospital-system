# UC-008: Review Audit Logs

## Metadata
- **ID:** UC-008
- **Bounded Context:** Access Control / Audit
- **Related BR:** BR-004, BR-005
- **Status:** draft
- **Owner:** Product Owner
- **Last updated:** 2026-06-07

## Actor
Security Auditor, System Administrator

## Trigger
Actor navigates to the Audit Event Logs screen (SCR-023).

## Preconditions
- User is authenticated
- User is assigned the "Security" or "Administrator" role in the system

## Main Flow
1. User navigates to the Audit Event Logs screen (SCR-023).
2. System calls the `GET /audit/events` API with default filters (last 24 hours).
3. System retrieves and displays a chronological list of audit events.
4. For each audit event, system displays: Timestamp, Actor, Action (e.g., LOGIN, CHAT_QUERY, DOC_UPLOAD, PERMISSION_CHECK), Target Resource (e.g., Patient ID, Document ID), Outcome (SUCCESS, BLOCKED), and Client IP.
5. User filters the logs by date range, actor, action, or outcome status.
6. User clicks on an audit event to view the full JSON payload details (including Trace ID, request metadata, and justification notes if applicable).

## Alternative Flows
- **5a. View Blocked Attempts Only:** User filters outcome by "BLOCKED" → System displays only denied access and security policy violation events.
- **6a. Export Logs:** User clicks "Export CSV" → System compiles filtered log records and downloads them to the user's local machine.

## Exceptions
- **E1. Unauthorized role access:** An authenticated user without "Security" or "Administrator" role attempts to access the audit logs → System blocks access, returns HTTP 403 Forbidden, and creates a critical audit log event tracking the unauthorized access attempt.
- **E2. Audit database connection failure:** System cannot connect to the audit datastore → System displays error message "Audit log service is temporarily offline."

## Postconditions
- Chronological or filtered audit events are displayed
- Access violation metrics are updated on the backend dashboard

## Acceptance Criteria

### AC-1: Security auditor access authorization
**Given:** An authenticated user with the role "Security"  
**When:** The user navigates to the Audit Event Logs screen (SCR-023)  
**Then:** System displays the audit event log list with all records  
**And:** API request returns HTTP 200 OK  

### AC-2: Standard user access restriction
**Given:** An authenticated user with the role "Doctor" (not "Security" or "Administrator")  
**When:** The user attempts to request audit events from `GET /audit/events`  
**Then:** System returns HTTP 403 Forbidden  
**And:** System writes a new audit record: Action = "UNAUTHORIZED_ACCESS_ATTEMPT", Resource = "Audit Logs", Outcome = "BLOCKED"  

### AC-3: Filtering by blocked attempts
**Given:** Audit database contains 100 entries, including 95 SUCCESS events and 5 BLOCKED events  
**When:** User filters the audit logs screen by Outcome = "BLOCKED"  
**Then:** The screen displays exactly 5 records  
**And:** Every displayed record shows the outcome label "BLOCKED"  

## Dependencies
- **Upstream UC:** None
- **Downstream UC:** None
- **External Systems:** PostgreSQL Audit Log Database

## Notes
Must comply with hospital privacy standards — patient medical record content is never written into the audit log payload (only metadata like patient IDs are tracked).

## History
- v1 (2026-06-07, Agent): Created template with 3 ACs
