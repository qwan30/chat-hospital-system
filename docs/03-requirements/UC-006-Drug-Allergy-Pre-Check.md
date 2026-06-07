# UC-006: Drug/Allergy Pre-Check

## Metadata
- **ID:** UC-006
- **Bounded Context:** Clinical Safety
- **Related BR:** BR-007
- **Status:** draft
- **Owner:** Product Owner
- **Last updated:** 2026-06-07

## Actor
Doctor, Pharmacist

## Trigger
User navigates to patient medication review or requests drug/allergy check.

## Preconditions
- User is authenticated with Doctor or Pharmacist role
- User has treatment relationship with the patient
- Patient has medication and allergy data in HMS

## Main Flow
1. User navigates to patient medication review (SCR-008)
2. System retrieves current medications from HMS
3. System retrieves known allergies from HMS
4. System cross-references medications against allergy records
5. System checks basic drug interaction rules
6. System displays warnings with severity, rule explanation, and evidence source
7. User reviews warnings and acknowledges/dismisses

## Alternative Flows
- **3a. No allergy data:** Patient has no recorded allergies → System shows "No allergies recorded" + warning that allergy data may be incomplete
- **5a. No interactions found:** All medications are safe → System shows "No conflicts detected"
- **6a. Pharmacist-only warnings:** Some warnings visible only to Pharmacist role → Doctor sees high-severity only

## Exceptions
- **E1. HMS medication data unavailable:** Cannot retrieve medications → Show error + suggest checking HMS directly
- **E2. Drug interaction DB unavailable:** Cannot perform check → Show warning "Interaction check unavailable" + display raw medication list

## Postconditions
- Drug/allergy warnings are displayed (if any)
- Audit event created for medication safety check

## Acceptance Criteria

### AC-1: Known allergy conflict detected
**Given:** Patient P1 has allergy to Penicillin and current medication includes Amoxicillin  
**When:** Medication review is opened  
**Then:** Warning is displayed with severity "High", explanation "Amoxicillin is a penicillin-type antibiotic"  
**And:** Warning cites allergy record as evidence source  

### AC-2: No conflicts returns clean result
**Given:** Patient P2 has no allergy conflicts with current medications  
**When:** Medication review is opened  
**Then:** "No conflicts detected" message is displayed  
**And:** Medication list is shown without warnings  

## Dependencies
- **Upstream UC:** UC-001 (patient context selection)
- **Downstream UC:** None
- **External Systems:** HMS REST API (medications, allergies)

## Notes
Phase 2 feature — requires drug interaction knowledge base. MVP may use simplified rule set.

## History
- v1 (2026-04-27, Original): Basic use case
- v2 (2026-06-07, Agent): Full template with 2 ACs
