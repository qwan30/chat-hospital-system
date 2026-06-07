# Project Evidence Sheet

Project: AI-Powered Hospital Knowledge Assistant  
Repository: `D:\projects\chatbot-hospital-system`  
Public remote: `https://github.com/qwan30/chat-hospital-system`  
Target role lens: Full-stack Engineer  
Assumed personal role: Solo developer, USER-PROVIDED and supported by Git author history  
Audit date: 2026-06-07  
Source template: `evidence-sheet.md`

## 1. Executive Summary

| Field | Evidence-backed answer | Classification |
|---|---|---|
| What this project is | A full-stack hospital knowledge assistant with a FastAPI backend, Next.js frontend, permission-filtered RAG, citation handling, chat threads, document ingestion, HMS evidence import/sync, audit logs, and metrics surfaces. | VERIFIED |
| Problem it targets | Hospital staff need faster access to policy, clinical, patient, and operational knowledge while preventing unauthorized PHI exposure. | VERIFIED from docs |
| Primary users | Doctors, nurses, pharmacists, records staff, admin/IT, and product/project stakeholders. | VERIFIED from docs |
| Main stack | FastAPI, SQLAlchemy, Alembic, PostgreSQL/pgvector, Redis/RQ, Next.js 16, React 19, TypeScript, Tailwind CSS, shadcn-style UI, Vitest/TAP tests, Pytest. | VERIFIED |
| Current strongest evidence | Backend test suite passes `245 passed, 2 skipped`; frontend workspace tests pass `16` TAP tests; frontend typecheck, lint, and production build pass; Docker/GitHub Actions workflow files exist. | VERIFIED |
| Deployment status | Docker Compose and GitHub Actions workflows are configured, but no live deployment URL or successful CI run was verified in this audit. | VERIFIED plus MISSING |
| Adoption evidence | Public GitHub repo exists with 0 stars, 0 forks, 0 open issues, one public branch, and no open PR evidence. No user/adoption analytics found. | VERIFIED |
| Best resume angle | Full-stack security-conscious AI app: permission-first RAG, citation validation, audit trails, streaming chat, shared threads, document/HMS evidence ingestion, and tested backend/frontend contracts. | INFERRED |
| Main risk to avoid | Do not claim production deployment, real hospital adoption, measured time savings, HIPAA compliance, or token memory-only auth across the whole app without more proof. | VERIFIED |

Overall assessment: the repository has strong implementation and test evidence for a full-stack AI assistant demo/MVP. It does not yet have enough evidence for production impact, public adoption, audited compliance, or measured business outcomes.

## 2. Repository Inspection Summary

| Item | Evidence | Classification |
|---|---|---|
| Local path | `D:\projects\chatbot-hospital-system` | VERIFIED |
| Main documentation folder | `docs/`, numbered from `00_template_usage_guide.md` through `10_design_system_and_metrics.md` | VERIFIED |
| Application folder | `app/` | VERIFIED |
| Frontend app | `app/frontend` | VERIFIED |
| Backend app | `app/backend` | VERIFIED |
| Git remote | Local remote is `https://github.com/thanhquan3010/chat-hospital-system.git`; GitHub API resolves to `https://github.com/qwan30/chat-hospital-system`. | VERIFIED |
| GitHub repo visibility | Public API returned repository metadata successfully. | VERIFIED |
| GitHub stars/forks/issues | `stargazers_count=0`, `forks_count=0`, `open_issues_count=0`. | VERIFIED |
| Branches | GitHub API returned only `main`. | VERIFIED |
| Pull requests | GitHub API returned no PRs in the sampled public API query. | VERIFIED |
| Git authorship | `git shortlog -sne --all` returned `45 Thanh Quan <tranthanhquan09@gmail.com>`. | VERIFIED |
| Dirty worktree before report | `M app/frontend/next-env.d.ts`, `?? HIRING_SIGNALS_ANALYSIS.md`, `?? evidence-sheet.md`, `?? package-lock.json`. | VERIFIED |
| Workflow state | Khuym onboarding complete; existing Khuym handoff belongs to prior `kotaemon-chat-assistant-ui` UAT signoff and was not resumed. | VERIFIED |
| Tool limitation | `gkg` is not available on PATH; Khuym status also reported GKG server not reachable/project not indexed. | VERIFIED |

