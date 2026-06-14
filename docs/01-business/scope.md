# Project Scope

> Project: HOSP-AI-001 · Version: 1.0 · Owner: Product Owner · Last Updated: 2026-06-14  

## 1. MVP Scope — Implemented

| Area | Deliverable | Status |
|------|------------|--------|
| Dashboard | Populated + empty states with metrics | ✅ |
| AI Chat | Cited Q&A (simple_qa, decompose_qa, patient_summary) | ✅ |
| Streaming | SSE token-by-token answers | ✅ |
| Patient Summary | AI-generated structured clinical summary | ✅ |
| Document OCR | PDF → PyMuPDF → chunk → pgvector index | ✅ |
| Semantic Search | Vector HNSW + BM25 + hybrid + Graph RAG | ✅ |
| Drug Check | Drug-allergy interaction detection | ✅ |
| Audit Trail | Immutable audit_logs, all sensitive queries | ✅ |
| Permissions | RBAC (7 roles) + ABAC (5 scopes, expiration) | ✅ |
| Access Requests | Break-glass justification workflow | ✅ |
| Impact Metrics | Time/cost saved, helpful rate dashboard | ✅ |
| RAG Trace | Pre/post-rerank scores, retrieval observability | ✅ |
| Chat Threads | Multi-user, patient-linked/general scope | ✅ |
| HMS Sync | Patient data sync with progress tracking | ✅ |
| Global Search | Ctrl+K command palette | ✅ |
| System Settings | 14 runtime configuration keys | ✅ |
| SSO + MFA | HMS JWT bridge + MFA verification | ✅ |
| Patient Timeline | Chronological encounters/labs/docs | ✅ |
| Responsive UI | 14 pages, 30+ shadcn/ui, 25+ screens | ✅ |

## 2. Out of Scope (MVP)

- Automated medical diagnosis (assistive only)
- Non-HMS EMR integration
- Native mobile apps (responsive web only)
- Multi-language NLP (English-only for medical)
- Payment/billing
- HL7/FHIR real-time integration
- Patient-facing portal
- External cloud LLM for PHI

## 3. Post-MVP Roadmap

| Priority | Feature | Rationale |
|----------|---------|-----------|
| High | Dedicated embedding service | Better retrieval quality |
| High | Prometheus/Grafana monitoring | Production observability |
| Medium | FHIR/HL7 integration | Interoperability |
| Medium | Custom fine-tuned medical LLM | Domain accuracy |
| Low | Native mobile apps | Bedside access |
| Low | Multi-language support | International deployment |

## 4. Constraints

| Constraint | Detail |
|------------|--------|
| Hardware | 16GB RAM workstation (Qwen2.5 3B/7B Q4) |
| Network | Hospital intranet only, no public internet |
| PHI | No patient data to external cloud |
| Compliance | HIPAA audit trail mandatory |

## Change Log
| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-06-14 | Agent | Created from codebase + project foundation |
