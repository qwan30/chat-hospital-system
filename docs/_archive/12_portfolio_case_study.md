# Portfolio Case Study: Privacy-Aware Hospital Knowledge Assistant

## Positioning

This project is best presented as a full-stack/backend AI engineering MVP, not as a production hospital system. The strongest angle is the engineering of a permission-filtered RAG assistant with citation validation, audit evidence, HMS data import/sync, and frontend workflows that expose those controls.

Safe one-line summary:

> Built a privacy-aware hospital knowledge assistant MVP with FastAPI, Next.js, permission-filtered RAG, citation validation, audit logs, HMS evidence import, and verified backend/frontend contract tests using synthetic data.

Avoid claims of HIPAA compliance, production deployment, real hospital users, or measured ROI unless separate evidence is added.

## Problem

Hospital staff often need to search across policies, clinical documents, appointments, lab results, and patient notes. A naive chatbot is unsafe in this domain because it may retrieve unauthorized patient chunks, hallucinate citations, or leave no audit trail.

The project targets a safer workflow:

- filter patient permissions before retrieval context reaches the LLM;
- return cited answers only when evidence supports them;
- refuse safely when evidence is missing;
- record allowed and denied sensitive actions for review;
- keep local/dev auth honest without pretending it is production identity management.

## Architecture

| Layer | Implementation | Evidence |
|---|---|---|
| Frontend | Next.js App Router, React, TypeScript, chat/documents/audit/metrics/settings pages | `app/frontend/src/app`, `app/frontend/src/components` |
| API | FastAPI route modules under `/api/v1` | `app/backend/src/hospital_ai/api/routes` |
| Data | SQLAlchemy async models, Alembic migrations, PostgreSQL/pgvector target, SQLite test mode | `app/backend/src/hospital_ai/db`, `app/backend/alembic` |
| RAG | Permission-filtered retrieval, citation validation, safe refusal, streaming validation | `services/retrieval.py`, `services/chat.py`, `api/routes/chat_stream.py` |
| Documents | Upload, page/chunk storage, worker indexing, retry/failure states | `api/routes/documents.py`, `workers/jobs.py` |
| HMS | Appointment import and HMS sync into citeable evidence documents | `api/routes/hms.py`, `services/hms_appointments.py`, `services/hms_sync.py` |
| Audit/Metrics | Audit logs, user feedback, metric events, summary dashboard | `api/routes/audit.py`, `api/routes/feedback.py`, `services/metrics.py` |

## Security Model

The security story is "privacy-aware MVP controls," not formal compliance.

Implemented controls:

- active patient permission predicates include user, patient, scope, soft-delete, and expiry checks;
- RAG retrieval filters permissions before evidence reaches answer generation;
- document listing is permission-filtered and returns `{items}`;
- HMS sync writes require records/admin authority and patient upload scope where applicable;
- settings reads are admin/security only; settings writes are admin-only;
- denied HMS/settings attempts create audit events;
- frontend login keeps bearer tokens in React memory only and persists only the API URL.

Known limits:

- production OIDC/session handling is not implemented;
- no formal HIPAA/SOC2 audit has been performed;
- no real patient data or real clinician usage is included.

## Portfolio Hardening Completed On 2026-06-07

| Area | Change | Verification |
|---|---|---|
| API contracts | Frontend now uses `/patients/search`, `GET /documents`, `POST /documents`, `/audit/logs`, and `/feedback/metrics/summary`. | `python scripts/verify_contracts.py` |
| Document list | Added `GET /documents?patient_id=&status=&limit=` returning `{items}` with patient-scope filtering. | `test_document_list_is_permission_filtered_and_returns_items` |
| Token handling | Removed bearer-token persistence from `localStorage`; API URL persistence remains. | `npm.cmd run test:workspace`, static grep |
| Settings permissions | Admin/security can read settings; only admin can write; denied write is audited. | `test_settings_read_write_role_policy_and_denial_audit` |
| HMS sync permissions | Sync routes require upload/admin permission before writes. | `test_doctor_hms_sync_full_is_denied_and_audited` |
| Metrics | Metrics dashboard now consumes `/feedback/metrics/summary` and shows denied audit count. | `test_metrics_summary_includes_audit_denial_count` |
| RAG proof | Added deterministic synthetic eval for no-evidence, cited answer, denied patient, HMS appointment, general knowledge, and graph relation cases. | `python scripts/run_rag_eval.py` |

## Verified Local Results

Latest local checks from this hardening pass:

| Command | Result |
|---|---|
| `python -m pytest -q` in `app/backend` | `250 passed, 2 skipped, 1 warning` |
| `python -m compileall src tests scripts -q` in `app/backend` | Passed |
| `python scripts/verify_contracts.py` in `app/backend` | Passed |
| `python scripts/run_rag_eval.py` in `app/backend` | `6/6` synthetic cases passed; report in `history/portfolio-hardening-2026-06/rag-eval-report.md` |
| `python scripts/uat_product_api_check.py --base-url http://127.0.0.1:8000` in `app/backend` | Passed against a temporary SQLite-backed local API; report in `history/portfolio-hardening-2026-06/api-uat/20260607T110018Z/api-uat-summary.md` |
| `npm.cmd run test:workspace` in `app/frontend` | `18` checks passed |
| `npm.cmd run typecheck`, `npm.cmd run lint`, `npm.cmd run build` in `app/frontend` | Passed |
| Browser smoke screenshots | Login page captured at desktop and mobile sizes in `history/portfolio-hardening-2026-06/screenshots/` |

Fresh authenticated workflow screenshots and human demo sign-off are still recommended before final publication.

## Safe CV Bullets

- Built a full-stack hospital knowledge assistant MVP with FastAPI, Next.js, SQLAlchemy, PostgreSQL/pgvector-ready retrieval, and synthetic/de-identified clinical workflows.
- Implemented permission-filtered RAG so patient evidence is filtered by active scope before it can be passed to answer generation.
- Added citation validation, safe-refusal behavior, and audit trails for patient-grounded AI answers.
- Integrated document upload/indexing and HMS appointment/sync data as citeable evidence sources.
- Hardened frontend/backend contracts with route verification, memory-only bearer-token handling, admin-only settings writes, HMS sync permission checks, and regression tests.

## Limitations To Disclose

- No live production deployment URL has been verified.
- No real hospital users, clinical pilot, authenticated browser workflow refresh, or human UAT sign-off is available in the current artifact set.
- Business metrics are instrumented and demo-visible, but ROI/time-saved claims are estimates unless backed by a generated report or real usage data.
- RAG evaluation now has a synthetic local report; do not generalize its `100%` synthetic result to real hospital data or production performance.
