# API UAT Summary

Generated: 2026-04-28T17:14:32.970933+00:00
Evidence JSON: `api-evidence.json`

| Scenario | Severity if failed | Result | Evidence |
|---|---|---|---|
| auth and no-token boundary | P1 block | PASS | `auth-anonymous`, `auth-wrong-token`, `auth-dev-doctor`, `auth-dev-records`, `auth-dev-security`, `auth-dev-admin` |
| general knowledge thread answer | P2 fix before sign-off | PASS | `general-thread-create`, `general-thread-message` |
| HMS appointment import role boundary | P1 block | PASS | `hms-import-records`, `hms-import-doctor-denied` |
| doctor patient-linked HMS appointment answer | P1 block | PASS | `patient-thread-create`, `patient-thread-message` |
| denied patient access and audit trace | P1 block | PASS | `records-patient-thread-denied`, `security-audit-events`, `doctor-audit-denied` |
| shared thread rename, share, reload, archive | P2 fix before sign-off | PASS | `shared-thread-create`, `shared-thread-rename`, `shared-thread-share-admin`, `shared-thread-admin-reload`, `shared-thread-archive`, `shared-thread-archived-detail` |

## Details

### auth and no-token boundary

- Expected: Known dev tokens resolve to seeded users; no token and wrong token are blocked without PHI.
- Actual: All seeded tokens authenticated; anonymous and wrong-token requests returned 401.
- Severity if failed: P1 block

### general knowledge thread answer

- Expected: A general thread answers from approved non-PHI evidence with no patient_id.
- Actual: General thread returned an approved non-PHI citation and no patient context.
- Severity if failed: P2 fix before sign-off

### HMS appointment import role boundary

- Expected: Records staff or admin can import appointment summaries; doctor import is denied.
- Actual: Records import succeeded with appointments lineage; doctor import was denied.
- Severity if failed: P1 block

### doctor patient-linked HMS appointment answer

- Expected: Doctor asks about Alice and receives appointment evidence with source_family appointments.
- Actual: Doctor answer cited HMS appointment evidence with source_family appointments.
- Severity if failed: P1 block

### denied patient access and audit trace

- Expected: A role without Alice read access is denied before evidence; security can review denial logs.
- Actual: Records access was denied, and security could review a denied audit event.
- Severity if failed: P1 block

### shared thread rename, share, reload, archive

- Expected: Doctor can rename/share/archive a thread; admin sees shared persisted thread after reload.
- Actual: Rename, share, reload, and archive all persisted through backend APIs.
- Severity if failed: P2 fix before sign-off
