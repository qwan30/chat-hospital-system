# Future Improvements

> Project: HOSP-AI-001 · Version: 1.0 · Owner: Product Owner · Last Updated: 2026-06-14  

## 1. Near-Term (Next 2 Sprints)

| ID | Improvement | Value | Effort |
|----|------------|-------|--------|
| FI-001 | CI-integrated RAG evaluation pipeline | Automated quality tracking | Medium |
| FI-002 | Prometheus/Grafana monitoring | Production observability | Medium |
| FI-003 | OIDC discovery for HMS JWT | Standard auth | Small |
| FI-004 | Redis-based shared embedding cache | Multi-worker performance | Small |
| FI-005 | Automated CI dependency scanning | Security compliance | Small |

## 2. Medium-Term (Q3-Q4)

| ID | Improvement | Value | Effort |
|----|------------|-------|--------|
| FI-006 | Dedicated embedding service | Higher retrieval quality | Large |
| FI-007 | Custom fine-tuned medical LLM | Domain accuracy | Large |
| FI-008 | FHIR/HL7 lab results integration | Interoperability | Large |
| FI-009 | Advanced Graph RAG (Neo4j) | Multi-hop reasoning | Large |
| FI-010 | Role-based dashboard customization | Personalization | Medium |

## 3. Long-Term (Post-MVP)

| ID | Improvement |
|----|------------|
| FI-011 | Native mobile apps (iOS/Android) |
| FI-012 | Multi-language NLP |
| FI-013 | Voice-to-text clinical queries |
| FI-014 | Real-time collaborative threads |
| FI-015 | Predictive analytics (readmission, deterioration) |

## 4. Architecture Evolution Triggers

| When | Consider |
|------|---------|
| Retrieval quality becomes bottleneck | Extract embedding service to microservice |
| Query load impacts write performance | Separate read/write DBs (CQRS) |
| Async workflows become complex | Event-driven with message broker |
| Hospital spans regions | Multi-region deployment |

## Change Log
| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-06-14 | Agent | 20 improvements across 3 horizons + architecture triggers |