## 3. Technology Verification Matrix

| Technology / tool | Where verified | Role in project | Classification |
|---|---|---|---|
| Python | Backend package and tests under `app/backend` | Backend runtime and service layer | VERIFIED |
| FastAPI | `app/backend/src/hospital_ai/main.py`, API routers | HTTP API framework | VERIFIED |
| SQLAlchemy async ORM | `app/backend/src/hospital_ai/db/models.py`, services | Database models and async data access | VERIFIED |
| Alembic | `app/backend/alembic/versions/*.py` | Schema migrations | VERIFIED |
| PostgreSQL | Docker Compose, CI workflow, backend settings | Target relational database | VERIFIED as configured |
| pgvector | migrations and CI service image | Vector retrieval support | VERIFIED as configured |
| SQLite / aiosqlite | backend dev/test dependencies | Local tests and lightweight dev DB | VERIFIED |
| Redis/RQ | `workers/queue.py`, Docker Compose | Background document indexing queue | VERIFIED as implemented/configured |
| Next.js | `app/frontend/package.json`, build output | Frontend app router runtime | VERIFIED |
| React | `app/frontend/package.json`, component files | UI rendering | VERIFIED |
| TypeScript | frontend source and `npm run typecheck` | Frontend type safety | VERIFIED |
| Tailwind CSS v4 | frontend package and CSS usage | Styling system | VERIFIED |
| shadcn-style/Radix UI | frontend package and UI components | Component primitives | VERIFIED |
| Recharts | frontend package and metrics page code | Metrics visualization | VERIFIED |
| Motion | frontend package | UI animation support | VERIFIED |
| Pytest | backend test run | Backend verification | VERIFIED |
| Vitest/TAP-style workspace checks | `npm run test:workspace` | Frontend contract verification | VERIFIED |
| Docker Compose | root `docker-compose.yml`, backend compose | Local multi-service environment | VERIFIED as configured |
| GitHub Actions | `.github/workflows/*.yaml` | CI/build automation | VERIFIED as configured, not run live |
| PaddleOCR and file loaders | backend optional dependencies and loader modules | OCR/document ingestion | VERIFIED as code/config, not live OCR-tested here |
| Ollama/OpenAI provider hooks | backend config/service code | LLM provider integration | VERIFIED as code/config, no live provider test |
| Graph/RAG enrichment | migration `0006`, graph services/tests | Entity/relation enrichment | VERIFIED as code/test evidence |

## 4. Problem, Users, and Workflow Evidence

| Area | Evidence | Classification |
|---|---|---|
| Problem statement | Docs describe slow knowledge lookup, fragmented clinical/administrative information, and need for permission-safe answers. | VERIFIED |
| Users | PRD lists doctor, nurse, pharmacist, records staff, admin/IT, PM/PO personas. | VERIFIED |
| Core workflow | User authenticates with dev bearer token, selects/searches patient or uses general mode, submits question, backend retrieves permission-filtered evidence, answer returns citations and audit trace. | VERIFIED |
| Document workflow | Upload/ingest document, split pages/chunks, embed/index evidence, retrieve by permission and patient context. | VERIFIED in backend |
| HMS workflow | Import/sync HMS appointments, lab results, or records into indexed evidence with patient metadata and audit. | VERIFIED in backend |
| Shared thread workflow | Threads can be created, renamed, archived, shared, and constrained by patient permissions. | VERIFIED in backend/frontend/tests |
| Admin/settings workflow | Settings route and UI exist, but production-grade admin authorization is not fully proven. | VERIFIED plus MISSING |
| Metrics workflow | Backend records metric events and user feedback; frontend has metrics page. Measured real-world impact is not present. | VERIFIED plus MISSING |

