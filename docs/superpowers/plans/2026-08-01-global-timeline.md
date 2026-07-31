# Global Timeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a global timeline API endpoint (`GET /api/v1/timeline`) that aggregates Chat, Document, and Audit events filtered by RBAC, and integrate it with the frontend timeline page.

**Architecture:** A local scatter-gather approach using a new backend endpoint. It checks the user's `PatientPermission`s, queries `ChatThread`, `Document`, and `AuditLog` concurrently, sorts them in memory by timestamp, and returns a unified paginated feed to be displayed on the React frontend via `@tanstack/react-query`.

**Tech Stack:** FastAPI, SQLAlchemy (async), React, TanStack Query, Tailwind CSS, Lucide Icons.

## Global Constraints
- Must not fetch data from external HMS for the global view to ensure <30s latency.
- Strict PHI compliance: only return events linked to `patient_id`s the user has explicit `PatientPermission` to view (or global audit logs for the user themselves).
- Frontend design constraints apply (shadcn/ui + Tailwind).

---

### Task 1: Define Backend Schemas

**Files:**
- Create: `app/backend/src/hospital_ai/schemas/timeline.py`

**Interfaces:**
- Produces: `TimelineEventBase`, `GlobalTimelineResponse` models.

- [ ] **Step 1: Write the schema file**
```python
# app/backend/src/hospital_ai/schemas/timeline.py
from datetime import datetime
from typing import Literal, Optional, Any
from pydantic import BaseModel
from .base import ApiSchema

class TimelineEventBase(ApiSchema):
    event_id: str
    timestamp: datetime
    type: Literal["chat", "document", "audit"]
    title: str
    body: str
    patient_id: Optional[str] = None
    metadata: dict[str, Any] = {}

class GlobalTimelineResponse(ApiSchema):
    events: list[TimelineEventBase]
    total_count: int
```

- [ ] **Step 2: Commit**
```bash
git add app/backend/src/hospital_ai/schemas/timeline.py
git commit -m "feat: define timeline schemas"
```

---

### Task 2: Implement Backend API Route (`/api/v1/timeline`)

**Files:**
- Create: `app/backend/src/hospital_ai/api/routes/timeline.py`
- Modify: `app/backend/src/hospital_ai/main.py` (to register router)

**Interfaces:**
- Consumes: `GlobalTimelineResponse`, `TimelineEventBase` from Task 1. `PatientPermission`, `ChatThread`, `Document`, `AuditLog` from DB models.

- [ ] **Step 1: Create the router and logic**
```python
# app/backend/src/hospital_ai/api/routes/timeline.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import asyncio

from hospital_ai.db.session import get_db
from hospital_ai.api.dependencies import get_current_user
from hospital_ai.db.models import User, PatientPermission, ChatThread, Document, AuditLog
from hospital_ai.schemas.timeline import GlobalTimelineResponse, TimelineEventBase

router = APIRouter(prefix="/timeline", tags=["Timeline"])

@router.get("", response_model=GlobalTimelineResponse)
async def get_global_timeline(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Get permitted patient IDs
    perm_stmt = select(PatientPermission.patient_id).where(PatientPermission.user_id == current_user.id)
    perm_result = await db.execute(perm_stmt)
    allowed_patients = [row[0] for row in perm_result.all()]

    if not allowed_patients:
        # User has no assigned patients, return empty or just personal audit logs
        return GlobalTimelineResponse(events=[], total_count=0)

    # 2. Scatter gather
    chat_stmt = select(ChatThread).where(ChatThread.patient_id.in_(allowed_patients)).order_by(desc(ChatThread.created_at)).limit(limit)
    doc_stmt = select(Document).where(Document.patient_id.in_(allowed_patients)).order_by(desc(Document.created_at)).limit(limit)
    audit_stmt = select(AuditLog).where(AuditLog.user_id == current_user.id).order_by(desc(AuditLog.created_at)).limit(limit)

    chat_res, doc_res, audit_res = await asyncio.gather(
        db.execute(chat_stmt),
        db.execute(doc_stmt),
        db.execute(audit_stmt)
    )

    events = []
    for chat in chat_res.scalars().all():
        events.append(TimelineEventBase(
            event_id=f"chat-{chat.id}",
            timestamp=chat.created_at,
            type="chat",
            title="AI consult started",
            body=chat.title or "New consultation",
            patient_id=chat.patient_id,
            metadata={}
        ))
        
    for doc in doc_res.scalars().all():
        events.append(TimelineEventBase(
            event_id=f"doc-{doc.id}",
            timestamp=doc.created_at,
            type="document",
            title="Document uploaded",
            body=f"{doc.filename} added to patient record",
            patient_id=doc.patient_id,
            metadata={}
        ))
        
    for audit in audit_res.scalars().all():
        events.append(TimelineEventBase(
            event_id=f"audit-{audit.id}",
            timestamp=audit.created_at,
            type="audit",
            title=audit.action,
            body=audit.details.get("reason", "Action logged"),
            patient_id=None,
            metadata={}
        ))

    # 3. Sort and paginate
    events.sort(key=lambda x: x.timestamp, reverse=True)
    paginated_events = events[offset:offset+limit]

    return GlobalTimelineResponse(events=paginated_events, total_count=len(events))
```

- [ ] **Step 2: Register router in `main.py`**
Modify `app/backend/src/hospital_ai/main.py` to include the new timeline router under `api/v1`.

- [ ] **Step 3: Test backend**
Run `curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/timeline` (or rely on frontend testing).

- [ ] **Step 4: Commit**
```bash
git add app/backend/src/hospital_ai/api/routes/timeline.py app/backend/src/hospital_ai/main.py
git commit -m "feat: implement global timeline endpoint"
```

---

### Task 3: Integrate API in Frontend

**Files:**
- Modify: `app/frontend/src/routes/_app.timeline.index.tsx`
- Modify: `app/frontend/src/lib/api/timeline.ts` (Create)

**Interfaces:**
- Consumes: `GET /api/v1/timeline` API.

- [ ] **Step 1: Create API helper**
```typescript
// app/frontend/src/lib/api/timeline.ts
import { fetchApi } from "./index";

export interface TimelineEvent {
  event_id: string;
  timestamp: string;
  type: "chat" | "document" | "audit";
  title: string;
  body: string;
  patient_id?: string;
  metadata: Record<string, any>;
}

export interface TimelineResponse {
  events: TimelineEvent[];
  total_count: number;
}

export async function getGlobalTimeline(limit = 50, offset = 0): Promise<TimelineResponse> {
  return fetchApi(`/api/v1/timeline?limit=${limit}&offset=${offset}`);
}
```

- [ ] **Step 2: Update the React component**
```tsx
// In app/frontend/src/routes/_app.timeline.index.tsx
import { useQuery } from "@tanstack/react-query";
import { getGlobalTimeline } from "@/lib/api/timeline";
import { format } from "date-fns";

// Inside TimelinePage component:
const { data, isLoading } = useQuery({
  queryKey: ["global-timeline"],
  queryFn: () => getGlobalTimeline()
});

// Update rendering logic:
// Replace the hardcoded `events` array with `data?.events`.
// Map types to icons/tones dynamically:
// chat -> Sparkles (ai)
// document -> FileText (primary)
// audit -> UserCheck (secondary)
```
Ensure the UI matches the required empty states and gracefully handles loading.

- [ ] **Step 3: Commit**
```bash
git add app/frontend/src/routes/_app.timeline.index.tsx app/frontend/src/lib/api/timeline.ts
git commit -m "feat: integrate global timeline API into frontend"
```
