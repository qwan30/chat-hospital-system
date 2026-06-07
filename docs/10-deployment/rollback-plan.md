# Rollback & Contingency Plan

> Project: AI-Powered Hospital Knowledge Assistant  
> Project Code: HOSP-AI-001  
> Version: 2.0  
> Status: Draft  
> Owner: DevOps / SRE Lead  
> Last Updated: 2026-06-07  

---

## 1. Rollback Scenarios & Procedures

If a critical incident occurs during deployment or active operations, SRE/DevOps teams must execute the following rollback runbooks:

| Incident Scenario | Trigger Event | Action / Rollback Steps |
|---|---|---|
| **Critical API Defect** | Smoke test failure or critical P0/P1 error reported post-deployment. | 1. Stop incoming API traffic at the gateway layer.<br>2. Revert the container image tag to the last stable deployment version.<br>3. Verify backend health, then resume traffic. |
| **Database Migration Failure**| Migration script throws errors or risks data integrity/corruption. | 1. Halt the application server deployment pipeline.<br>2. Restore the database from the snapshot backup created immediately before deployment.<br>3. Validate schema integrity, log the failure, and abort deploy. |
| **OCR Process Lock / Failure**| Task queues freeze or PaddleOCR workers crash under high load. | 1. Pause active redis task ingestion queues.<br>2. Restart OCR worker Docker instances.<br>3. Reprocess failed items sequentially; alert SRE if heap exhaustion persists. |
| **LLM Inference Failure** | Ollama connection timeout or CUDA out-of-memory error. | 1. Check GPU allocation and restart the Ollama docker container.<br>2. Fall back to a smaller quantized model (e.g. Qwen2.5 3B instead of 7B) to reduce RAM load.<br>3. If Ollama remains offline, return a friendly "LLM offline" system warning status. |
| **Authorization / Permission Leak**| User accesses unauthorized patient records (audit logs show policy failure). | 1. **IMMEDIATELY SHUT DOWN** affected chat/query endpoints.<br>2. Revert to the last approved security access control policy configuration.<br>3. Review audit event logs, patch the policy bug, write a regression test, and redeploy. |

---

## 2. Emergency Escalation Contact Path

```
Level 1: DevOps/SRE On-Call (Initial Incident Response)
  └── Level 2: Tech Lead / Backend Architect (Code/Database Patching)
        └── Level 3: Product Owner & Hospital Security Representative (Regulatory/PHI Notification)
```

---

## Change Log
| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-04-27 | DevOps Engineer | Initial rollback instructions |
| 2.0 | 2026-06-07 | Agent | Split into dedicated rollback plan documentation |