## 5. Feature and Scope Inventory

| Feature | Evidence | Status | Classification |
|---|---|---|---|
| Authentication | Bearer-token dev auth and current-user dependency exist. Non-local default token map is guarded. | Implemented for local/dev | VERIFIED |
| Role and permission model | Role scopes and active patient permission filters exist. | Implemented and tested | VERIFIED |
| Permission-before-retrieval RAG | Retrieval queries join documents/chunks/pages and enforce active permission before evidence reaches the assistant. | Implemented and tested | VERIFIED |
| Citation validation | Chat service and streaming path validate citations and reject invalid evidence. | Implemented and tested | VERIFIED |
| Safe refusal | No-evidence/general-knowledge paths avoid unsupported patient claims. | Implemented and tested | VERIFIED |
| Streaming chat | SSE-style streaming endpoint buffers output for citation validation before final evidence emission. | Implemented and tested | VERIFIED |
| Chat threads | Persistent thread, participant, message, share/archive flows. | Implemented and tested | VERIFIED |
| General knowledge mode | Approved non-PHI source catalog for non-patient answers. | Implemented | VERIFIED |
| Document ingestion | Upload/indexing services, loaders, workers, retries, page/chunk storage. | Implemented | VERIFIED |
| OCR/file parsing | Composite loader supports text/PDF/docx/excel/html and OCR fallback hooks. | Implemented/configured | VERIFIED |
| HMS appointment import | Manual appointment evidence import with patient ownership and upload-scope checks. | Implemented and tested | VERIFIED |
| HMS sync | Appointment/lab-result/medical-record/full sync endpoints and service exist. | Implemented, but route-level permission strength needs review | VERIFIED plus MISSING |
| Audit logs | Access denial, query, document, and event audit paths exist. | Implemented and tested | VERIFIED |
| Metrics and feedback | MetricEvent/UserFeedback models, summary route, and frontend metrics screen exist. | Implemented | VERIFIED |
| Frontend chat workspace | Chat shell, thread sidebar, patient linking, streaming controls, evidence panel, runtime API config. | Implemented and tested | VERIFIED |
| Frontend document page | UI exists, but some frontend API paths do not match backend routes. | Partially implemented | CONTRADICTED |
| Frontend audit/metrics calls | UI exists, but `listAuditLogs` calls `/audit` while backend exposes `/audit/logs` and `/audit/events`. | Contract mismatch | CONTRADICTED |
| Frontend auth storage | Docs claim runtime token memory behavior in places, but app-wide login context stores token in localStorage. | Needs correction or scoping | CONTRADICTED |

## 6. Architecture and Design Decisions

| Decision | Evidence | Why it matters | Classification |
|---|---|---|---|
| FastAPI backend | `main.py`, routers, backend README | Clear Python API surface for RAG, documents, HMS, audit, settings. | VERIFIED |
| Next.js frontend | `app/frontend`, package scripts, App Router pages | Modern full-stack frontend with dashboard/chat/document surfaces. | VERIFIED |
| Permission-first retrieval | PermissionService and RetrievalService | Prevents unauthorized patient chunks from reaching answer generation. | VERIFIED |
| Citation-bound answers | ChatService and streaming validation | Supports traceability and reduces unsupported answer risk. | VERIFIED |
| Local-first/dev-safe defaults | config docs and deterministic/stub defaults | Lets the app run without external LLM dependencies during tests. | VERIFIED |
| PostgreSQL + pgvector | migrations, CI, compose | Supports structured clinical data plus vector search. | VERIFIED as configured |
| Hybrid retrieval | vector/BM25/RRF code and audit tests | Improves retrieval flexibility over vector-only search. | VERIFIED |
| Background indexing | Redis/RQ worker code | Separates upload API from expensive document processing. | VERIFIED as code/config |
| Graph enrichment | graph tables/services/tests | Adds patient-scoped entity/relation context to RAG. | VERIFIED |
| HMS as indexed evidence | HMS services and tests | Converts hospital-system records into citeable retrieval artifacts. | VERIFIED |
| Audit and metrics tables | migrations/services/routes | Creates evidence for permission checks, usage, latency estimates, and feedback. | VERIFIED |
| Docker/GitHub Actions | compose/workflows | Provides delivery path, though current CI/deploy run was not verified. | VERIFIED as configured |

