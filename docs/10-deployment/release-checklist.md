# Release Checklist & Plan

> Project: AI-Powered Hospital Knowledge Assistant  
> Project Code: HOSP-AI-001  
> Version: 2.0  
> Status: Draft  
> Owner: PM / DevOps / Tech Lead  
> Last Updated: 2026-06-07  

---

## 1. Release Milestones & Entry/Exit Criteria

The road to production release follows these phased milestones:

| Milestone | Activities | Entry Criteria | Exit / Promotion Criteria |
|---|---|---|---|
| **Sprint 0** | Setup repo, structure documents, seed synthetic data, configure local Docker stack. | Initial request approved. | Docker stack runs successfully; documents normalized. |
| **MVP Build** | Implement auth, upload, OCR, semantic search, Chat, patient summary, citations. | Sprint 0 completed. | Core features functional in developer environment. |
| **System Test** | Run integration, security, permissions, OCR, and RAG evaluation test plans. | MVP Build completed. | Zero critical (P0/P1) bugs; code coverage ≥80%. |
| **UAT** | Clinical SMEs perform patient summary and chat queries, verifying citation rates. | System Test completed. | SME validation and product owner sign-off. |
| **Demo Release**| Compile project portfolio demo, record screen animations, finalize case study. | UAT completed. | Dashboard functions; video recordings saved. |
| **Pilot** | Deploy in restricted department (ICU/Cardiology) for live hospital trials. | Demo Release completed. | Hospital compliance & institutional review board approval. |

---

## 2. Observability Metrics & Alerts Runbook

If any of the following operational signals breach thresholds, follow the recommended actions:

| Alert Trigger / Signal | Threshold | Action Runbook Steps |
|---|---|---|
| **API 5xx Error Rate** | `>2%` within 5 minutes | 1. Check API gateway and FastAPI container logs.<br>2. Roll back to the previous stable Docker image if immediate hotfix is unavailable. |
| **Chat Response Latency** | `P95 > 5` seconds | 1. Query pgvector index performance logs.<br>2. Review RAG search execution plans in PostgreSQL. |
| **LLM Inference Latency** | `Average > 20` seconds | 1. Check local Ollama container CPU/GPU usage.<br>2. Reduce context chunk counts (limit retrieved chunks) or switch to a smaller quantized model. |
| **OCR Worker Queue Backlog** | Task stale for `>30` mins | 1. Inspect Redis queue state.<br>2. Restart the OCR worker processes or spin up additional RQ worker instances. |
| **RAG No-Evidence Rate** | `>30%` on evaluation dataset | 1. Review document chunking size and overlap policies.<br>2. Check if embedding models need reindexing. |
| **Authorization Failures** | Unexpected spike in 403 errors | 1. Review access control configurations.<br>2. Verify if ABAC rules are misinterpreting clinician departments. |
| **Missing Audit Event** | Any patient query missing audit record | **BLOCK RELEASE**. Audit compliance is a mandatory release gate. Inspect RAG query middleware. |

---

## Change Log
| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-04-27 | Release Manager | Initial release checkpoints |
| 2.0 | 2026-06-07 | Agent | Extracted release plan and observability runbook to dedicated checklist |
