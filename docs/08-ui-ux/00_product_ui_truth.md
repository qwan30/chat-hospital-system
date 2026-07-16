# Product UI Truth: HMS AI Copilot

> Project: AI-Powered Hospital Management System Copilot  
> Project Code: HOSP-AI-001  
> Version: 3.0  
> Status: Approved Source of Truth  
> Last Updated: 2026-07-12  

This document serves as the master **Product UI Truth** for the integrated Hospital Management System (HMS) AI Copilot. It defines the positioning, screen-level inventories, data ownership boundaries, and backend API routes mapped to the 25 target screens.

---

## 1. Product Positioning

*   **Integrated AI Copilot, Not a Standalone Chatbot**: The system is designed as an interactive AI assistant integrated directly into the Hospital Management System ecosystem, acting as a Backend-For-Frontend (BFF) aggregator.
*   **System of Record vs. AI Engine**:
    *   **HMS (System of Record)**: Exposes transactional clinical records (patients, appointments, vitals, labs, medication logs, authorization policies, and access requests).
    *   **Chatbot AI Assistant**: Manages local LLM interactions, RAG retrieval indexes (pgvector chunks, document OCR files), source citation mappings, session threads, and productivity metrics.

---

## 2. Screen Inventory & Data/API Ownership

The following table catalogs all target screens, mapping their priorities, data/API ownership scopes, and active endpoints:

| Screen ID | Screen Name & Route | Priority | Module | Data Ownership | API Ownership / Endpoint Called |
|---|---|---|---|---|---|
| **SCR-001** | Staff SSO Login (`/login`) | P0 (Must) | Auth | HMS Credential Store | HMS Auth: `POST /api/v1/auth/login` |
| **SCR-002** | MFA Verification (`/login/mfa`) | P0 (Must) | Auth | HMS MFA Tokens | HMS Auth: `POST /api/v1/auth/mfa/verify` |
| **SCR-003** | Populated Workspace (`/dashboard`) | P0 (Must) | Dashboard | Aggregated (HMS + Chatbot) | BFF API: `GET /api/v1/dashboard/summary` |
| **SCR-004** | Action Success Toast (Overlay) | P0 (Must) | Dashboard | Local UI State | UI Event-driven |
| **SCR-005** | Onboarding Empty State (`/dashboard`) | P1 (Must) | Dashboard | Aggregated | BFF API: `GET /api/v1/dashboard/summary` (empty) |
| **SCR-006** | Patient List (`/patients`) | P0 (Must) | Patients | HMS Patient Index | BFF API: `GET /api/v1/patients/search` |
| **SCR-007** | Patient Details (`/patients/:id`) | P0 (Must) | Patients | Aggregated (HMS Snapshot + AI Summary) | BFF API: `GET /api/v1/patients/{id}/overview` |
| **SCR-008** | Medication Review (`/patients/:id/meds`) | P0 (Must) | Patients | HMS Meds + AI Warning | BFF API: `POST /api/v1/patients/{id}/medication-review` |
| **SCR-009** | Patient Search Empty (`/patients`) | P1 (Must) | Patients | HMS Search Results | BFF API: `GET /api/v1/patients/search` (empty) |
| **SCR-010** | AI Summary Stream (`/patients/:id/summary`) | P0 (Must) | Patients | Chatbot Streaming Context | Chatbot API: `POST /api/v1/patients/{id}/ai-summary/generate` |
| **SCR-011** | New Patient Context Chat (`/chat/new`) | P0 (Must) | Chat | Chatbot Threads + HMS selector | Chatbot API: `POST /api/v1/chat-threads` |
| **SCR-012** | Safe Refusal Display (`/chat/:id`) | P0 (Must) | Chat | Chatbot Refusal Rules | Chatbot API: `POST /api/v1/chat` (HTTP 422 response) |
| **SCR-013** | AI Copilot Landing (`/chat`) | P0 (Must) | Chat | Chatbot Suggested Prompts | Chatbot API: `GET /api/v1/chat-threads` |
| **SCR-014** | Chat Cited Answer (`/chat/:id`) | P0 (Must) | Chat | Chatbot Vectors + Citations | Chatbot API: `POST /api/v1/chat` (cites evidence metadata) |
| **SCR-015** | OCR Indexing Dashboard (`/documents`) | P1 (Must) | Documents | Chatbot Document Status | Chatbot API: `GET /api/v1/documents` |
| **SCR-016** | OCR Review Screen (`/documents/:id/review`)| P1 (Must) | Documents | Chatbot Extraction Text | Chatbot API: `GET /api/v1/documents/{id}/extracted-text` |
| **SCR-017** | Batch Upload Modal (`/documents/upload`) | P1 (Must) | Documents | Chatbot Ingestion Queue | Chatbot API: `POST /api/v1/documents/batch` |
| **SCR-018** | Document Pages Preview (implied preview) | P1 (Must) | Documents | Chatbot Raw File Store | Chatbot API: `GET /api/v1/documents/{id}/pages/{page}` |
| **SCR-019** | Citation Source Viewer (Overlay Panel) | P0 (Must) | Citations | Chatbot Vector Chunk | Chatbot API: `GET /api/v1/chat/queries/{queryId}/citations` |
| **SCR-020** | Global Search Command (Ctrl+K) | P2 (Should) | Search | Multi-system search index | BFF API: `GET /api/v1/search/global` |
| **SCR-021** | Access Denied Screen (`/patients/:id/denied`)| P0 (Must) | Access Control | HMS Access Policy | BFF API: `GET /api/v1/patients/{id}/overview` (HTTP 403) |
| **SCR-022** | Access Request Justification Modal | P0 (Must) | Access Control | HMS Access Requests | BFF API: `POST /api/v1/access-requests` |
| **SCR-023** | Audit Events Log (`/audit/logs`) | P1 (Must) | Audit | Chatbot Audit Events | Chatbot API: `GET /api/v1/audit/events` |
| **SCR-024** | Impact Quality Summary (`/metrics`) | P1 (Must) | Metrics | Chatbot Metric Events | Chatbot API: `GET /api/v1/metrics/summary` |
| **SCR-025** | Profile & System Prefs (`/settings/profile`) | P2 (Should) | Settings | HMS User Profile + Local settings| BFF API: `GET /api/v1/users/me/preferences` |
| **SCR-026** | Notifications Feed (`/notifications`) | P1 (Must) | Notifications | Chatbot Alert Events (CDSS + system) | Chatbot API: `GET /api/v1/notifications` |

