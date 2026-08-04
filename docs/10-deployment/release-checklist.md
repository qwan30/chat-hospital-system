# Release Checklist & Plan

> Project: AI-Powered Hospital Knowledge Assistant  
> Project Code: HOSP-AI-001  
> Version: 2.2
> Status: Staging/demo contract; production approval remains outstanding
> Owner: PM / DevOps / Tech Lead  
> Last Updated: 2026-08-04

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
| **External LLM Inference Latency** | `Average > 20` seconds | 1. Check Gemini or the explicitly selected DeepSeek provider status and API latency.<br>2. Reduce context chunk counts and review provider quotas. Automatic Gemini/DeepSeek fallback is not part of the contract. |
| **OCR Worker Queue Backlog** | Task stale for `>30` mins | 1. Inspect Redis queue state.<br>2. Restart the OCR worker processes or spin up additional RQ worker instances. |
| **RAG No-Evidence Rate** | `>30%` on evaluation dataset | 1. Review document chunking size and overlap policies.<br>2. Check if embedding models need reindexing. |
| **Authorization Failures** | Unexpected spike in 403 errors | 1. Review access control configurations.<br>2. Verify if ABAC rules are misinterpreting clinician departments. |
| **Missing Audit Event** | Any patient query missing audit record | **BLOCK RELEASE**. Audit compliance is a mandatory release gate. Inspect RAG query middleware. |

---

## 3. Repository deployment-contract gate

Run this gate from the repository root before requesting a Dokploy deploy or
rollback handoff:

```bash
python app/backend/scripts/verify_deployment_contract.py
```

The gate checks the Vercel frontend plus Dokploy/Traefik backend shape, private
database/Redis/backend ports, R2/Gemini/JWKS variables, immutable image and
Dokploy hook workflows, frontend secret isolation, and staging/demo data
boundaries. `0` means the repository contract is valid; `2` means the contract
or required repository inputs are invalid. It does not contact Dokploy, GHCR,
Cloudflare, the VPS, or an LLM provider.

## 4. Staging/demo promotion gates

- [ ] Repository deployment-contract validator returns `0`, including the
      candidate `--backend-image` immutable-reference check.
- [ ] CI backend, migration, frontend, observability, and image scan gates pass.
- [ ] CI release artifact records the source SHA, image tag, and image digest.
- [ ] Production Compose is image-only, requires `BACKEND_IMAGE`, and uses the
      same immutable image for the migration container, backend, and worker.
- [ ] PostgreSQL `768m`, Redis `256m`, backend `768m`, and worker `1024m`
      memory ceilings are present; actual VPS RAM/swap/disk and `docker stats`
      evidence is captured separately.
- [ ] Candidate image is pulled and `alembic upgrade head` succeeds before the
      backend/worker rollout.
- [ ] Dokploy environment injects backend-only secrets; Vercel contains only
      client-safe variables such as `VITE_API_URL`.
- [ ] Traefik route `api.<domain> -> backend:8000` is configured and HTTPS is
      verified by the operator.
- [ ] Encrypted PostgreSQL backup and recoverable R2 object version/export are
      recorded, with a known restore-test result.
- [ ] Smoke test uses synthetic/de-identified data and confirms API health,
      worker queue behavior, document processing, citations, and permission
      boundaries.
- [ ] Production remains blocked until hospital/security approval, approved
      network boundary, and explicit release sign-off exist.

---

## Change Log
| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-04-27 | Release Manager | Initial release checkpoints |
| 2.0 | 2026-06-07 | Agent | Extracted release plan and observability runbook to dedicated checklist |
| 2.1 | 2026-08-04 | Agent | Added Dokploy/Vercel contract validation and staging/demo promotion gates |
| 2.2 | 2026-08-04 | Agent | Added Task 7 immutable-image, migration-order, and VPS resource gates |
