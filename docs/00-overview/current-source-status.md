# Current Source Status

## Stack Overview
- **Backend:** FastAPI (Python 3.12), SQLAlchemy (async), Uvicorn, PostgreSQL/SQLite (aiosqlite), Alembic, Pytest (262 tests).
- **Frontend:** TanStack Start, React 19, Vite 8, Bun, Tailwind CSS v4, shadcn/ui. Dev on port **8082**.
- **Testing:** Pytest (Backend), Playwright & Vitest (Frontend), 27-test DevTools audit suite.
- **API Client:** Relative `/api` base URL → Vite proxy → `http://localhost:8000/api/v1`. (Fixed CORS issue — previously used absolute `localhost:8000`.)
- **Core Integrations:** RAG with permission-filtered chunks, GraphRAG with PostgreSQL, JWT-based Authentication.
- **RBAC:** `/settings` is **admin-only** (enforced in `rbac.ts` ADMIN_ONLY list).

## Route Inventory & Feature Status
### Backend Routes (`/api`)
- `/auth/me` - **Active** (JWT + dev bearer tokens)
- `/chat` & `/chat/stream` - **Active** (Streaming chat, SSE, citation tracking)
- `/documents` - **Active** (Upload, hybrid search, page metadata)
- `/patients` - **Active** (Patient access control)
- `/access-requests` - **Active** (Pending review workflows)
- `/audit` - **Active** (Event logging for PHI access)
- `/dashboard/summary` - **Active**
- `/search/global` - **Active** (Role-aware hybrid search)
- `/settings` - **Active** (Admin-only: GET requires admin/security, PUT requires admin)
- `/graph/patients/$patientId` - **Active** (Knowledge graph visualization)

### Frontend Routes
- `/_app.chat.index` - **Active** (Global chat, contextual suggestion)
- `/_app.patients.$patientId` - **Active** (Patient details)
- `/_app.documents.$documentId` - **Active** (Document previews & citations)
- `/_app.access-requests` - **Active** (Approval reviews)
- `/_app.audit` - **Active** (Audit logs)
- `/_app.settings` - **Active** (Admin-only system settings)
- `/_app.graph.patients.$patientId` - **Active** (Knowledge graph)
- `/error/*` - **Active** (15 error pages: forbidden, not-found, server, timeout, maintenance, etc.)

## Known Exceptions
- **PHI Redaction:** Unsupported redaction claims removed.
- **Role/Workspace Switching:** Requires full sign-out to change demo persona.
- **Synthetic RAG Adapter:** `rag_spike_adapter.py` planned for offline simulation.
- **E2E in CI:** Frontend E2E tests need backend service in CI pipeline (no backend running in `frontend-test` job).
- **Type annotation migration:** Backend files being converted from `X | None` → `Optional[X]` for Python 3.9 compat.

## Verification Status
- Backend test suite: 262 tests pass, lint green (ruff).
- Frontend: 27/27 DevTools audit pass, 135/147 E2E pass (12 need backend in CI).
- API contract verification: `verify_contracts.py` green.
- CORS fix: `DEFAULT_API_URL` changed to `/api` (relative, via Vite proxy).
- RBAC fix: `/settings` restricted to admin-only.
- Chat accessible to: cardiologist, hospitalist, rn, pharmacist (front_desk blocked).
- Graph accessible to: cardiologist, hospitalist (others blocked).
