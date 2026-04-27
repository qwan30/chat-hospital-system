# Template Usage Guide

**Project:** AI-Powered Hospital Knowledge Assistant
**Project Code:** HOSP-AI-001
**Version:** 1.0
**Status:** Draft
**Last Updated:** 2026-04-27

**Owner:** PM / BA / Tech Lead / QA

## Purpose
This documentation pack converts the uploaded enterprise DOCX templates into Markdown for a hospital AI assistant project. It should be copied into `docs/` and used as the Sprint 0 baseline before coding.

## Project Summary
Build a secure, local-first AI assistant for hospital staff. The assistant uses OCR, PostgreSQL, pgvector, permission-aware RAG, and later Graph RAG to answer questions over patient records and medical documents with citations.

## Recommended Reading Order
1. `01_business_case_brd.md` - business value, KPIs, scope, ROI
2. `02_process_bpmn_use_case.md` - As-Is/To-Be process and use cases
3. `03_prd_srs_requirements.md` - functional/NFR/data requirements
4. `04_ui_ux_design_package.md` - UX, IA, screens, design rules
5. `05_system_architecture_sdd.md` - architecture, components, sequences, ADRs
6. `06_database_api_integration.md` - ERD, tables, APIs, integrations
7. `07_deployment_infrastructure_plan.md` - environments, CI/CD, rollback
8. `08_master_test_plan_rtm.md` - test strategy, test cases, RTM
9. `09_ready_to_code_go_nogo_checklist.md` - readiness gate
10. `10_design_system_and_metrics.md` - UI style and impact metrics

## MVP Direction for 16GB RAM
| Area | Choice |
|---|---|
| Backend | FastAPI |
| DB | PostgreSQL + pgvector |
| Queue | Redis + Celery/RQ |
| OCR | PaddleOCR / PP-OCR CPU mode |
| Local LLM | Ollama with Qwen2.5 3B or 7B quantized |
| Embeddings | BGE-M3 if possible; smaller multilingual embedding for low-memory mode |
| Graph | SQL relationships in MVP; Neo4j in Phase 2 |
| UI | Streamlit for fastest MVP or Next.js for product UI |

## Khuym Workflow Mapping
| Work | Slash Command | Output |
|---|---|---|
| Start/resume | `/using-khuym` | Load project state |
| Clarify | `/exploring` | Decisions in `CONTEXT.md` |
| Plan | `/planning` | `approach.md` and task beads |
| Gate check | `/validating` | Security/privacy/performance validation |
| Parallelize | `/swarming` | Worker agents by domain |
| Implement | `/executing` | Code + tests |
| Review | `/reviewing` | Verification + UAT notes |
| Learn | `/compounding` | Lessons learned |
| Debug | `/debugging` | Blocker diagnosis |
| Repo intelligence | `/gkg` | Codebase understanding |

## Key Portfolio Target
Reduced patient information lookup time from ~10-15 minutes to under 30 seconds using OCR, permission-aware RAG, and Graph RAG.
