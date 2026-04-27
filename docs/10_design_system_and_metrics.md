# Design System & Impact Metrics

**Project:** AI-Powered Hospital Knowledge Assistant
**Project Code:** HOSP-AI-001
**Version:** 1.0
**Status:** Draft
**Last Updated:** 2026-04-27

**Owner:** UX Lead / PM / Tech Lead

## 1. Purpose
Define the UI style and measurement model needed to prove the hospital AI assistant reduces time, effort, and cost.

## 2. UI Direction
Use a Linear/Cal.com-inspired minimal enterprise style: monochrome-first, high readability, subtle shadows, and medical semantic colors only when meaning matters.

## 3. Design Tokens
| Role | Token | Value |
|---|---|---|
| Primary text | text.primary | #242424 |
| Secondary text | text.secondary | #898989 |
| Background | bg.default | #ffffff |
| Surface | surface.default | #ffffff |
| Info | semantic.info | #2563eb |
| Success | semantic.success | #16a34a |
| Warning | semantic.warning | #f59e0b |
| Danger | semantic.danger | #dc2626 |

## 4. Core Components
| Component | Purpose | Must Have |
|---|---|---|
| Patient Banner | Prevent wrong-patient context | MRN/ID, DOB, scope |
| AI Answer Card | Safe response display | Answer, citations, confidence, disclaimer |
| Citation Chip | Link claim to source | Document/page/table/chunk |
| Source Viewer | Verify answer | Page preview and highlight |
| Medical Alert | Safety warning | Severity, source, explanation |
| Metrics Card | Prove impact | Baseline, actual, time saved, cost estimate |
| Audit Row | Review access | Actor, action, object, trace ID |

## 5. AI Answer Layout
```text
Patient Context Banner
Question
Answer
Evidence / Citations
Confidence
Safety Note
```

## 6. Metrics to Capture
| Metric ID | Metric | Description |
|---|---|---|
| MET-001 | query_latency_ms | Total response time |
| MET-002 | retrieval_latency_ms | Retrieval time |
| MET-003 | generation_latency_ms | LLM generation time |
| MET-004 | documents_retrieved | Docs/chunks retrieved |
| MET-005 | citations_count | Number of citations |
| MET-006 | baseline_manual_time_sec | Estimated manual baseline |
| MET-007 | actual_ai_time_sec | Actual AI workflow time |
| MET-008 | estimated_time_saved_sec | Baseline - actual |
| MET-009 | estimated_cost_saved | Time saved * hourly cost |
| MET-010 | helpful_feedback_rate | User feedback metric |
| MET-011 | no_evidence_rate | Unsupported query rate |
| MET-012 | unauthorized_block_count | Blocked access attempts |

## 7. Metric Event Schema
```sql
CREATE TABLE metric_events (
    id UUID PRIMARY KEY,
    query_id UUID,
    user_id UUID,
    task_type VARCHAR(64) NOT NULL,
    baseline_manual_time_sec INTEGER,
    actual_ai_time_sec INTEGER,
    estimated_time_saved_sec INTEGER,
    estimated_cost_saved NUMERIC(12,2),
    documents_retrieved INTEGER,
    citations_count INTEGER,
    query_latency_ms INTEGER,
    retrieval_latency_ms INTEGER,
    generation_latency_ms INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);
```

## 8. Baseline Assumptions
| Workflow | Manual Baseline | AI Target | Target Reduction |
|---|---:|---:|---:|
| Patient summary | 10-15 min | <30 sec | ~95% |
| Document lookup | 5-10 min | <30 sec | ~90% |
| Scanned PDF search | 5-15 min | <60 sec | ~80-90% |
| Medication/allergy pre-check | 3-5 min | <15 sec | ~90% |
| Lab trend lookup | 5-10 min | <30 sec | ~90% |

## 9. Cost Saving Formula
```text
cost_saved = time_saved_hours * average_staff_hourly_cost
```
Example:
```text
100 lookups/day * 10 minutes saved / 60 * $20/hour = ~$333/day
```

## 10. CV / Portfolio Template
```text
Built an AI-powered hospital knowledge assistant using FastAPI, PostgreSQL, pgvector, OCR, and Graph RAG.
Reduced patient information lookup time from ~10-15 minutes to under 30 seconds in simulated clinical workflows.
Decreased manual document review effort by ~80% through permission-aware semantic search with citations.
Implemented audit and metric tracking to estimate operational cost savings of ~$300/day.
```
