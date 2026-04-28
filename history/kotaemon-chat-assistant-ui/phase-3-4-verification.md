# Phase 3/4 Verification - HMS Appointment Evidence And Release Hardening

**Date:** 2026-04-28
**Feature:** kotaemon-chat-assistant-ui
**Scope:** Phase 3 and Phase 4 execution

## Phase 3 Slice

The first HMS-backed data family is appointment summaries.

Source reference:
- `D:\projects\hospital-management-system\docs\API_ENDPOINTS_COMPREHENSIVE.md`
- `D:\projects\hospital-management-system\docs\HMS_SRS.md`
- `D:\projects\hospital-management-system\backend\controller\src\main\java\com\hospital\api\appointment\AppointmentController.java`
- `D:\projects\hospital-management-system\backend\domain\src\main\java\com\hospital\core\appointment\AppointmentEntity.java`

Implemented contract:
- `POST /api/v1/hms/appointments/import`
- Payload must include matching `patient_id` and `source_patient_id`.
- Records staff require patient upload scope; admins may import.
- Imported evidence is stored as `hms_appointment_summary` in `documents`, `document_pages`, and `document_chunks`.
- Metadata preserves `source_system`, `source_family`, `source_record_id`, `source_path`, `source_lifecycle_state`, `approval_state`, and `patient_permission_required`.

Excluded from import:
- CCCD
- phone
- email
- address
- insurance number
- booking contact identity fields
- live HMS database credentials or removed internal-assistant endpoints

## Safety Checks

Automated coverage now proves:

- Imported HMS appointment evidence can be cited in a patient-linked thread after patient read permission.
- Non-records/non-admin users cannot import HMS appointment evidence.
- Mismatched HMS patient ownership is rejected before indexing.
- Revoked patient permission blocks HMS appointment evidence before chat query/message creation.
- Deleted or archived HMS-derived source documents are excluded from retrieval.
- Invalid generated citations do not commit orphaned chat messages.
- Frontend tokens are memory-only and are not read from or written to localStorage.
- Thread summaries load before selected-thread details, so one failed detail request does not hide all accessible threads.
- Raw backend error details are not rendered in the browser.
- Inert sidebar/evidence controls were removed.

## Seeded UAT Scenario

1. `cd app/backend`
2. `alembic upgrade head`
3. `python scripts/seed_dev.py`
4. Start the backend and frontend.
5. In the frontend, enter backend URL `http://localhost:8000` and bearer token `dev-doctor`.
6. Create or open Alice's patient-linked thread.
7. Ask: `What is the appointment status and vital signs?`
8. Expected: answer cites HMS appointment evidence with source family `appointments`.
9. Remove or expire Alice read permission for `dev-doctor`.
10. Ask the same question again.
11. Expected: patient-linked answer is denied before evidence reaches the LLM context.

## Verification Commands

```bash
cd app/backend
python -m compileall src tests
python -m pytest

cd app/frontend
npm run test:workspace
npm run typecheck
npm run lint
npm run build
```

Latest result:
- Backend compile passed.
- Backend tests: 55 passed, 2 skipped.
- Frontend workspace tests: 16 passed.
- Frontend typecheck, lint, and build passed.
- Playwright loaded `http://localhost:3000` after clearing browser storage with no console warnings or errors.

## Remaining Non-Blocking Follow-Up

`br-2o5` remains open: move approved general knowledge sources behind a provider or repository boundary. It is not part of the HMS appointment slice, but should be handled before large source expansion.