## 7. Personal Contribution Analysis

| Claim | Evidence | Classification |
|---|---|---|
| User worked as solo developer | User selected "Solo developer"; Git shortlog shows one author with 45 commits. | USER-PROVIDED plus VERIFIED support |
| User likely implemented backend and frontend | Git history has one author across project; repository contains both backend and frontend implementation. | INFERRED |
| User likely owned architecture/docs/test strategy | Sprint 0 docs, code, tests, workflows, and Khuym history are in same repo with same author evidence. | INFERRED |
| Exact hours spent | No time logs or issue tracker estimates found. | MISSING |
| Team size beyond solo | No collaborator commit evidence found, but absence of commits is not proof no non-commit help existed. | MISSING |
| PR review or mentorship evidence | No public PRs found in GitHub API query. | MISSING |
| Production operations ownership | Docker/CI files exist, but no deployed environment or runbook execution was verified. | MISSING |

Resume-safe ownership wording should say "built" or "implemented" only if the user is comfortable confirming solo authorship. Avoid saying "led a team" or "collaborated across departments" unless external evidence is added.

## 8. Technical Challenges and How They Were Addressed

| Challenge | Evidence-backed handling | Classification |
|---|---|---|
| Preventing PHI leakage through RAG | Active patient permission filters are applied before chunk retrieval; denied accesses are audited; tests cover revoked/unauthorized patient access. | VERIFIED |
| Avoiding uncited hallucinated answers | Citation validation exists in both non-streaming and streaming flows; invalid citations reject answer persistence in tested paths. | VERIFIED |
| Supporting streaming without leaking unvalidated evidence | Streaming endpoint buffers generated output and validates citations before final evidence emission. | VERIFIED |
| Handling no-evidence scenarios | Service has safe refusal/no-evidence behavior and tests for general-mode isolation. | VERIFIED |
| Turning HMS records into RAG evidence | HMS import/sync services render records into documents/pages/chunks with source metadata and audit events. | VERIFIED |
| Document indexing reliability | Worker job tracks source hash, OCR/chunking/embedding stages, failure states, retries, and dead-letter queue config. | VERIFIED |
| Frontend contract stability | Workspace verification script checks thread state, streaming controls, safe errors, HMS citations, and canonical type literals. | VERIFIED |
| Frontend/backend route drift | Some non-chat pages call endpoint paths that do not match backend routes. | CONTRADICTED |
| Production authentication | Local/dev bearer token flow exists; production auth/session model is explicitly separate/pending in Khuym handoff. | MISSING |
| Live performance validation | Docs define targets, but no load test or real latency dataset was verified. | MISSING |

## 9. Existing Measurable Evidence

