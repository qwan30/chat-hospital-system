# Portfolio Hardening Discovery

## Current Repo Reality

- Backend prefixes routes through `app/backend/src/hospital_ai/api/router.py` under `Settings.api_v1_prefix`.
- Patients are exposed at `GET /patients/search`, returning `{items}`.
- Audit logs are exposed at `GET /audit/logs`, with `/audit/events` kept as an alias.
- Documents support `POST /documents`, `GET /documents/{document_id}`, page reads, retry, and search. There is no permission-filtered `GET /documents` list endpoint yet.
- Frontend `api-client.ts` still calls `/patients`, `/documents/upload`, and `/audit`, and expects arrays for list responses.
- Frontend settings page uses same-origin `/api/v1/settings` instead of configured `apiUrl`.
- `AuthProvider` persists both API URL and bearer token in `localStorage`.
- Settings routes authenticate but do not enforce admin/security role policy.
- HMS sync routes authenticate but do not check records/admin role or patient upload scope before writing HMS-derived documents.

## Impact Analysis

- `apiFetch`: CRITICAL; 11 direct API wrappers and 11 frontend flows depend on it. Avoid global behavior changes.
- `listDocuments`: HIGH; direct callers are Admin, Documents, and Metrics pages. Preserve `DocumentItem[]` return type.
- `listAuditLogs`: HIGH; direct callers are Admin, Metrics, and Audit pages. Preserve `AuditEntry[]` return type.
- `listPatients`: LOW; direct callers are Admin and Documents pages.
- `uploadDocument`: LOW; direct caller is Documents upload handler.
- `AuthProvider`: LOW by GitNexus.
- Settings handlers: LOW by GitNexus.
- HMS sync service methods: LOW by GitNexus; direct route callers only.

## Verification Targets

- Backend route/security tests for document listing, settings role policy, HMS sync denial audit, metrics summary, and contract route matching.
- Frontend workspace check and static token-storage check.
- Existing backend and frontend gates where practical in the current workspace.

