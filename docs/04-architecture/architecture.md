# System Architecture & Software Design Document

> Project: AI Copilot for Hospital Management System (HMS)  
> Project Code: HOSP-AI-001  
> Version: 3.0  
> Status: Approved  
> Owner: System Architect / Tech Lead  
> Last Updated: 2026-06-07  

---

## 1. Architecture Goals and Constraints
*   **System of Record Separation**: The HMS owns all transactional hospital clinical data. The AI assistant functions as a read-model caching layer and RAG vector store.
*   **Next.js UI BFF Aggregator**: The Next.js web application interacts exclusively with the AI Assistant Backend (BFF), which consolidates endpoints and proxies EMR data checks to the HMS API.
*   **Local-first Privacy**: No patient Protected Health Information (PHI) is processed by external cloud LLMs. Local quantized models (Qwen2.5 3B/7B via Ollama) are used.
*   **HNSW Vector Indexing**: Document chunks, metadata, and embeddings are managed locally in PostgreSQL using the `pgvector` extension.

---

## 2. System Context

The multi-layer integration architecture operates as follows:

```mermaid
flowchart TD
    UI[Next.js Web UI] -->|BFF APIs| BFF[AI Assistant FastAPI Backend]
    BFF -->|Read-only caches & RAG| PG[(AI PostgreSQL + pgvector)]
    BFF -->|Inference Queries| LLM[Local Ollama / vLLM Engine]
    BFF -->|Enqueue OCR task| Redis[(Redis Task Queue)]
    Redis -->|Process job| Worker[Celery Ingestion Worker]
    Worker -->|OCR extraction| OCR[PaddleOCR Engine]
    Worker -->|Write chunk embeddings| PG
    BFF -->|Integration client queries| HMS[HMS Spring Boot API]
```

---

## 3. Component Architecture

| Component Layer | Responsibility | Primary Datastore |
|---|---|---|
| **Next.js Web UI** | Interacts with Chat, Patient snapshots, Document OCR dashboards, and Metrics views. | Browser state |
| **FastAPI Backend (BFF)** | Direct entry point for UI. Handles request validation, routes queries, checks policies, and performs auth bridge mappings. | PostgreSQL |
| **HMS Spring Boot API** | External system of record owning clinical patient records, logins, appointments, and access requests. | HMS Production DB |
| **Celery Indexing Worker** | Processes uploaded documents, page OCR blocks, and generates vector chunks. | Local filesystem / S3 |
| **Ollama Inference Engine** | Local quantized Large Language Model execution. | Model directory |
| **pgvector Database** | Stores user chat threads, de-identified metrics, audit logs, and document chunk vectors. | PostgreSQL |

---

## 4. Key Sequences

### Request Patient Overview & Context
This sequence outlines permission check routing before HMS EMR snapshots are cached and displayed to clinicians:

```mermaid
sequenceDiagram
    actor Doctor
    participant UI as Next.js Web UI
    participant BFF as FastAPI BFF
    participant HMS as HMS Spring Boot API
    participant PG as pgvector Database

    Doctor->>UI: Select patient P1
    UI->>BFF: GET /api/v1/patients/P1/overview
    BFF->>HMS: GET /api/v1/ai/patients/P1/permissions?userId=D1
    alt Access Approved
        HMS-->>BFF: Authorized (Temporary scope active)
        BFF->>HMS: GET /api/v1/ai/patients/P1/snapshot
        HMS-->>BFF: Return demographics, medications, labs snapshot
        BFF->>PG: Retrieve cached documents & AI summary
        PG-->>BFF: Return PDF chunks and latest summary
        BFF-->>UI: Return merged EMR snapshot + AI summary + citations
        UI-->>Doctor: Render Patient Details screen (SCR-007)
    else Access Denied
        HMS-->>BFF: Unauthorized (Access Blocked)
        BFF->>PG: Log blocked event in audit_events table
        BFF-->>UI: Return HTTP 403 (SCR-021)
        UI-->>Doctor: Display Access Denied (No relationship)
    end
```

---

## 5. Quality Attribute Design

*   **Security & Privacy**: Enforces active patient permission predicates at the HMS API gateway layer before any RAG search vector retrieval runs.
*   **Performance**: Minimizes HMS network request count by utilizing composite snapshot endpoints (`/ai/patients/{id}/snapshot`) instead of querying vitals, labs, and logs in separate requests.
*   **Resource Management**: Restricts local worker threads and limits concurrent Ollama batch sizes to fit standard hospital workstation 16GB RAM limits.

---

## Change Log
| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-04-27 | System Architect | Initial architecture draft |
| 2.0 | 2026-06-07 | Agent | Restructured into standalone doc |
| 3.0 | 2026-06-07 | Agent | Updated system context to position HMS as the external system of record and added BFF sequence |