---

## 3. Environment & Workspace Modes

The UI exposes the active environment workspace mode (`SCR-027` selection panel) to restrict features and govern data safety:

1.  **Synthetic Sandbox**: Uses mock patient datasets and fake clinical records. Safe for developer testing and UI design iterations.
2.  **Training Playground**: Uses de-identified historical charts. Safe for hospital staff training and onboarding exercises.
3.  **Production Environment**: Fully integrated with live hospital intranet data grids. Connects to the real HMS database. Strict ABAC checks and audit logging are active.

---

## 4. Architectural Rules of UI Truth
*   **UI leads experience**: Component views (e.g. recent lists, timeline records, search filters) are defined by the 26 approved designs.
*   **No direct HMS DB manipulation by UI**: Frontend components must consume aggregated Backend-For-Frontend (BFF) endpoints routed through the AI Assistant, avoiding direct database operations.
*   **Source Citation Mandate**: Every answer panel displays source citation links (`SCR-019`) to build clinician trust and prevent hallucinations.

---

## 5. CDSS Autonomous Agent — Notification Type

### 5.1 High Risk Clinical Alert (`kind: 'ai'`)

The Autonomous CDSS (Clinical Decision Support System) Agent generates `ClinicalAlert` records that surface as a new notification type in the `/notifications` feed (`SCR-026`).

| Property | Value / Behaviour |
|----------|-------------------|
| **Notification ID** | e.g. `n-007` (auto-generated, unique per alert) |
| **`kind`** | `'ai'` — displayed with the AI/robot badge icon |
| **Title** | `'High Risk Clinical Alert'` |
| **Body** | Human-readable CDSS finding, e.g. _"CDSS detected severe Bleeding Risk due to new Aspirin prescription. Cross-referenced with patient history."_ |
| **`read`** | `false` on creation — alert always starts **unread**; dismissed by user action |
| **Severity** | Encoded in body/metadata: `LOW` / `MEDIUM` / `HIGH` / `CRITICAL`; alerts with severity ≥ `HIGH` are created |
| **`href`** | `/patients/{patient_id}` — clicking **Open** navigates to the full patient profile |
| **Trigger** | Automatic: fired by `run_cdss_analysis()` after document OCR + entity extraction + graph indexing complete |
| **Audience** | Treating physician (Doctor role) — scoped to the patient's care team |

### 5.2 Notifications Page Behaviour

*   **Unread badge**: The bell icon in the header shell shows an unread count that includes CDSS alerts.
*   **Unread filter**: Toggling the unread filter keeps CDSS `kind='ai'` alerts visible — they are treated identically to other unread notifications.
*   **Open action**: The **Open** link on each alert resolves `href` and performs a client-side navigation to the patient profile, where the doctor can review the full clinical context.
*   **Dismissal**: Marking an alert read (`PATCH /api/v1/notifications/{id}/read`) decrements the unread counter; the alert remains in the list for audit purposes.
