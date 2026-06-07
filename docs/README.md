# AI-Powered Hospital Knowledge Assistant Documentation Pack

Welcome to the documentation pack for the AI-Powered Hospital Knowledge Assistant (HOSP-AI-001). This documentation has been structured hierarchically to serve as a comprehensive, modular specification for design, development, security, operations, and handoff.

---

## 1. Directory Structure

The documentation is organized into the following folders under `docs/`:

*   **`00-overview/`**: Technical foundation, project context, definition of ready/done, and document indexing.
    *   [project-foundation.md](00-overview/project-foundation.md) — Tech stack, architecture principles, and code standards.
    *   [project-context.md](00-overview/project-context.md) — Project metadata and business background.
    *   [documentation-index.md](00-overview/documentation-index.md) — Persona-based reading paths.
    *   [definition-of-ready-done.md](00-overview/definition-of-ready-done.md) — Quality gates and sprint definitions.
*   **`01-business/`**: Business case, KPIs, and business requirements.
    *   [brd.md](01-business/brd.md) — Business case index, KPIs, RACI, and risk maps.
    *   [business-rules.md](01-business/business-rules.md) — Constraints and business logic catalog.
    *   Individual `BR-XXX.md` requirement specifications.
*   **`02-product/`**: Personas, data requirements, and product roadmap.
    *   [prd.md](02-product/prd.md) — Personas, data objects, and MVP criteria.
*   **`03-requirements/`**: Detailed use cases and access controls.
    *   [use-cases.md](03-requirements/use-cases.md) — Traceability matrix index.
    *   [functional-requirements.md](03-requirements/functional-requirements.md) — System features.
    *   [non-functional-requirements.md](03-requirements/non-functional-requirements.md) — Performance, security, and privacy targets.
    *   [permissions-matrix.md](03-requirements/permissions-matrix.md) — Scopes and access matrices.
    *   Individual `UC-XXX.md` use case specifications with Given/When/Then acceptance criteria.
*   **`04-architecture/`**: High-level designs, ADRs, and security architecture.
    *   [architecture.md](04-architecture/architecture.md) — System context and component boundaries.
    *   [security-architecture.md](04-architecture/security-architecture.md) — Data protection flows and retrieval filters.
    *   [adr/](04-architecture/adr/) — Architectural Decision Records (ADR-001 through ADR-007).
*   **`05-api/`**: REST endpoint designs and error specifications.
    *   [api-contract.md](05-api/api-contract.md) — Endpoint contracts and JSON payload examples.
    *   [api-overview.md](05-api/api-overview.md) — Integration mappings and workflows.
    *   [error-codes.md](05-api/error-codes.md) — Standardized system error codes.
*   **`06-database/`**: Physical and relational schemas.
    *   [db-schema.md](06-database/db-schema.md) — Entity dictionary and DDL table schemas.
    *   [erd.md](06-database/erd.md) — Entity-relationship diagrams.
*   **`07-flows/`**: Process sequences and state machines.
    *   [state-machine.md](07-flows/state-machine.md) — Document and query state machines.
*   **`08-ui-ux/`**: Design tokens and screen lists.
    *   [design-system.md](08-ui-ux/design-system.md) — Color palettes, components, and wireframes.
    *   [screen-list.md](08-ui-ux/screen-list.md) — Master screen catalog of the 25 screenshots.
*   **`09-testing/`**: Test cases and coverage matrices.
    *   [test-plan.md](09-testing/test-plan.md) — Test strategy and AI/RAG metrics.
    *   [test-cases.md](09-testing/test-cases.md) — Detailed test scenario inventory.
    *   [rtm.md](09-testing/rtm.md) — Requirements Traceability Matrix.
    *   [manual-test-checklist.md](09-testing/manual-test-checklist.md) — Manual UAT scenarios.
*   **`10-deployment/`**: Installation and rollbacks.
    *   [deployment-guide.md](10-deployment/deployment-guide.md) — Environment setups (Local Lite, Dev, Prod).
    *   [ci-cd.md](10-deployment/ci-cd.md) — Automated build pipeline definitions.
    *   [release-checklist.md](10-deployment/release-checklist.md) — Milestones and runbook triggers.
    *   [rollback-plan.md](10-deployment/rollback-plan.md) — Incident response steps.
*   **`11-operations/`**: Monitoring models.
    *   [monitoring-guide.md](11-operations/monitoring-guide.md) — Operations performance metrics.
*   **`12-handover/`**: Delivery packages.
    *   [project-summary.md](12-handover/project-summary.md) — Audited repository evidence sheet.
    *   [final-deliverables.md](12-handover/final-deliverables.md) — CV portfolio case study.

---

## 2. Reading Paths

*   **For Business Analysts & Product Owners**: Start with [brd.md](01-business/brd.md), then read [prd.md](02-product/prd.md) and [use-cases.md](03-requirements/use-cases.md).
*   **For Developers & Architects**: Read [project-foundation.md](00-overview/project-foundation.md), then inspect [architecture.md](04-architecture/architecture.md) and [api-contract.md](05-api/api-contract.md).
*   **For QA & Testers**: Read [test-plan.md](09-testing/test-plan.md), [rtm.md](09-testing/rtm.md), and [manual-test-checklist.md](09-testing/manual-test-checklist.md).
*   **For DevOps & SREs**: Check [deployment-guide.md](10-deployment/deployment-guide.md), [ci-cd.md](10-deployment/ci-cd.md), and [monitoring-guide.md](11-operations/monitoring-guide.md).
