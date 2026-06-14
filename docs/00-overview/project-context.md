# Project Context

> Project: AI Copilot for Hospital Management System (HMS)  
> Project Code: HOSP-AI-001  
> Version: 1.0  
> Status: Approved  
> Owner: Product Owner  
> Last Updated: 2026-06-14  

---

## 1. Project Metadata

| Field | Value |
|-------|-------|
| Project Name | AI-Powered Hospital Knowledge Assistant |
| Project Code | HOSP-AI-001 |
| Repository | chatbot-hospital-system |
| Type | Web Application (Next.js 16 + FastAPI) |
| Domain | Healthcare — Clinical Decision Support |
| Compliance | HIPAA (audit trail, local PHI processing) |
| Timeline | Sprint 0 → MVP Build → System Test → UAT → Pilot |

---

## 2. Business Background

Hospitals using EMR/HMS systems face significant time penalties when clinicians need to look up patient information across multiple screens, documents, and systems. A typical patient information lookup takes 10–15 minutes of manual EMR navigation. This project builds an AI copilot layer that:

- Accepts natural-language clinical questions from authorized clinicians.
- Retrieves relevant evidence from patient records and indexed documents.
- Generates cited, grounded answers using local LLM inference.
- Enforces permission boundaries so clinicians only see data within their treatment scope.
- Logs every sensitive query for HIPAA-compliant audit trails.

---

## 3. Key Statistics (from codebase analysis, June 2026)

| Metric | Value |
|--------|-------|
| Source files | 332 |
| Code symbols | 3,274 |
| Code relationships | 6,683 edges |
| Execution flows | 216 |
| Backend route modules | 14 |
| Database tables | 13 |
| Alembic migrations | 6 |
| Frontend pages | 14 App Router pages |
| UI components | 30+ shadcn/ui primitives + 60+ feature components |
| LLM providers | 3 (Stub, Ollama, OpenAI-compatible) |
| Embedding providers | 3 (Deterministic, Ollama, OpenAI) |
| Reasoning pipelines | 3 (Simple QA, Decompose QA, Patient Summary) |

---

## 4. Architecture Summary

```
Next.js 16 Frontend (App Router)
        ↓ REST /api/v1
FastAPI BFF (14 route modules)
        ↓
Service Layer (18 modules)
    ├── ChatService (RAG pipeline: retrieve → rerank → generate)
    ├── LLM Manager (Stub | Ollama | OpenAI)
    ├── Embedding Service (deterministic | Ollama | OpenAI)
    ├── PermissionService (ABAC + RBAC)
    ├── RetrievalService (vector + BM25 + hybrid + Graph RAG)
    ├── DrugCheckService (allergy + interaction detection)
    ├── AuditService (immutable audit trail)
    ├── MetricsService (impact tracking)
    └── HMS Connector (sync, appointments, lab results)
        ↓
PostgreSQL + pgvector (single database)
Redis + RQ (background job processing)
```

---

## 5. External Dependencies

| System | Role | Protocol |
|--------|------|----------|
| HMS (Hospital Management System) | Source of truth for clinical data, auth, permissions | REST API (Spring Boot) |
| Ollama | Local LLM inference (Qwen2.5 3B/7B) | REST API |
| OpenAI (optional) | Cloud LLM fallback (non-PHI queries only) | REST API |
| Redis | Job queue backend for RQ workers | Redis protocol |

---

## Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-06-14 | Agent | Created from codebase analysis |