| Metric / result | Value | Source | Resume-safe? | Classification |
|---|---:|---|---|---|
| Backend pytest result | `245 passed, 2 skipped, 1 warning` | `python -m pytest -q` in `app/backend` | Yes, as test coverage evidence | VERIFIED |
| Backend compile check | Passed | `python -m compileall src tests scripts` | Yes | VERIFIED |
| Frontend workspace tests | `16` TAP tests passed | `npm run test:workspace` in `app/frontend` | Yes | VERIFIED |
| Frontend typecheck | Passed | `npm run typecheck` | Yes | VERIFIED |
| Frontend lint | Passed | `npm run lint` | Yes | VERIFIED |
| Frontend production build | Passed | `npm run build` | Yes | VERIFIED |
| Next build compile time | `7.8s` compile, TypeScript `23.5s` in this local run | Next.js build output | Only as local build evidence, not product performance | VERIFIED |
| Static pages generated | `11/11` | Next.js build output | Maybe, as app size context | VERIFIED |
| Backend route decorators | `34` | Static route scan | Yes, as scope count | VERIFIED |
| Alembic migrations | `6` | `app/backend/alembic/versions/*.py` | Yes | VERIFIED |
| Backend model classes in `db/models.py` | `13` listed model classes | Static inspection | Yes with exact scope | VERIFIED |
| Additional metric/feedback models | `MetricEvent`, `UserFeedback` in `services/metrics.py` and migration `0006` | Static inspection | Yes with caveat | VERIFIED |
| Frontend page files | `9` | Static file count | Yes with caveat | VERIFIED |
| Frontend component files | `16` | Static file count | Yes with caveat | VERIFIED |
| Public GitHub stars | `0` | GitHub API | No positive adoption claim | VERIFIED |
| Public GitHub forks | `0` | GitHub API | No positive adoption claim | VERIFIED |
| Public open issues | `0` | GitHub API | Neutral only | VERIFIED |
| Lookup time target | `<30 seconds` target | BRD/test plan docs | Not as achieved impact | USER-PROVIDED target |
| Citation rate target | `>=95%` target | BRD/test plan docs | Not as achieved impact | USER-PROVIDED target |
| Document review reduction | `~80%` target/assumption | docs | Not as achieved impact | USER-PROVIDED target |

No measured production latency, real user count, hospital deployment, dollars saved, or clinician time-savings dataset was found.

## 10. Engineering Scope Counts

| Scope item | Count | Counting rule | Classification |
|---|---:|---|---|
| Backend API route decorators | 34 | Static scan of `@router.get/post/patch/delete` in route files | VERIFIED |
| Alembic migrations | 6 | Files under `app/backend/alembic/versions` | VERIFIED |
| Backend pytest tests executed | 245 passed, 2 skipped | Pytest collection/result, includes parametrization | VERIFIED |
| Backend source/test/docs subset files | 72 | `git ls-files` subset for backend models/migrations/tests and frontend TS/TSX files | VERIFIED |
| Frontend App Router page files | 9 | Files named `page.tsx` under frontend app route tree | VERIFIED |
| Frontend component files | 16 | Static count under `app/frontend/src/components` | VERIFIED |
| Frontend workspace contract checks | 16 | TAP output from `npm run test:workspace` | VERIFIED |
| Git commits by main author | 45 | `git shortlog -sne --all` | VERIFIED |
| GitHub public branches | 1 | GitHub branches API | VERIFIED |

These counts are suitable for evidence inventory. They should not be inflated into claims like "enterprise-scale" or "production-grade" without operational proof.

## 11. Quality, Reliability, and Security Evidence

| Area | Evidence | Classification |
|---|---|---|
| Permission enforcement | Tests cover unauthorized patient blocked, revoked permission blocked, upload denial, and general-mode isolation. | VERIFIED |
| Auditability | AuditLog model, audit routes, denied-access audit tests, chat/audit trace tests. | VERIFIED |
| Citation safety | Tests cover invalid citation rejection and streaming citation validation. | VERIFIED |
| Dev token guard | Tests check committed dev token defaults are disabled outside local environment. | VERIFIED |
| CORS | Configurable CORS and local frontend origin test exist. | VERIFIED |
| Error handling | Frontend adapter maps 401/403/404/500 to safe messages; SSE errors sanitized in tests. | VERIFIED |
| Data deletion/archival | Retrieval excludes deleted/archived evidence in tested paths. | VERIFIED |
| Worker reliability | Retry/dead-letter queue code exists; local worker runtime was not tested in this audit. | VERIFIED as code/config |
| Compliance | Docs are privacy-aware, but no formal HIPAA/SOC2/security audit evidence found. | MISSING |
| Production auth | Pending/separate from dev bearer-token flow. | MISSING |
| Frontend token storage | App-wide login context persists token in localStorage, contradicting broad memory-only token wording. | CONTRADICTED |
| Endpoint contract health | Chat workspace is tested, but documents/audit/list-patient frontend API paths have backend route mismatches. | CONTRADICTED |

