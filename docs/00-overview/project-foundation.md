# Project Foundation

> Project: AI-Powered Hospital Knowledge Assistant  
> Project Code: HOSP-AI-001  
> Version: 2.0  
> Owner: Tech Lead / System Architect  
> Last updated: 2026-06-07  
> Status: In Review

This document is the **single source of truth** for all technical standards, conventions, and architectural decisions. Other documents reference this rather than duplicating its content.

---

## 1. Tech Stack

| Layer | Technology | Version / Notes |
|---|---|---|
| **Backend API** | FastAPI (Python) | Async, OpenAPI auto-generation |
| **Database** | PostgreSQL + pgvector | Structured data + vector search |
| **Cache / Queue** | Redis | Task queue, session cache |
| **OCR** | PaddleOCR / PP-OCR | CPU-mode for MVP (16GB RAM) |
| **Embedding** | Sentence-transformers | Local embedding model |
| **LLM** | Ollama (Qwen2.5 3B/7B quantized) | Local-first for PHI privacy |
| **Graph** | SQL graph (MVP) / Neo4j (Phase 2) | Relationship traversal |
| **Frontend** | Next.js (TypeScript, React) | App Router, server components |
| **Observability** | OpenTelemetry → Prometheus/Grafana/Loki | Metrics, traces, logs |
| **HMS Integration** | Spring Boot REST API (Java) | Source of truth for clinical data |

## 2. Architecture Principles

| Principle | Description | Enforcement |
|---|---|---|
| **Local-first privacy** | No external LLM for PHI by default | Architecture review, deployment config |
| **Permission before retrieval** | RBAC/ABAC filters applied before any context reaches LLM | Code review, integration tests, TC-002/TC-016 |
| **Source traceability** | Every AI answer must cite its evidence source | RAG pipeline design, TC-004 |
| **Modularity** | Separate OCR, RAG, graph, API, UI concerns | Module boundaries, dependency rules |
| **Measurable impact** | Track time/cost saved per workflow | Metric events, MET-001 through MET-013 |
| **Fail-safe AI** | Refuse when evidence is insufficient | Safe refusal pattern, TC-005 |

## 3. Architecture Dependency Rules

```
Frontend → Chatbot BFF API (only)
Chatbot BFF → HMS REST API (for clinical data)
Chatbot BFF → PostgreSQL + pgvector (for AI/RAG data)
Chatbot BFF → Redis (for queue/cache)
Chatbot BFF → Ollama/vLLM (for LLM inference)
Workers → Redis queue → PostgreSQL (for OCR/embedding jobs)
HMS API → HMS Database (MySQL) — not directly accessed by chatbot
```

**Rules**:
- Frontend must never call HMS API directly — always through Chatbot BFF
- Chatbot must never write to HMS database — HMS is read-only source of truth
- Workers must be idempotent — retry-safe for OCR and embedding jobs
- All cross-service calls must include trace ID

## 4. Coding Standards

### Python (Backend)
- **Style**: PEP 8, enforced by `ruff` + `black`
- **Type hints**: Required for all public functions
- **Async**: Use `async/await` for I/O-bound operations
- **Error handling**: Use domain exceptions, never catch bare `Exception`
- **File size limit**: Max 400 lines per module
- **Method length**: Max 50 lines
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes

### TypeScript (Frontend)
- **Style**: ESLint + Prettier
- **Components**: React function components, `PascalCase` filenames
- **State**: Minimal client state, server components where possible
- **Variables**: `camelCase` locals, `PascalCase` components

### General
- **Immutability**: Prefer immutable data structures
- **SOLID**: Apply at module boundaries
- **No hardcoded secrets**: Use environment variables, validate at startup
- **Logging**: Structured JSON logs with trace_id

## 5. Security Posture

| Control | Implementation | Verification |
|---|---|---|
| Authentication | Local auth / OIDC | TC-001 |
| Authorization | RBAC + ABAC + patient scope | TC-002, TC-003, TC-016 |
| Retrieval safety | Permission filters before vector/graph retrieval | TC-016 (0 leakage) |
| Data protection | TLS in transit, encryption at rest | Architecture review |
| Secrets management | `.env` files, secret scan in CI | CI pipeline |
| Audit logging | Immutable `audit_events` table | TC-011 |
| PHI protection | Local-first LLM, no external API for PHI | Deployment config |
| Input validation | Schema validation at API boundary | Integration tests |
| Test data | Synthetic/de-identified only in non-prod | Data policy |

## 6. CI/CD Summary

| Stage | Tool | Gate |
|---|---|---|
| Lint | ruff, black, ESLint | No blockers |
| Unit test | pytest, Jest | Critical tests pass |
| Integration test | pytest (API + DB + Redis) | Core flows pass |
| Security scan | secret scan, dependency scan | No critical/high |
| Build | Docker images | No build errors |
| Deploy QA | Docker Compose | Smoke tests pass |
| UAT | Manual scenarios | Sign-off |

## 7. Test Strategy Summary

| Level | Scope | Owner | Target |
|---|---|---|---|
| Unit | Functions, utilities | Dev | ≥80% coverage |
| Integration | API + DB + Redis + workers | Dev/QA | Core flows pass |
| Permission | RBAC/ABAC retrieval filters | QA/Security | 0 unauthorized chunks |
| OCR | OCR output quality | QA/AI | OCR accuracy on sample set |
| RAG Eval | Relevance, citations, safe refusal | QA/AI | Citation rate ≥95%, safe refusal ≥90% |
| System | End-to-end workflows | QA | No P0/P1 |
| UAT | Business validation | PO/SME | Sign-off |
| Performance | Latency, load | QA/SRE | Summary <30s, search P95 <5s |

## 8. Performance Targets

| Metric | Target | Measurement |
|---|---|---|
| Patient summary latency | <30 sec (MVP dataset) | NFR-PERF-001 |
| Document search latency | P95 <5 sec | NFR-PERF-002 |
| Citation rate (when evidence exists) | ≥95% | RAG eval |
| Safe refusal (no evidence) | ≥90% | RAG eval |
| Unauthorized chunks to LLM | 0 | NFR-SEC-002 |
| MVP runs on 16GB RAM | Local Lite mode | NFR-COST-001 |

## 9. API Response Format

All Chatbot BFF API responses follow this envelope:

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "meta": {
    "trace_id": "uuid",
    "timestamp": "ISO8601",
    "pagination": { "page": 1, "per_page": 20, "total": 100 }
  }
}
```

Error response:
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "FORBIDDEN",
    "message": "No treatment relationship with this patient",
    "details": { ... }
  },
  "meta": { "trace_id": "uuid" }
}
```

## 10. Git & Commit Convention

- **Branch model**: `main` → `develop` → `feature/UC-XXX-description`
- **Commit format**: `<type>(UC-XXX): <description>`
  - Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`
- **PR template**: Must link UC, list AC verified, document AI usage

---

## Change Log
| Version | Date | Author | Change |
|---|---|---|---|
| 2.0 | 2026-06-07 | Agent | Initial creation from architecture, deployment, and requirements docs |
