# BR-007: Drug/Allergy Conflict Warning

## Metadata
- **ID:** BR-007
- **Status:** draft
- **Owner:** Product Owner
- **Stakeholders:** Doctor, Pharmacist, QA Lead
- **Priority:** Should (Phase 2)
- **Target Quarter:** Post-MVP

## Background
Medication errors are a leading cause of adverse events in hospitals. Pharmacists and doctors need automated assistance to cross-check current medications against known allergies and drug interactions, with evidence sources clearly cited.

## Goal
System can flag potential drug/allergy conflicts with warning messages that include source and rule explanation.

## Success Metrics
- Known drug/allergy conflicts are detected: ≥90% on test dataset
- Warning includes evidence citation: 100%
- False positive rate: <20%

## In Scope
- Cross-reference current medications with allergy records
- Drug interaction database lookup (basic rules)
- Warning with severity, source, and rule explanation
- Integration with patient medication review screen

## Out of Scope
- Full pharmacovigilance system
- Real-time prescription interception
- Drug dosing recommendations
- Regulatory approval for clinical decision support

## Related Use Cases
- UC-006: Drug/Allergy Pre-Check

## Constraints
- **Technical:** Requires complete medication and allergy data from HMS
- **Regulatory:** AI output is advisory only — clinician must verify
- **Data:** Drug interaction rules need a curated knowledge base

## Open Questions
- [ ] What drug interaction database/rules should be used?
- [ ] Should warnings be blocking (prevent action) or informational?
- [ ] How should severity levels be classified?

## History
- v1 (2026-04-27, Original): Initial draft
- v2 (2026-06-07, Agent): Extracted to individual file