## 12. Delivery and Deployment Evidence

| Delivery item | Evidence | Classification |
|---|---|---|
| Local frontend dev command | `cd app/frontend && npm run dev` from AGENTS and package scripts | VERIFIED |
| Frontend production build | `npm run build` passed locally | VERIFIED |
| Backend tests | `python -m pytest -q` passed locally | VERIFIED |
| Docker Compose | Root `docker-compose.yml` defines PostgreSQL/pgvector, Redis, backend, and frontend services. | VERIFIED as configured |
| Backend Dockerfile | Backend containerization file exists. | VERIFIED |
| GitHub Actions backend test workflow | Python 3.11/3.12 matrix with PostgreSQL pgvector service and pytest/ruff steps. | VERIFIED as configured |
| GitHub Actions frontend test/build workflow | Node 20 workflow with npm ci, typecheck, lint, build. | VERIFIED as configured |
| Docker image workflow | Workflow builds/pushes backend/frontend images to GHCR. | VERIFIED as configured |
| Live URL | No live deployment URL found in repo or GitHub homepage metadata. | MISSING |
| Successful remote CI run | Workflow definitions exist, but current run status was not verified in this audit. | MISSING |
| Root lockfile warning | Next.js build warned about multiple lockfiles and selected `D:\projects\chatbot-hospital-system\package-lock.json` as root. | VERIFIED limitation |

## 13. Adoption and External Impact Evidence

| Evidence type | Result | Classification |
|---|---|---|
| Public repository | Repo is publicly visible through GitHub API. | VERIFIED |
| Stars | 0 | VERIFIED |
| Forks | 0 | VERIFIED |
| Issues | 0 open | VERIFIED |
| Pull requests | No PRs returned in sampled API query. | VERIFIED |
| Live deployment | Not found. | MISSING |
| Real users | No analytics, user count, or hospital pilot data found. | MISSING |
| Clinical validation | UAT/product-test documents exist, but human signoff is pending in Khuym handoff. | MISSING |
| Measured time saved | Not measured; only target assumptions in docs. | MISSING |
| Measured retrieval quality | Targets exist, but no evaluated dataset/results file was verified. | MISSING |

Adoption claims should remain neutral: "built a public full-stack project" is supported; "used by hospital staff" is not supported.

## 14. Resume-Safe Claims

These are evidence-safe claim ingredients, not final resume bullets.

| Claim ingredient | Evidence basis | Classification |
|---|---|---|
| Built a full-stack hospital knowledge assistant with FastAPI and Next.js | Backend/frontend source, docs, build/test results | VERIFIED |
| Implemented permission-filtered RAG so unauthorized patient chunks are filtered before LLM context construction | RetrievalService, PermissionService, tests | VERIFIED |
| Added citation validation and audit traces for patient-grounded answers | ChatService, streaming route, RetrievedEvidence, audit tests | VERIFIED |
| Built persistent chat threads with participants, sharing/archive behavior, and patient-linked messages | Backend routes/models/tests and frontend shell/tests | VERIFIED |
| Integrated HMS appointment/evidence import and sync services into document retrieval workflows | HMS routes/services/tests | VERIFIED |
| Implemented document ingestion/indexing with loaders, chunking, embeddings, retry/failure states, and background queue hooks | Worker/loaders/services/migrations | VERIFIED |
| Created frontend chat workspace with runtime API configuration, streaming controls, patient context, evidence panel, and safe error handling | AssistantShell, API adapter, stream client, frontend tests | VERIFIED |
| Maintained backend quality gate with 245 passing tests and frontend quality gate with test/typecheck/lint/build passing | Local verification commands | VERIFIED |
| Designed project documentation covering BRD, PRD/SRS, architecture, API/integration, deployment, test plan, and design metrics | `docs/00` through `docs/10` | VERIFIED |
| Sole/main implementer | User-provided solo role plus one-author Git shortlog | USER-PROVIDED plus VERIFIED support |

