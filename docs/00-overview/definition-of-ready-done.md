# Definition of Ready & Definition of Done

> Project: AI-Powered Hospital Knowledge Assistant  
> Project Code: HOSP-AI-001  
> Version: 2.0  
> Status: Draft  
> Owner: PM / PO / Tech Lead / QA  
> Last Updated: 2026-06-07  

---

## 1. Ready-to-Code Go / No-Go Checklist

Before starting any feature implementation sprint, the following mandatory gates must be verified:

| # | Ingress Gate Criteria | Evidence Verification Source | Status |
|---|---|---|---|
| **1** | Business scope and KPI metrics approved. | `docs/01-business/brd.md` | `[ ]` Pending |
| **2** | Process diagrams and use cases approved. | `docs/03-requirements/use-cases.md` | `[ ]` Pending |
| **3** | Feature requirements have clear acceptance criteria. | `docs/03-requirements/functional-requirements.md` | `[ ]` Pending |
| **4** | Security and privacy compliance targets confirmed. | `docs/04-architecture/security-architecture.md`| `[ ]` Pending |
| **5** | UX screen layouts and wireframes reviewed. | `docs/08-ui-ux/design-system.md` | `[ ]` Pending |
| **6** | System component architecture design approved. | `docs/04-architecture/architecture.md` | `[ ]` Pending |
| **7** | Database schema and API contracts approved. | `docs/06-database/db-schema.md` / `docs/05-api/` | `[ ]` Pending |
| **8** | Local Lite deployment configuration validated. | `docs/10-deployment/deployment-guide.md` | `[ ]` Pending |
| **9** | Master test plan and RTM mappings verified. | `docs/09-testing/test-plan.md` / `rtm.md` | `[ ]` Pending |
| **10**| Audit event schemas and metrics tracking defined. | `docs/11-operations/monitoring-guide.md` | `[ ]` Pending |
| **11**| Synthetic/de-identified testing dataset ready. | QA Test Fixtures | `[ ]` Pending |
| **12**| AI clinical disclaimer and safe refusals configured. | System prompt configurations | `[ ]` Pending |

---

## 2. Mandatory No-Go Triggers

If any of the following conditions exist, the sprint is halted (**NO-GO**):

- **No Permission Matrix**: Coding RAG features without explicit RBAC/ABAC rules defined.
- **No Citation Plan**: Generating AI responses that do not link back to vector chunk indexes.
- **No Audit Logs**: Launching API endpoints without active logging of query transactions.
- **PHI in Development**: Using real patient records in local development or QA environments.
- **Hardware Footprint Overage**: Attempting to deploy local models exceeding 16GB RAM constraints.
- **No Refusal Handlers**: Lack of system prompts/rules mapping to `INSUFFICIENT_EVIDENCE` states.

---

## 3. Allowed Conditional GO Exclusions

The following low-risk items may be deferred for subsequent sprint phases:
- Advanced UI/UX pixel polishing.
- Integration of a separate graph store database (Neo4j deferred to Phase 2).
- Integration of external OAuth/OIDC authentication providers (local dev auth accepted for MVP).

---

## 4. Definition of Done (DoD) Checklist

A feature card is marked **Done** and promoted to release when it satisfies:

1.  **Code Quality**: Passed lint checking (`black`, `ruff`, `eslint`); compiles without warnings.
2.  **Test Coverage**: Unit test coverage is ≥80%; all regression tests pass.
3.  **Traceability Matrix**: Use Case files, API endpoints, and test cases mapped in RTM.
4.  **Audit Logs**: Confirmed that all write operations and sensitive data reads generate audit events.
5.  **Metrics Integration**: Time and cost-saving metrics are logged correctly to analytics datastores.
6.  **Product Owner Sign-off**: UAT verification checklists completed.

---

## Change Log
| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-04-27 | Release Lead | Initial sprint go/no-go checklist |
| 2.0 | 2026-06-07 | Agent | Combined Go/No-Go and Definition of Done checklists into a unified overview document |
