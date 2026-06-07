# Monitoring & Operations Guide

> Project: AI-Powered Hospital Knowledge Assistant  
> Project Code: HOSP-AI-001  
> Version: 2.0  
> Status: Draft  
> Owner: DevOps / SRE Lead  
> Last Updated: 2026-06-07  

---

## 1. Operations Performance Metrics

The operations team monitors the following telemetry parameters to verify system responsiveness and compute business value ROI metrics:

| Metric ID | Parameter / Metric | Telemetry Capture Type | Operational Description |
|---|---|---|---|
| **MET-001** | `query_latency_ms` | Histogram (OTel) | Total response duration from user submit to chat answer return. |
| **MET-002** | `retrieval_latency_ms` | Histogram (OTel) | Time spent querying PostgreSQL pgvector HNSW indexes. |
| **MET-003** | `generation_latency_ms` | Histogram (OTel) | Time spent generating tokens on local Ollama/vLLM endpoints. |
| **MET-004** | `documents_retrieved` | Counter (DB) | Count of document chunks retrieved to construct LLM context. |
| **MET-005** | `citations_count` | Counter (DB) | Count of cited source segments embedded in the chat response. |
| **MET-006** | `baseline_manual_time_sec` | Static Constant | Estimated manual time required to perform task (e.g. 900s for summaries). |
| **MET-007** | `actual_ai_time_sec` | Dynamic Variable | Time spent by clinician during AI interaction (BFF response + review). |
| **MET-008** | `estimated_time_saved_sec` | Calculated Value | Formula: `baseline_manual_time_sec - actual_ai_time_sec`. |
| **MET-009** | `estimated_cost_saved` | Calculated Value | Formula: `estimated_time_saved_sec * clinician_hourly_rate`. |
| **MET-010** | `helpful_feedback_rate` | Gauge (DB) | Percentage of user thumbs-up votes on chat answer citations. |
| **MET-011** | `no_evidence_rate` | Gauge (DB) | Percentage of chatbot answers returning `INSUFFICIENT_EVIDENCE`. |
| **MET-012** | `unauthorized_block_count` | Counter (DB) | Total count of blocked unauthorized patient access attempts. |
| **MET-013** | `shared_thread_reuse_count` | Counter (DB) | Frequency of clinicians opening and reading shared thread sessions. |

---

## 2. PostgreSQL Analytics Database Schema

Metric events are logged directly to the chatbot database for de-identified aggregate reporting:

```sql
CREATE TABLE metric_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_id UUID NOT NULL,
    user_id UUID NOT NULL,
    task_type VARCHAR(64) NOT NULL, -- e.g. PATIENT_SUMMARY, CHAT_QUERY
    baseline_manual_time_sec INTEGER NOT NULL,
    actual_ai_time_sec INTEGER NOT NULL,
    estimated_time_saved_sec INTEGER GENERATED ALWAYS AS (baseline_manual_time_sec - actual_ai_time_sec) STORED,
    estimated_cost_saved NUMERIC(12,2) NOT NULL, -- computed as (time_saved_sec / 3600.0) * clinician_hourly_rate
    documents_retrieved INTEGER NOT NULL DEFAULT 0,
    citations_count INTEGER NOT NULL DEFAULT 0,
    query_latency_ms INTEGER NOT NULL,
    retrieval_latency_ms INTEGER NOT NULL,
    generation_latency_ms INTEGER NOT NULL,
    shared_thread_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for date range query optimization
CREATE INDEX idx_metric_events_created_at ON metric_events(created_at);
```

---

## 3. Operations Baseline Estimates

Savings calculations are based on the following verified manual workflow baselines:

| Medical Workflow | Manual Review Baseline | AI Assistant Target | Expected Productivity Gain |
|---|---|---|---|
| **Patient Summary** | 15 minutes (900 seconds) | < 30 seconds | ~95% reduction in review time |
| **Document Lookup** | 5-10 minutes (300-600s) | < 30 seconds | ~90% reduction in search time |
| **Scanned PDF Search** | 5-15 minutes (300-900s) | < 60 seconds | ~80-90% reduction in parsing time |
| **Medication Allergy Check**| 3-5 minutes (180-300s) | < 15 seconds | ~90% reduction in check time |
| **Lab Trend Analysis** | 5-10 minutes (300-600s) | < 30 seconds | ~90% reduction in lookup time |

---

## Change Log
| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-04-28 | PM / Tech Lead | Initial metrics framework definition |
| 2.0 | 2026-06-07 | Agent | Extracted SQL analytics schema, updated baseline calculations, and organized monitoring guide |