Good wording constraints:

| Avoid | Safer direction |
|---|---|
| "Production-ready HIPAA-compliant assistant" | "privacy-aware MVP with permission filtering, audit logs, and citation validation" |
| "Reduced lookup time by 80%" | "designed around a documented target of sub-30-second lookup; measured production impact not yet available" |
| "Used by doctors/nurses in production" | "built for doctor, nurse, pharmacist, records, and admin personas defined in the PRD" |
| "Secure authentication" | "implemented local/dev bearer-token auth with role and patient-scope checks; production auth remains separate" |
| "Token is memory-only" | "chat workspace supports runtime token state; app-wide login currently persists auth config in localStorage" |

## 15. Unsafe, Unsupported, or Contradicted Claims

| Claim | Status | Reason |
|---|---|---|
| Deployed to production | MISSING | No live URL or production deployment evidence verified. |
| Used by a hospital or real clinicians | MISSING | No user analytics, signoff, or pilot evidence found. |
| Reduced lookup time by 80% | MISSING | Docs contain target/assumption, not measured result. |
| Achieved `>=95%` citation rate | MISSING | Target exists; no evaluation result file found. |
| HIPAA compliant | MISSING | Privacy/security design exists, but no formal compliance audit evidence. |
| All frontend pages are API-contract correct | CONTRADICTED | Documents/audit/patient list API client paths do not match backend route set. |
| Token is memory-only across the app | CONTRADICTED | `auth-context.tsx` persists auth config/token in localStorage. |
| HMS sync endpoints enforce the same upload/admin permission boundary as manual appointment import | MISSING | Manual import checks permissions; sync route-level permission strength needs review. |
| Open-source adoption | CONTRADICTED for positive adoption | Public repo has 0 stars/forks and no PR evidence. |
| Team leadership | MISSING | Solo authorship evidence exists, not team evidence. |
| Production performance under load | MISSING | No benchmark or load-test output verified. |

## 16. Missing Evidence and Measurement Plan

| Priority | Missing evidence | How to measure or produce it |
|---|---|---|
| Critical | Live deployment or demo URL | Deploy backend/frontend or record local demo with exact commit, environment, and test data. |
| Critical | Production authentication/session design | Add implementation or ADR, tests for non-local auth, and update frontend storage behavior. |
| Critical | Human UAT signoff | Close pending Khuym handoff with signed test report and final browser screenshots. |
| Critical | Frontend/backend route contract for documents/audit/patients | Add integration tests or OpenAPI-generated client checks; fix mismatched routes. |
| High | Retrieval quality/citation rate | Create synthetic/de-identified eval dataset; report precision/recall/citation validity and refusal correctness. |
| High | Latency and throughput | Run load tests for chat, retrieval, document upload/indexing; record p50/p95/p99 and hardware profile. |
| High | PHI leakage/security regression suite | Expand permission tests, add negative retrieval fixtures, and record zero unauthorized chunk checks. |
| High | CI run evidence | Capture GitHub Actions run URLs or artifacts for backend, frontend, and Docker workflows. |
| Medium | User workflow screenshots/video | Capture chat, evidence panel, HMS import, thread share, metrics, and denied-access flows. |
| Medium | Docker smoke test | Start compose stack and verify health, chat, document upload, and metrics endpoints. |
| Medium | Public project polish | Add README demo GIF, architecture diagram, sample data notes, and known limitations. |
| Optional | External adoption | Publish release, gather feedback/issues/stars only if naturally earned. |

## 17. Questions for the User

Critical questions:

| Question | Why it matters |
|---|---|
| Can you confirm you were the only developer for implementation, docs, and tests? | Converts solo ownership from supported assumption to confirmed resume fact. |
| Was this ever deployed outside local development? If yes, where? | Determines whether deployment claims are safe. |
| Did any real hospital staff or classmates/instructors test it? | Determines whether user/adoption/UAT claims are safe. |
| Should the login token persistence in localStorage be fixed before using this project in a portfolio? | Current implementation weakens "memory-only token" and security claims. |
| Should document/audit/patient frontend API mismatches be fixed before portfolio screenshots? | Non-chat pages may fail at runtime. |

