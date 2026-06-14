# Glossary

> Project: HOSP-AI-001 — AI Hospital Knowledge Assistant  
> Version: 1.0 · Last Updated: 2026-06-14  

## Business Terms

| Term | Definition |
|------|------------|
| **HMS** | Hospital Management System — the external Spring Boot EMR owning all clinical data, user identities, and access policies |
| **MRN** | Medical Record Number — unique patient identifier within the hospital |
| **PHI** | Protected Health Information — patient data subject to HIPAA privacy rules |
| **HIPAA** | Health Insurance Portability and Accountability Act — US patient data privacy regulation |
| **Clinician** | Any authorized medical professional using the AI copilot (doctor, nurse, pharmacist, lab staff) |
| **Treatment Relationship** | ABAC rule: clinician must have active attending/departmental relationship with patient to access data |
| **Break-Glass Access** | Emergency override for temporary patient access with mandatory justification and audit |
| **Scope** | Permission level: read, summary, medication, upload, admin |

## Technical Terms

| Term | Definition |
|------|------------|
| **BFF** | Backend-for-Frontend — FastAPI single entry point for the Next.js UI |
| **RAG** | Retrieval-Augmented Generation: retrieve chunks → rerank → generate cited answer |
| **LLM** | Large Language Model — Qwen2.5 via Ollama (local) or OpenAI-compatible (cloud) |
| **LLM Manager** | Provider abstraction: runtime switch between Stub / Ollama / OpenAI |
| **Embedding** | 1024-dimension vector representation for semantic similarity via pgvector |
| **pgvector** | PostgreSQL extension for vector storage + HNSW similarity search |
| **RQ** | Redis Queue — Python job queue for async OCR, indexing, HMS sync |
| **HNSW** | Hierarchical Navigable Small World — pgvector ANN indexing algorithm |
| **BM25** | Probabilistic retrieval function used alongside vector search in hybrid mode |
| **Graph RAG** | Entity-relationship-aware retrieval discovering related chunks via knowledge graph traversal |
| **Trace ID** | UUID propagating across all service boundaries for request tracking and audit |
| **Citation** | Reference (evidence_id) linking an AI answer to a specific supporting document chunk |
| **Reranker** | Cross-encoder or score-based component reordering retrieved chunks by relevance |
| **Soft Delete** | `deleted_at` timestamp pattern — used on 9 of 13 tables |
| **Alembic** | SQLAlchemy migration tool — 6 version-controlled schema migrations |
| **SSE** | Server-Sent Events — protocol for streaming chat token-by-token |

## Pipeline Terms

| Term | Definition |
|------|------------|
| **simple_qa** | Default: retrieve → rerank → generate single answer |
| **decompose_qa** | Complex questions: break into sub-questions → retrieve each → synthesize |
| **patient_summary** | Retrieve all patient evidence → generate structured clinical summary |
| **auto** | System auto-selects best pipeline based on question analysis |

## State Values

| Entity | State Machine |
|--------|--------------|
| Document | uploaded → ocr_processing → ocr_failed \| ocr_completed → indexing → index_failed \| indexed → archived |
| AI Query | received → denied \| no_evidence \| completed \| failed |
| HMS Sync | pending → running → completed \| failed \| partial |
| Chat Thread | active ↔ archived (scope: general \| patient-linked) |
| Audit Outcome | allowed \| denied \| failed |

## Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-06-14 | Agent | Created from codebase analysis |
