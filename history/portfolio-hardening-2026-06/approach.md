# Portfolio Hardening Approach

## Work Shape

Direct standard slice. The previous plan is broad, but repo discovery shows several high-value contract/security fixes are localized and testable. Implement those first and leave larger RAG/browser/portfolio expansion as follow-up if gates remain green.

## Implementation Plan

1. Patch frontend API client wrappers:
   - `listPatients` -> `/patients/search` and unwrap `{items}`.
   - `listDocuments` -> `/documents` and unwrap `{items}`.
   - `uploadDocument` -> `POST /documents` with `patient_id`, `title`, `document_type`, and `file`.
   - `listAuditLogs` -> `/audit/logs` and unwrap `{items}`.
   - add `getMetricsSummary` for `/feedback/metrics/summary`.
2. Patch frontend auth/settings:
   - persist API URL only;
   - keep bearer token in React state only;
   - settings page uses configured `apiUrl` and bearer token.
3. Patch backend:
   - add permission-filtered `GET /documents` returning `{items}`;
   - add role guard helpers to settings;
   - require upload permission for HMS sync routes before writes;
   - keep denial auditing through `PermissionService`.
4. Add focused tests/scripts/docs:
   - backend API tests for new route/security behavior;
   - frontend workspace contract test for no token persistence and route paths;
   - update evidence/report docs with verified scope only.

## Risks

- `apiFetch`, `listDocuments`, and `listAuditLogs` are high/critical blast-radius areas. Keep return types unchanged for callers.
- Existing tests often exercise services directly instead of ASGI routes. Add API-level tests only where route behavior matters.
- The broad plan includes browser screenshots and full RAG eval. Treat those as follow-up unless implementation remains small enough after core gates.

