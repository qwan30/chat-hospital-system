# BR-005: Impact Metrics Tracking

## Metadata
- **ID:** BR-005
- **Status:** approved
- **Owner:** PM / Product Owner
- **Stakeholders:** Sponsor, Admin, QA Lead
- **Priority:** Must
- **Target Quarter:** MVP

## Background
The project needs to demonstrate measurable ROI to justify continued investment. Without metrics, it's impossible to prove the AI assistant saves time and reduces costs compared to manual workflows.

## Goal
System logs metrics for time saved, cost savings, and quality indicators, displayed in a dashboard.

## Success Metrics
- Metrics dashboard shows before/after workflow data: functional in MVP
- Every AI query creates a metric event: 100%
- Cost saving estimate is calculable: formula implemented

## In Scope
- Metric event creation for every AI workflow
- Time saved calculation (baseline manual time vs actual AI time)
- Cost saved calculation (time saved × hourly cost)
- Metrics dashboard with filtering and time series
- Citation rate, retrieval quality, and safe refusal rate tracking

## Out of Scope
- Real-time cost accounting integration
- Benchmarking against other hospitals
- Staff performance scoring

## Related Use Cases
- UC-009: View Impact Metrics

## Constraints
- **Technical:** Metric events must be de-identified where possible
- **Privacy:** No PHI in metric aggregations
- **Baseline:** Manual baseline values are estimates until validated

## Open Questions
- [ ] What is the average staff hourly cost for cost saving calculations?
- [ ] Should metrics be visible to all staff or restricted to PM/Admin?

## History
- v1 (2026-04-27, Original): Initial draft
- v2 (2026-06-07, Agent): Extracted to individual file
