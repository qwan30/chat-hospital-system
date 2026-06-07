# Documentation Index

> Project: AI-Powered Hospital Knowledge Assistant  
> Project Code: HOSP-AI-001  
> Version: 2.0  
> Last updated: 2026-06-07

## Quick Start Reading Paths

### For Business Analyst / Product Owner
1. [Project Context](project-context.md)
2. [BRD](../01-business/brd.md)
3. [PRD](../02-product/prd.md)
4. [Use Cases](../03-requirements/use-cases.md)
5. [Screen List](../08-ui-ux/screen-list.md)

### For Developer
1. [Project Foundation](project-foundation.md) ← **start here**
2. [Architecture](../04-architecture/architecture.md)
3. [API Contract](../05-api/api-contract.md)
4. [DB Schema](../06-database/db-schema.md)
5. [State Machines](../07-flows/state-machine.md)

### For QA / Tester
1. [Test Plan](../09-testing/test-plan.md)
2. [Test Cases](../09-testing/test-cases.md)
3. [RTM](../09-testing/rtm.md)
4. [Use Cases (with ACs)](../03-requirements/use-cases.md)

### For Security / Compliance
1. [Project Foundation § Security](project-foundation.md#5-security-posture)
2. [Permissions Matrix](../03-requirements/permissions-matrix.md)
3. [Audit Logs](../09-testing/test-cases.md) (TC-002, TC-011, TC-016)

### For DevOps / SRE
1. [Deployment Guide](../10-deployment/deployment-guide.md)
2. [CI/CD](../10-deployment/ci-cd.md)
3. [Monitoring Guide](../11-operations/monitoring-guide.md)
4. [Rollback Plan](../10-deployment/rollback-plan.md)

---

## Folder Map

| Directory | Purpose | Key Files |
|---|---|---|
| `00-overview/` | Documentation map, project context, technical foundation | `project-foundation.md`, `project-context.md`, `documentation-index.md` |
| `01-business/` | Business requirements and rules | `brd.md`, `BR-001-*.md` through `BR-007-*.md`, `business-rules.md`, `glossary.md` |
| `02-product/` | Product requirements and roadmap | `prd.md` |
| `03-requirements/` | Software requirements and use cases | `use-cases.md`, `UC-001-*.md` through `UC-009-*.md`, `functional-requirements.md`, `non-functional-requirements.md`, `permissions-matrix.md` |
| `04-architecture/` | Architecture and technical decisions | `architecture.md`, `adr/ADR-001-*.md` through `ADR-007-*.md` |
| `05-api/` | API contracts and OpenAPI | `api-contract.md`, `api-overview.md`, `error-codes.md` |
| `06-database/` | Schema, ERD, and data dictionary | `db-schema.md`, `erd.md` |
| `07-flows/` | Business flows, state machines | `state-machine.md` |
| `08-ui-ux/` | UI/UX design and screen catalog | `screen-list.md`, `design-system.md` |
| `09-testing/` | QA and testing documentation | `test-plan.md`, `test-cases.md`, `rtm.md` |
| `10-deployment/` | Deployment, CI/CD, release | `deployment-guide.md`, `ci-cd.md`, `rollback-plan.md` |
| `11-operations/` | Operations and monitoring | `monitoring-guide.md` |
| `12-handover/` | Project summary and deliverables | `project-summary.md`, `final-deliverables.md` |

---

## Cross-Cutting References

- [UI/API Traceability Matrix](../ui_api_traceability_matrix.md) — SCR → UC → API → FR → BR → TC
- [Screen Design Images](../screen-design/) — 25 annotated screenshots

---

## Change Log
| Version | Date | Author | Change |
|---|---|---|---|
| 2.0 | 2026-06-07 | Agent | Initial creation replacing `00_template_usage_guide.md` |
