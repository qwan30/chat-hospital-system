# Manual Test & UAT Checklist

> Project: AI Copilot for Hospital Management System (HMS)  
> Project Code: HOSP-AI-001  
> Version: 4.0  
> Status: Approved  
> Owner: QA Lead / Clinician SMEs  
> Last Updated: 2026-06-15  

---

## 1. User Acceptance Testing (UAT) Scenarios

The following high-level scenarios must be verified manually by designated clinician and administrative stakeholders before system release sign-off:

| UAT Scenario | Step-by-Step Verification Protocol | Designated SME | Sign-off Status |
|---|---|---|---|
| **Clinician Patient Summary Verification** | 1. Log in as a Doctor (`SCR-001`).<br>2. Select patient with known history (`SCR-006`).<br>3. Verify that the Patient Overview screen calls `GET /patients/{id}/overview` to load the snapshot and cached AI summary.<br>4. Click on the Penicillin allergy citation chip (`SCR-014`).<br>5. Check that the side panel viewer opens and correctly displays the cited EMR allergy record row (`SCR-019`). | Attending Physician / MD | `[ ]` Unsigned |
| **Justification Override Workflow** | 1. Log in as a Nurse (`SCR-001`).<br>2. Attempt to select a patient admitted to a different department (`SCR-006`).<br>3. Verify the screen redirects to "Access Denied" (`SCR-021`).<br>4. Click "Request Temporary Access" to open the justification modal (`SCR-022`).<br>5. Submit a valid consultation note and select "High Urgency".<br>6. Check that the request submits successfully and refreshes the EMR scope on approval. | Consult Nurse / RN | `[ ]` Unsigned |
| **Scanned Record OCR Ingestion** | 1. Log in as Records Staff.<br>2. Open Document Dashboard (`SCR-015`) and drag three scanned PDF lab printouts into the Batch Upload modal (`SCR-017`).<br>3. Track processing progress. If a file displays "Needs Review", open the OCR Review screen (`SCR-016`) and check low-confidence text highlights.<br>4. Correct text boxes and click "Approve Index".<br>5. Execute global semantic search (`SCR-020`) and verify the document page returns with text highlights. | Records Clerk / Admin | `[ ]` Unsigned |
| **Pharmacist Medication Safety Check** | 1. Log in as a Pharmacist.<br>2. Select patient with Penicillin allergy.<br>3. Open Medication Review screen (`SCR-008`).<br>4. Run drug safety precheck for "Amoxicillin" prescription.<br>5. Verify that a High-severity warning pops up citing the patient's Penicillin allergy as the conflict source. | Clinical Pharmacist | `[ ]` Unsigned |
| **Security Log Audit Trail** | 1. Log in as Security Auditor.<br>2. Open Audit Event logs page (`SCR-023`).<br>3. Perform patient data queries using a test Doctor account.<br>4. Refresh the audit log screen and verify that each query has created a SUCCESS record detailing the user ID, patient ID, and trace ID. | Chief Information Security Officer | `[ ]` Unsigned |
| **Management ROI Productivity Review** | 1. Log in as Project Manager (PM).<br>2. Open productivity dashboard (`SCR-024`).<br>3. Verify that time saved and cost savings are recalculated and incremented in dashboard graphs. | Product Owner / PM | `[ ]` Unsigned |

---

## 2. Automated E2E Coverage (Reduced Manual Burden)

The following UAT scenarios are now partially or fully covered by automated E2E real-user interaction tests (`app/frontend/e2e/flows/`). Manual verification is still recommended for final sign-off, but regression testing is automated:

| UAT Scenario | Automated Coverage | E2E Suite | Status |
|---|---|---|---|
| Clinician Patient Summary — login + patient selection | Login flow + patient navigation | `login-flow`, `patient-flow` | ✅ Automated |
| Justification Override — access denied + request button | Access denied page + request button | `patient-flow` | ✅ Automated |
| Pharmacist Medication Safety — start review | Medication review page + start button | `patient-flow` | ✅ Automated |
| Security Log Audit — page load | Audit page loads via sidebar | `navigation-flow` | ✅ Automated |
| Management ROI Dashboard — page load | Dashboard via sidebar + direct URL | `navigation-flow` | ✅ Automated |

> **Note (2026-06-15)**: 56 automated E2E tests run at 100% pass rate. See `test-plan.md` §5 for details.

---

## Change Log
| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-04-27 | QA Lead | Initial manual UAT scenarios |
| 2.0 | 2026-06-07 | Agent | Restructured into checklists |
| 3.0 | 2026-06-07 | Agent | Realigned verification scenarios to BFF endpoints and access justification workflows |
| 4.0 | 2026-06-15 | Agent | Added automated E2E coverage mapping; 5/6 UAT scenarios now have automated regression tests |
