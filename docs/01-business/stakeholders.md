# Stakeholders

> Project: HOSP-AI-001 — AI Hospital Knowledge Assistant  
> Version: 1.0  
> Owner: Product Owner  
> Last Updated: 2026-06-14  
> Status: Approved  

## Stakeholder List

| ID | Name/Group | Type | Responsibility |
|----|------------|------|----------------|
| SH-001 | Product Owner | Internal | Product vision, feature prioritization, acceptance sign-off |
| SH-002 | System Architect | Internal | Architecture design, ADRs, technical standards |
| SH-003 | Backend Team | Internal | FastAPI development, API design, database |
| SH-004 | Frontend Team | Internal | Next.js UI, component library, UX |
| SH-005 | QA Team | Internal | Test planning, execution, defect tracking |
| SH-006 | DevOps Team | Internal | CI/CD, deployment, monitoring, infrastructure |
| SH-007 | Security Team | Internal | Security architecture, HIPAA compliance, audit |
| SH-008 | Clinical SMEs | External | Clinical domain expertise, UAT validation |
| SH-009 | Hospital IT Admin | External | Infrastructure, network, deployment approval |
| SH-010 | End Users (Clinicians) | External | Daily AI copilot use for patient care |

## RACI Matrix

| Activity | Responsible | Accountable | Consulted | Informed |
|----------|-------------|-------------|-----------|----------|
| Business requirements | Product Owner | Sponsor | Clinical SMEs | All |
| Architecture decisions | System Architect | Tech Lead | Dev leads | Product Owner |
| API design | Backend Lead | System Architect | Frontend Lead | QA Lead |
| Database design | Backend Lead | System Architect | DevOps Lead | QA Lead |
| UI/UX design | Frontend Lead | Product Owner | Clinical SMEs | Backend Lead |
| Security compliance | Security Lead | System Architect | DevOps Lead | Product Owner |
| Test strategy | QA Lead | Product Owner | Dev leads | DevOps Lead |
| Release approval | Product Owner | Sponsor | Tech + QA Lead | All |
| Production deployment | DevOps Lead | Tech Lead | Security Lead | Product Owner |
| HIPAA audit | Security Lead | Product Owner | DevOps Lead | Hospital IT |

## Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-06-14 | Agent | Created stakeholder list + RACI matrix |
