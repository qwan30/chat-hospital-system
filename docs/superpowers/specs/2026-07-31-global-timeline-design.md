# Global Timeline Feature Specification

**Date:** 2026-07-31
**Topic:** Global Timeline API and Frontend Integration

## Purpose
Replace the frontend mock data on the `/timeline` page with real data aggregated from the local database, respecting strict patient access permissions (RBAC).

## Architecture

We are adopting **Approach 1: Local-Only Scatter-Gather with RBAC Filtering**. 
The system will aggregate events only from internal subsystems (Chat, Documents, Audit Logs) and exclude the external HMS clinical events to ensure low latency and strict PHI compliance for the MVP.

## 1. Backend Endpoint
- **Route:** `GET /api/v1/timeline`
- **Controller:** Located in a new file `app/backend/src/hospital_ai/api/routes/timeline.py` (or integrated into an existing dashboard/audit route).
- **Query Params:** `limit` (default: 50), `offset` (default: 0).
- **Response Schema:**
```python
class TimelineEventBase(ApiSchema):
    event_id: str
    timestamp: datetime
    type: Literal["chat", "document", "audit"]
    title: str
    body: str
    patient_id: Optional[str]
    metadata: dict[str, Any]

class GlobalTimelineResponse(ApiSchema):
    events: list[TimelineEventBase]
    total_count: int
```

## 2. Business Logic (Scatter-Gather)
1. **Permission Check:** Extract the authenticated user's ID and query the `PermissionService` to retrieve the list of `patient_id`s they are explicitly authorized to view.
2. **Data Fetching (Parallel/Concurrent):**
   - Fetch recent Chat threads/messages linked to authorized `patient_id`s.
   - Fetch recent Document uploads/index events linked to authorized `patient_id`s.
   - Fetch recent Audit logs related to the user or authorized patients.
3. **Aggregation:** Merge the results in memory.
4. **Sorting:** Sort the combined list descending by `timestamp`.
5. **Pagination:** Slice the array by `offset` and `limit`.

## 3. Frontend Integration
- **File:** `app/frontend/src/routes/_app.timeline.index.tsx`
- Remove the hardcoded `events` array.
- Use `@tanstack/react-query` to fetch from `/api/v1/timeline`.
- Map the backend `type` to visual indicators:
  - `chat` -> `icon: Sparkles`, `tone: "ai"`
  - `document` -> `icon: FileText`, `tone: "primary"`
  - `audit` -> `icon: UserCheck`, `tone: "secondary"`
- Render empty state if no events are returned.

## 4. Security & Edge Cases
- **PHI Leakage:** By pre-filtering all queries against the user's allowed `patient_id`s, we guarantee that no document or chat event for a restricted patient leaks into the global feed.
- **Empty State:** If a user has no assigned patients, the timeline will default to showing only system-level audit logs related to their own account.
