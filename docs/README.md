# AI-Powered Hospital Knowledge Assistant Documentation Pack

> **Version:** 4.0 · **Status:** Production · **Last Updated:** 2026-06-14 · **Synced with codebase**

Welcome to the documentation pack for the AI-Powered Hospital Knowledge Assistant (HOSP-AI-001). This documentation has been structured hierarchically to serve as a comprehensive, modular specification for design, development, security, operations, and handoff. **16 new files** added from the universal-docs-generator-skill template.

---

## 1. Directory Structure

The documentation is organized into the following folders under `docs/`:

*   **`00-overview/`**: Project foundation, context, and governance.
    *   [project-foundation.md](00-overview/project-foundation.md) — **Source of Truth** — technical standards, architecture, conventions.
    *   [project-context.md](00-overview/project-context.md) — Project metadata, business background, key statistics.
    *   [documentation-index.md](00-overview/documentation-index.md) — Persona-based reading paths and directory map.
    *   [document-control.md](00-overview/document-control.md) — Approval matrix, versioning rules, sync verification.
*   **`01-business/`**: Business case, KPIs, business rules, stakeholders, scope.
    *   [brd.md](01-business/brd.md) — Business case index, KPIs, RACI, risk maps.
    *   [business-rules.md](01-business/business-rules.md) — Constraints and business logic catalog.
    *   [stakeholders.md](01-business/stakeholders.md) — Stakeholder list, RACI matrix, communication plan.
    *   [scope.md](01-business/scope.md) — MVP scope (implemented), out-of-scope, future roadmap.
    *   [glossary.md](01-business/glossary.md) — Business, technical, pipeline, and state terminology.
    *   [acceptance-criteria.md](01-business/acceptance-criteria.md) — AC writing guide with project examples.
    *   [BR-TEMPLATE.md](01-business/BR-TEMPLATE.md) — Reusable Business Requirement template.
    *   Individual `BR-001` through `BR-007` requirement specifications.
*   **`02-product/`**: Personas, data requirements, and product roadmap.
    *   [prd.md](02-product/prd.md) — Personas, data objects, and MVP criteria.
*   **`03-requirements/`**: Detailed use cases, SRS, and access controls.
    *   [srs.md](03-requirements/srs.md) — Software Requirements Specification (24 FRs + 22 NFRs + traceability matrix).
    *   [use-cases.md](03-requirements/use-cases.md) — Use case index and traceability matrix.
    *   [functional-requirements.md](03-requirements/functional-requirements.md) — System features.
    *   [non-functional-requirements.md](03-requirements/non-functional-requirements.md) — Performance, security, privacy targets.
    *   [permissions-matrix.md](03-requirements/permissions-matrix.md) — RBAC + ABAC access matrices.
    *   [UC-TEMPLATE.md](03-requirements/UC-TEMPLATE.md) — Reusable Use Case Specification template.
    *   Individual `UC-001` through `UC-009` use case specifications with Given/When/Then.
*   **`04-architecture/`**: High-level designs, ADRs, coding standards, tech stack.
    *   [architecture.md](04-architecture/architecture.md) — System context and component boundaries.
    *   [security-architecture.md](04-architecture/security-architecture.md) — Data protection flows and retrieval filters.
    *   [module-breakdown.md](04-architecture/module-breakdown.md) — Complete module map: 14 routes, 18 services, 14+ pages, 60+ components.
    *   [tech-stack.md](04-architecture/tech-stack.md) — Full technology stack: backend, frontend, LLM/AI, infrastructure.
    *   [coding-standards.md](04-architecture/coding-standards.md) — Python, TypeScript, database conventions + code limits.
    *   [adr/](04-architecture/adr/) — ADR-001 through ADR-007 + [adr-template.md](04-architecture/adr/adr-template.md).
*   **`05-api/`**: REST endpoint designs and error specifications.
    *   [api-contract.md](05-api/api-contract.md) — Endpoint contracts and JSON payload examples.
    *   [api-overview.md](05-api/api-overview.md) — Integration mappings and workflows.
    *   [error-codes.md](05-api/error-codes.md) — Standardized system error codes.
*   **`06-database/`**: Physical and relational schemas, data dictionary, migrations.
    *   [db-schema.md](06-database/db-schema.md) — 13-table schema with constraints and relationships.
    *   [erd.md](06-database/erd.md) — Entity-relationship diagram (Mermaid).
    *   [data-dictionary.md](06-database/data-dictionary.md) — Column-level reference for all 13 tables.
    *   [migration-guide.md](06-database/migration-guide.md) — Alembic commands, 6-migration history, expand-and-contract.
