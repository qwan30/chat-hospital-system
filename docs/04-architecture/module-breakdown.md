# Module Breakdown

> Project: HOSP-AI-001 · Version: 1.0 · Owner: System Architect · Last Updated: 2026-06-14  

## 1. API Layer (14 route modules)

| Module | File | Key Endpoints | Dependencies |
|--------|------|---------------|-------------|
| Auth | `routes/auth.py` | GET /me | get_current_user |
| Patients | `routes/patients.py` | list, overview, summary, meds, timeline | PermissionService, HMS |
| Documents | `routes/documents.py` | upload, list, detail, retry-ocr | Storage, OCR, RQ |
| Chat | `routes/chat.py` | POST (10/min) | ChatService |
| Chat Stream | `routes/chat_stream.py` | POST SSE | ChatService, LLM |
| RAG Trace | `routes/rag_trace.py` | GET trace | AiQuery, RetrievedEvidence |
| Chat Threads | `routes/chat_threads.py` | CRUD + participants | ChatThreadService |
| HMS | `routes/hms.py` | POST sync, GET jobs | HmsSyncService |
| Audit | `routes/audit.py` | GET logs (security/admin) | AuditLog |
| Settings | `routes/settings.py` | GET/PUT (14 keys) | SettingsStore |
| Dashboard | `routes/dashboard.py` | GET summary | MetricsService |
| Search | `routes/search.py` | GET global (20/min) | PermissionService |
| Access Requests | `routes/access_requests.py` | POST create, GET status | HMS, Audit |
| Feedback | `routes/feedback.py` | POST submit, GET metrics | MetricsService |

## 2. Service Layer (18 modules)

| Module | File | Responsibility | Key Classes |
|--------|------|---------------|-------------|
| Chat | `services/chat.py` | RAG pipeline orchestration | ChatService |
| Chat Threads | `services/chat_threads.py` | Thread lifecycle | ChatThreadService |
| Chat Utils | `services/chat_utils.py` | Prompt building, stub answers | build_grounded_prompt |
| Embeddings | `services/embeddings.py` | Embedding generation + cache | EmbeddingService |
| Embedding Providers | `services/embedding/` | 3 providers | manager, deterministic, ollama, openai |
| LLM Providers | `services/llm/` | 3 providers | LLMManager, BaseLLM, StubLLM, OllamaLLM, OpenAILLM |
| Reasoning | `services/reasoning.py` | 3 pipelines | SimpleQA, DecomposeQA, PatientSummary |
| Retrieval | `services/retrieval.py` | Vector + hybrid search | RetrievalService |
| BM25 | `services/bm25.py` | Keyword retrieval | Bm25Service |
| Graph RAG | `services/graph_rag.py` | Entity-relationship retrieval | find_related_entities |
| Permissions | `services/permissions.py` | ABAC + RBAC | PermissionService |
| Audit | `services/audit.py` | Immutable audit trail | AuditService |
| Drug Check | `services/drug_check.py` | Drug-allergy detection | DrugCheckService |
| HMS Connector | `services/hms_connector.py` | HMS API client | HmsConnector |
| HMS Sync | `services/hms_sync.py` | Sync orchestration | HmsSyncService |
| HMS Appointments | `services/hms_appointments.py` | Appointments | HmsAppointmentsService |
| Metrics | `services/metrics.py` | Impact tracking | MetricsService |
| General Knowledge | `services/general_knowledge.py` | Non-patient queries | GeneralKnowledgeService |

## 3. Frontend (14+ pages, 60+ components)

| Domain | Components |
|--------|-----------|
| `ui/` | 30 shadcn primitives |
| `app-shell/` | Sidebar, Topbar, CommandPalette, Footer, RightRail |
| `auth/` | LoginCard, MFACard, AuthMarketingPane, AuthTrustStrip |
| `chat/` | ChatLayout, Composer, StreamingAnswer, AssistantCard, UserBubble, PromptGrid, SafeRefusalCard |
| `patient/` | DetailHeader, AISummaryCard, MedicationList, EncounterTimeline, MiniLabStrip, AllergyAlertsCard |
| `document/` | DocumentsTable, UploadDropzone, BatchUploadModal, OCRPipelineStepper, OCRReviewPage |
| `evidence/` | CitationCard, EvidenceRail, InlineCitation, DocumentViewerModal, RetrievalStepper |
| `access/` | RequestModal, DeniedPanel, JustificationTextarea, NextActionsRail |
| `audit/` | EventsTable, FilterBar, EventDrawer, ComplianceCard |
| `viz/` | TrendLineChart, BarVolumeChart, StorageDonutChart, QualitySafetyChart |
| `empty/` | DashboardHero, EmptyStateCard, Skeleton components |

## Change Log
| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-06-14 | Agent | Complete module map — 14 routes, 18 services, 14+ pages, 60+ components |
