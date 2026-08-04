# Monitoring & Operations Guide

> Project: AI-Powered Hospital Knowledge Assistant  
> Project Code: HOSP-AI-001  
> Version: 3.0  
> Status: Draft  
> Owner: DevOps / SRE Lead  
> Last Updated: 2026-08-04  

---

## 1. Operations Performance Metrics

The operations team monitors the following telemetry parameters to verify system responsiveness and compute business value ROI metrics:

| Metric ID | Parameter / Metric | Telemetry Capture Type | Operational Description |
|---|---|---|---|
| **MET-001** | `query_latency_ms` | Histogram (OTel) | Total response duration from user submit to chat answer return. |
| **MET-002** | `retrieval_latency_ms` | Histogram (OTel) | Time spent querying PostgreSQL pgvector HNSW indexes. |
| **MET-003** | `generation_latency_ms` | Histogram (OTel) | Time spent generating tokens on Gemini / DeepSeek API endpoints. |
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

Metrics are tracked via the `MetricsService` in `app/backend/src/hospital_ai/services/metrics.py` and exposed through the `/api/v1/feedback/metrics/summary` endpoint. Impact metrics (time saved, cost saved, helpful rate) are derived from `ai_queries` records and user feedback submissions.

The `/api/v1/feedback/metrics/summary` endpoint returns:
- `total_queries` — total AI queries processed
- `avg_latency_ms` — average query latency
- `total_time_saved_sec` — estimated clinician time saved
- `total_cost_saved` — estimated cost savings
- `helpful_rate` — percentage of positive (thumbs-up) feedback
- `no_evidence_rate` — percentage of queries returning "no evidence"
- `audit_deny_count` — total access denials logged in `audit_logs`

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

## 4. VPS Monitoring Profile

For the initial deployment on a 4 GB RAM VPS, the standard Grafana/Loki/Tempo observability stack is deferred until memory testing proves sufficient headroom. Monitoring is performed natively using the following tools:

- `free -h` — Monitor system RAM and swap usage.
- `df -h` — Monitor system disk usage.
- `docker stats --no-stream` — View per-container CPU and memory usage.
- `docker system df` — Monitor Docker disk usage.
- `docker compose -f infra/docker-compose.yml logs --tail=100 backend` — View recent backend application logs.
- `docker compose -f infra/docker-compose.yml exec redis redis-cli INFO memory` — Monitor Redis memory consumption.

---

## 5. Alerts and Thresholds

| What | How | Threshold | Action |
|------|-----|-----------|--------|
| API health | `curl <PLACEHOLDER_DOMAIN>/api/v1/health` | Non-200 for >60s | Restart backend |
| Disk usage | `df -h` | <20% free | Prune Docker images, check pg_dump retention |
| Memory | `free -h` | <512MB available | Check for memory leaks, restart worker |
| Docker disk | `docker system df` | >30GB | `docker system prune` |
| Queue depth | `redis-cli LLEN rq:queue:default` | >50 pending jobs | Check worker health |
| Failed jobs | `redis-cli LLEN rq:queue:failed` | >0 | Inspect and retry or clear |
| Chat latency | Backend logs / metrics endpoint | P95 >10s | Check Gemini quota |
| Gemini quota | Google AI Studio dashboard | >80% of limit | Reduce chat concurrency or switch to DeepSeek |

**LLM Provider Monitoring**:
Monitor Gemini and DeepSeek API health and rate limits via their respective provider dashboards. Internal usage can be tracked via querying `audit_events` in PostgreSQL.

---

## Change Log
| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-04-28 | PM / Tech Lead | Initial metrics framework definition |
| 2.0 | 2026-06-07 | Agent | Extracted SQL analytics schema, updated baseline calculations, and organized monitoring guide |
| 3.0 | 2026-08-04 | Agent | Added VPS monitoring profile, alerts, and replaced Ollama with Gemini/DeepSeek |
