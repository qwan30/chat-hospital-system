# BR-004: Permission-Aware Retrieval

## Metadata
- **ID:** BR-004
- **Status:** approved
- **Owner:** Security/Compliance
- **Stakeholders:** Hospital IT, Doctor, Nurse, QA Lead
- **Priority:** Must
- **Target Quarter:** MVP

## Background
Hospital data is highly sensitive (PHI). Staff must only access patients they have a treatment relationship with. The AI system must enforce permission checks before any patient data reaches the LLM context, preventing both unauthorized access and unauthorized AI-generated answers.

## Goal
System enforces permission-aware retrieval: unauthorized context never reaches the LLM, and every denied access is audited.

## Success Metrics
- Unauthorized chunks passed to LLM: 0 (zero tolerance)
- Unauthorized patient access attempts are blocked: 100%
- Every blocked access creates audit event: 100%

## In Scope
- RBAC (role-based access control) for feature-level permissions
- ABAC (attribute-based access control) for patient-level scope
- Permission filters applied before vector/graph retrieval
- Access denied state with clear user feedback
- Clinical justification request workflow for emergency access
- Audit trail for all permission checks

## Out of Scope
- Self-service role management by end users
- Cross-hospital access federation
- Break-the-glass emergency override (deferred to Phase 2)

## Related Use Cases
- UC-001: Ask Patient Question (permission check is precondition)
- UC-002: Generate Patient Summary (requires patient access)
- UC-008: Review Audit Logs

## Constraints
- **Technical:** Permission check must happen before retrieval, not after
- **Regulatory:** Must comply with hospital access policies
- **Audit:** Every permission decision must be logged with trace ID

## Open Questions
- [ ] What roles are required for MVP? (Q-002 from PRD)
- [ ] Should clinical justification requests require admin approval or auto-approve?

## History
- v1 (2026-04-27, Original): Initial draft
- v2 (2026-06-07, Agent): Extracted with expanded ABAC and audit requirements