*   **`07-flows/`**: Process sequences, state machines, user journeys.
    *   [state-machine.md](07-flows/state-machine.md) — Document, query, sync, thread state machines.
    *   [end-to-end-business-flow.md](07-flows/end-to-end-business-flow.md) — 4 critical flows: Chat RAG, Document OCR, Access Request, HMS Sync.
    *   [user-flow.md](07-flows/user-flow.md) — 6 persona-based user journeys (Doctor, Nurse, Pharmacist, Records, Security, Admin).
*   **`08-ui-ux/`**: Design system, Figma execution plans, and UI/API traceability.
    *   [00_product_ui_truth.md](08-ui-ux/00_product_ui_truth.md) — Product UI/UX truth (design tokens, brand).
    *   [figma-design-system-delivery.md](08-ui-ux/figma-design-system-delivery.md) — Figma design system delivery specs.
    *   [hms-frontend-ui-fix-design-system.md](08-ui-ux/hms-frontend-ui-fix-design-system.md) — Frontend UI fix and design system reference.
    *   [master-figma-execution-plan.md](08-ui-ux/master-figma-execution-plan.md) — Master Figma execution plan.
    *   [ui_api_traceability_matrix.md](08-ui-ux/ui_api_traceability_matrix.md) — Screen-to-API traceability matrix.
    *   [screen-design/](../docs/screen-design/) — 25+ screen design PNG references.
*   **`09-testing/`**: Test cases and coverage matrices.
    *   [test-plan.md](09-testing/test-plan.md) — Test strategy and AI/RAG metrics.
    *   [test-cases.md](09-testing/test-cases.md) — Detailed test scenario inventory.
    *   [rtm.md](09-testing/rtm.md) — Requirements Traceability Matrix.
    *   [manual-test-checklist.md](09-testing/manual-test-checklist.md) — Manual UAT scenarios.
*   **`10-deployment/`**: Installation, env vars, CI/CD, rollbacks.
    *   [deployment-guide.md](10-deployment/deployment-guide.md) — Environment setups (Local Lite, Dev, Prod).
    *   [env-variables.md](10-deployment/env-variables.md) — Complete reference: 30+ settings in 9 categories.
    *   [ci-cd.md](10-deployment/ci-cd.md) — Automated build pipeline definitions.
    *   [release-checklist.md](10-deployment/release-checklist.md) — Milestones and runbook triggers.
    *   [rollback-plan.md](10-deployment/rollback-plan.md) — Incident response steps.
*   **`11-operations/`**: Monitoring models.
    *   [monitoring-guide.md](11-operations/monitoring-guide.md) — Operations performance metrics.
*   **`12-handover/`**: Delivery packages, onboarding, known issues, roadmap.
    *   [project-summary.md](12-handover/project-summary.md) — Audited repository evidence sheet.
    *   [final-deliverables.md](12-handover/final-deliverables.md) — CV portfolio case study.
    *   [developer-onboarding.md](12-handover/developer-onboarding.md) — Quick start, repo structure, commands, env vars.
    *   [repository-guide.md](12-handover/repository-guide.md) — Complete codebase tour: all routes, services, tables, components.
    *   [known-issues.md](12-handover/known-issues.md) — 15 documented issues across tech debt, performance, testing, security.
    *   [future-improvements.md](12-handover/future-improvements.md) — 20 improvements across near/medium/long-term + architecture triggers.

---

## 2. Reading Paths

*   **For Business Analysts & Product Owners**: Start with [brd.md](01-business/brd.md), then read [prd.md](02-product/prd.md) and [use-cases.md](03-requirements/use-cases.md).
*   **For Developers & Architects**: Read [architecture.md](04-architecture/architecture.md), then inspect [api-contract.md](05-api/api-contract.md) and the backend source under `app/backend/src/hospital_ai/`.
*   **For QA & Testers**: Read [test-plan.md](09-testing/test-plan.md), [rtm.md](09-testing/rtm.md), and [manual-test-checklist.md](09-testing/manual-test-checklist.md).
*   **For DevOps & SREs**: Check [deployment-guide.md](10-deployment/deployment-guide.md), [ci-cd.md](10-deployment/ci-cd.md), and [monitoring-guide.md](11-operations/monitoring-guide.md).