Valuable questions:

| Question | Why it matters |
|---|---|
| What was the project timeframe? | Enables accurate delivery-scope framing. |
| Was this for coursework, capstone, portfolio, internship, or real client discovery? | Changes how the project should be positioned. |
| Which part was hardest: RAG safety, streaming, HMS integration, UI, tests, or deployment? | Helps choose the strongest resume narrative. |
| Do you have screenshots, demo video, or benchmark logs? | Adds proof for portfolio and interviews. |
| Are there hidden/private repos or PRs related to this work? | Could add collaboration or review evidence. |

Optional questions:

| Question | Why it matters |
|---|---|
| Do you want this evidence sheet turned into resume bullets later? | This report intentionally avoids polished resume claims. |
| Do you want a portfolio case-study version? | The evidence supports a strong technical case study with caveats. |

## 18. Evidence Strength Scores

| Category | Score | Rationale |
|---|---:|---|
| Project context | 4/5 | Docs clearly define problem, users, requirements, architecture, deployment plan, and test plan. |
| Personal ownership | 4/5 | User provided solo role and Git history shows one author; external confirmation still missing. |
| Technical complexity | 4/5 | Permission-filtered RAG, citation validation, streaming, document ingestion, HMS integration, audit/metrics, Docker/CI. |
| Full-stack scope | 4/5 | Backend and frontend are both substantial and verified by tests/builds. |
| Functional completeness | 3/5 | Chat/RAG flows are strong; document/audit/admin frontend route contracts have gaps. |
| Testing evidence | 4/5 | Strong local backend/frontend gates; no live CI run or full E2E browser run verified in this audit. |
| Security/privacy evidence | 3/5 | Good permission/audit tests; production auth, compliance, and token storage need work. |
| Performance evidence | 1/5 | Targets exist, but measured latency/retrieval quality/load data are missing. |
| Deployment evidence | 3/5 | Docker/GitHub Actions configured and local build passes; no live deployment verified. |
| Adoption evidence | 1/5 | Public repo exists but no stars/forks/users/signoff. |
| Overall resume evidence strength | 3.5/5 | Strong as an implementation-heavy full-stack AI portfolio project; weak as a production impact/adoption story. |

## 19. Recommended Handoff Package

For a recruiter, interviewer, or portfolio reviewer, prepare:

| Artifact | Status | Notes |
|---|---|---|
| Public GitHub repo link | Available | Use `https://github.com/qwan30/chat-hospital-system`. |
| Architecture overview | Available | Summarize from `docs/05_system_architecture_sdd.md`. |
| Demo screenshots | Missing | Capture chat, evidence panel, HMS import, denied access, metrics. |
| Local run instructions | Available | Use `app/README.md`, backend/frontend READMEs, Docker Compose notes. |
| Test proof | Available | Include latest backend/frontend command outputs from this audit. |
| Security explanation | Available with caveats | Focus on permission-before-retrieval, citation validation, audit logs; disclose production auth gap. |
| Known limitations | Available | Include route mismatches, no live deployment, no measured production impact, no compliance audit. |
| Case-study narrative | Not written yet | Can be created from this sheet after claims are finalized. |
| Resume bullets | Not written yet | Should use only claims from section 14 after user confirms ownership/deployment context. |

## Final Quality-Control Checklist

| Check | Result |
|---|---|
| Every positive technical claim tied to repo evidence | Passed |
| Unsupported metrics separated from measured results | Passed |
| Resume-style polished bullets avoided | Passed |
| Missing evidence explicitly marked | Passed |
| Contradictions called out | Passed |
| Personal role treated as user-provided unless externally proven | Passed |
| Security/compliance claims kept conservative | Passed |
| Adoption claims kept neutral | Passed |
| Current verification commands included | Passed |

