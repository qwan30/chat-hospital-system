# API Contract Specification

> Project: AI Copilot for Hospital Management System (HMS)  
> Project Code: HOSP-AI-001  
> Version: 3.0  
> Status: Approved  
> Owner: API Lead / Data Lead  
> Last Updated: 2026-06-07  

---

## 1. API Architecture Classification

To ensure clean decoupling, API endpoints are classified into three scopes:
1.  **HMS Source-of-Record APIs**: Transactional endpoints owned by the EMR/HIS core.
2.  **Chatbot BFF APIs**: Read-model and aggregation endpoints called directly by the Next.js UI.
3.  **HMS AI Integration APIs**: Endpoints exposed by HMS specifically for the AI Assistant's sync client.

---

## 2. HMS AI Integration Endpoints (HMS Owned)

### GET `/api/v1/ai/patients/{patientId}/snapshot`
Returns a unified clinical snapshot of the patient.

**Response (200 OK):**
```json
{
  "patient_id": "c3a8f108-9df2-4ce0-a15d-2b4737a4e69b",
  "mrn": "MRN-83921-A",
  "name": "John Doe",
  "dob": "1985-05-12",
  "gender": "Male",
  "allergies": [
    {"allergen": "Penicillin", "reaction": "Anaphylaxis", "severity": "High"}
  ],
  "current_medications": [
    {"drug": "Metformin", "dose": "500mg", "route": "Oral"}
  ],
  "recent_labs": [
    {"test": "HbA1c", "value": "6.8", "unit": "%", "timestamp": "2026-06-01T08:00:00Z"}
  ]
}
```

### GET `/api/v1/ai/patients/{patientId}/permissions`
Verifies clinician treatment scope before RAG retrieval.

**Request Query Parameters:**
- `userId`: UUID of the authenticated clinician.

**Response (200 OK):**
```json
{
  "user_id": "8c29012a-3b4e-4fdf-973c-fb8d9e2a1a8c",
  "patient_id": "c3a8f108-9df2-4ce0-a15d-2b4737a4e69b",
  "has_access": true,
  "scope_type": "treatment_relationship",
  "expires_at": "2026-06-08T00:00:00Z"
}
```

### GET `/api/v1/ai/changes`
Returns incremental clinical record updates for syncing vector caches.

**Request Query Parameters:**
- `since`: ISO timestamp.

**Response (200 OK):**
```json
{
  "last_timestamp": "2026-06-07T12:00:00Z",
  "changes": [
    {"entity_type": "patient", "entity_id": "c3a8f108-9df2-4ce0-a15d-2b4737a4e69b", "action": "UPDATE"},
    {"entity_type": "allergy", "entity_id": "1b08cfa7-c102-4c9f-8dfa-129cd8a1a681", "action": "INSERT"}
  ]
}
```

---

## 3. Chatbot BFF Endpoints (Chatbot Backend Owned)

### GET `/api/v1/dashboard/summary`
Aggregates activity counters and system status summaries for `SCR-003`.

**Response (200 OK):**
```json
{
  "recent_patients": [
    {"id": "uuid", "name": "John Doe", "mrn": "MRN-83921-A", "last_accessed": "2026-06-07T23:00:00Z"}
  ],
  "document_stats": {
    "indexed": 142,
    "processing": 3,
    "failed": 1
  },
  "metrics": {
    "hours_saved": 42.5,
    "cost_saved_usd": 3187.50
  },
  "systems_health": {
    "hms_api": "healthy",
    "ollama_inference": "healthy"
  }
}
```

### GET `/api/v1/patients/{patientId}/overview`
Returns the merged EMR snapshot and AI summary cache (`SCR-007`).

**Response (200 OK):**
```json
{
  "patient_id": "c3a8f108-9df2-4ce0-a15d-2b4737a4e69b",
  "mrn": "MRN-83921-A",
  "name": "John Doe",
  "dob": "1985-05-12",
  "gender": "Male",
  "ai_summary": {
    "text": "Patient has type 2 diabetes. Active allergy to Penicillin.",
    "last_updated": "2026-06-07T20:00:00Z",
    "freshness_status": "synced"
  },
  "emr_snapshot": {
    "allergies_count": 1,
    "medications_count": 1,
    "recent_vitals": {"bp": "120/80", "hr": 72}
  }
}
```

### POST `/api/v1/access-requests`
Submits clinical justifications to override patient scope locks (`SCR-022`).

**Request Body:**
```json
{
  "patient_id": "c3a8f108-9df2-4ce0-a15d-2b4737a4e69b",
  "justification_reason": "Consultation request from ICU attending.",
  "urgency": "high"
}
```

**Response (202 Accepted):**
```json
{
  "request_id": "7a0c8bdf-3b2a-4df9-a78b-fb8a3b8d9c2e",
  "status": "pending_approval",
  "message": "Clinical justification logged. Forwarded to HMS security audit."
}
```

### GET `/api/v1/search/global`
Executes global command palette searches across entities (`SCR-020`).

**Request Query Parameters:**
- `q`: Search query text.

**Response (200 OK):**
```json
{
  "patients": [
    {"id": "uuid", "name": "John Doe", "mrn": "MRN-83921-A"}
  ],
  "documents": [
    {"id": "uuid", "title": "ICU Discharge Summary.pdf", "relevance": 0.89}
  ],
  "threads": [
    {"id": "uuid", "title": "Allergy check discussion"}
  ]
}
```

### POST `/api/v1/documents/{documentId}/retry-ocr`
Retries OCR process on low-confidence or failed files (`SCR-016`).

**Response (200 OK):**
```json
{
  "document_id": "f5a09b3c-b3a1-432d-8b01-bc8d9e2a09c2",
  "status": "ocr_processing",
  "message": "OCR job re-enqueued in worker queue."
}
```

### GET `/api/v1/users/me/preferences`
Retrieves clinician profile UI settings (`SCR-025`).

**Response (200 OK):**
```json
{
  "user_id": "8c29012a-3b4e-4fdf-973c-fb8d9e2a1a8c",
  "theme": "dark",
  "streaming_enabled": true,
  "default_department_workspace": "Cardiology"
}
```

---

## 4. Standard Response Envelope
Errors return standard JSON envelopes as defined in [error-codes.md](error-codes.md).
```json
{
  "error_code": "FORBIDDEN",
  "message": "You do not have active treatment relationship scope for this patient.",
  "trace_id": "fb8a9d2a-a28c-4dfb-973c-2bc8d9e2a09b"
}
```
