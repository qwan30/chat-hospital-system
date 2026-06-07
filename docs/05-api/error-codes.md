# Standardized API Error Codes

> Project: AI-Powered Hospital Knowledge Assistant  
> Project Code: HOSP-AI-001  
> Version: 2.0  
> Status: Draft  
> Owner: API Lead / QA Lead  
> Last Updated: 2026-06-07  

---

## 1. Error Response Format

All API errors return a standard JSON envelope:

```json
{
  "error_code": "STRING_IDENTIFIER",
  "message": "Human readable description of the error context.",
  "trace_id": "uuid-for-tracking"
}
```

---

## 2. Error Catalog

The system defines the following domain-specific error codes:

| HTTP Status | Error Code | Message Pattern | Description / Triggering Event |
|---|---|---|---|
| **400 Bad Request** | `VALIDATION_ERROR` | "Invalid request payload format." | Request JSON fails field structure validation (Pydantic failure). |
| **400 Bad Request** | `PATIENT_ID_MISMATCH` | "Patient ID does not match records." | Document upload patient ID does not correspond to an existing record. |
| **401 Unauthorized** | `AUTHENTICATION_REQUIRED` | "Missing or invalid authentication token." | No bearer token provided or token signature is expired. |
| **403 Forbidden** | `FORBIDDEN` | "You do not have access scope to this resource." | User authenticated, but RBAC or ABAC scoping rules block access. |
| **403 Forbidden** | `UNAUTHORIZED_DEPT_ACCESS` | "Clinician is not active in this patient's department." | ABAC department check fails for requested patient data. |
| **404 Not Found** | `PATIENT_NOT_FOUND` | "Patient record with ID {uuid} was not found." | Query or summary requested for non-existent patient. |
| **404 Not Found** | `DOCUMENT_NOT_FOUND` | "Document with ID {uuid} not found." | Document view requested for non-existent document. |
| **409 Conflict** | `DUPLICATE_MRN` | "MRN already exists in the database." | Attempting to create or sync a patient with an existing MRN. |
| **422 Unprocessable** | `INSUFFICIENT_EVIDENCE` | "AI context retrieved contains insufficient facts to generate a reliable answer." | The semantic search did not find enough evidence to answer, triggering a safe refusal. |
| **422 Unprocessable** | `OCR_PROCESSING_FAILED` | "Document OCR failed due to layout parse error." | PaddleOCR failed to process the uploaded file. |
| **429 Too Many Requests**| `RATE_LIMIT_EXCEEDED` | "Too many queries submitted. Please wait." | API request limit reached for this session. |
| **500 Internal Error** | `INTERNAL_SERVER_ERROR` | "An unexpected error occurred. Reference trace: {uuid}." | Uncaught database, queue, or network failure. |
| **503 Service Unavailable**| `LLM_OFFLINE` | "Local Ollama LLM service is offline." | Chatbot BFF cannot connect to local Ollama inference API. |

---

## Change Log
| Version | Date | Author | Change |
|---|---|---|---|
| 2.0 | 2026-06-07 | Agent | Created standardized error catalog from API example snippets |
