# Ready-to-Code Go/No-Go Checklist

**Project:** AI-Powered Hospital Knowledge Assistant
**Project Code:** HOSP-AI-001
**Version:** 1.0
**Status:** Draft
**Last Updated:** 2026-04-27

**Owner:** PM / PO / Tech Lead / QA

## 1. Go / No-Go Summary
| Decision | Criteria | Result |
|---|---|---|
| GO | Mandatory items complete; no P0/P1; owners assigned | [ ] |
| CONDITIONAL GO | Minor accepted risks with mitigation/date | [ ] |
| NO-GO | Missing critical requirement/design/security/test/env | [ ] |

## 2. Mandatory Checklist
| # | Criteria | Evidence | Owner | Status |
|---|---|---|---|---|
| 1 | Business scope and KPI approved | 01 BRD | PO/BA | [ ] |
| 2 | Process and use cases approved | 02 Process | BA/SME | [ ] |
| 3 | Requirements have acceptance criteria | 03 PRD | PO/BA | [ ] |
| 4 | Security/privacy requirements confirmed | PRD NFR + access matrix | Security | [ ] |
| 5 | UX flow and screens reviewed | 04 UX | UX | [ ] |
| 6 | Architecture approved | 05 SDD | Tech Lead | [ ] |
| 7 | API/DB/integration approved | 06 API/DB | Backend/Data | [ ] |
| 8 | Deployment plan ready | 07 Deployment | DevOps | [ ] |
| 9 | Test Plan + RTM ready | 08 Test Plan | QA | [ ] |
| 10 | Audit and metrics defined | API/Test docs | PM/Security | [ ] |
| 11 | Synthetic data strategy defined | Test plan | QA/Data | [ ] |
| 12 | AI safety rules defined | PRD rules | PO/Compliance | [ ] |

## 3. Allowed Conditional GO Items
| Open Item | Impact | Mitigation |
|---|---|---|
| UI polish | Low | Improve during Sprint 1 |
| Neo4j deployment | Medium | Use SQL graph in MVP |
| Advanced VLM OCR | Medium | Use PaddleOCR first |
| Production IAM | Medium | Use local auth in MVP, OIDC later |

## 4. No-Go Conditions
| Signal | Required Action |
|---|---|
| No permission matrix | Define RBAC/ABAC before coding |
| No citation policy | Add citation design/tests |
| No audit plan | Implement audit schema first |
| Real patient data in dev | Generate/mask data first |
| Model too heavy for 16GB | Use 3B/7B quantized model |
| No metrics | Add metric_events before ROI/CV claim |
| No safe refusal behavior | Implement insufficient evidence response |

## 5. Sprint 0 Checklist
| Item | Owner | Status |
|---|---|---|
| Create repo structure | Tech Lead | [ ] |
| Add docs under `docs/` | PM/BA | [ ] |
| Docker Compose for PostgreSQL/Redis/API | DevOps | [ ] |
| Enable pgvector | Backend | [ ] |
| Add Ollama local LLM | AI Engineer | [ ] |
| Add OCR smoke script | AI Engineer | [ ] |
| Generate synthetic patients/documents | QA/Data | [ ] |
| Implement auth placeholder | Backend | [ ] |
| Create RAG benchmark questions | QA/SME | [ ] |
| Add `.env.example` | DevOps | [ ] |

## 6. Khuym Workflow for Development
| Stage | Slash Command | Definition of Done |
|---|---|---|
| Start | `/using-khuym` | `CONTEXT.md` loaded |
| Clarify | `/exploring` | Decisions captured |
| Plan | `/planning` | `approach.md` + beads |
| Validate | `/validating` | Gate passed |
| Parallelize | `/swarming` | Workers assigned |
| Code | `/executing` | Task implemented + tested |
| Review | `/reviewing` | Verified |
| Learn | `/compounding` | Lessons captured |
| Debug | `/debugging` | Blocker resolved |
| Inspect repo | `/gkg` | Codebase understood |

## 7. Final Approval
| Role | Name | Decision | Date |
|---|---|---|---|
| PO/BA | TBD | GO / NO-GO / CONDITIONAL GO | TBD |
| Tech Lead | TBD | GO / NO-GO / CONDITIONAL GO | TBD |
| QA Lead | TBD | GO / NO-GO / CONDITIONAL GO | TBD |
| Security | TBD | GO / NO-GO / CONDITIONAL GO | TBD |
| PM | TBD | GO / NO-GO / CONDITIONAL GO | TBD |
| Sponsor | TBD | GO / NO-GO / CONDITIONAL GO | TBD |
