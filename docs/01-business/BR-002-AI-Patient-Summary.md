# BR-002: AI Patient Summary

## Metadata
- **ID:** BR-002
- **Status:** approved
- **Owner:** Product Owner
- **Stakeholders:** Doctor, Nurse, QA Lead
- **Priority:** Must
- **Target Quarter:** MVP

## Background
Doctors reviewing patient cases spend 10–15 minutes collecting information from multiple systems. A structured, cited AI summary can reduce this to under 30 seconds while maintaining traceability to source data.

## Goal
System generates a comprehensive patient summary including history, medications, allergies, labs, and citations to source records.

## Success Metrics
- Summary includes all required sections (history, meds, allergies, labs): 100% on MVP dataset
- Summary includes source references for each section: ≥95%
- Generation latency: <30 sec on MVP dataset

## In Scope
- Aggregated patient summary from HMS structured data
- Citation to source records (encounters, medications, allergies, labs, documents)
- Streaming generation with progress indicator
- Summary refresh on demand

## Out of Scope
- Clinical interpretation or recommendation
- Summary across multiple patients
- Historical summary comparison (trend analysis)

## Related Use Cases
- UC-002: Generate Patient Summary

## Constraints
- **Technical:** Summary must be generated from authorized data only
- **Privacy:** Summary content is PHI — same access controls as source data
- **Performance:** Must complete within 30 sec on MVP dataset

## Open Questions
- [ ] Should summary include document-sourced data (OCR chunks) or only structured data?
- [ ] What sections are required vs optional for different roles?

## History
- v1 (2026-04-27, Original): Initial draft
- v2 (2026-06-07, Agent): Extracted to individual file
