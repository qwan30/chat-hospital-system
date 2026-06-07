# Design System & Impact Metrics

**Project:** AI-Powered Hospital Knowledge Assistant
**Project Code:** HOSP-AI-001
**Version:** 1.1
**Status:** Draft
**Last Updated:** 2026-04-28

**Owner:** UX Lead / PM / Tech Lead

## 1. Purpose

Define the UI style and measurement model for a Kotaemon-style hospital assistant that helps staff retrieve, verify, and safely discuss hospital knowledge and permission-gated patient information.

## 2. UI Direction

Use Kotaemon as the primary interaction reference: conversation sidebar, central chat transcript, prompt composer, answer citations, and a source/evidence panel. Use `docs/design/core-ui-linear.md` for the dark, dense workspace shell and `docs/design/document-notion-lite.md` for readable evidence surfaces. Use `docs/design/dashboard-vercel.md` only for later dashboard or admin slices.

The first screen is the assistant workspace. Metrics cards, document upload, knowledge-base management, settings, and admin dashboards are not part of Phase 1.

Phase 1 components must distinguish verified backend-backed data from local/sample data. Patient-scoped answer fields may use the current chat API contract when available; shared-thread data, general hospital knowledge, HMS integration details, and missing patient metadata must be visibly marked as local/sample or unavailable until those contracts exist.

## 3. Design Tokens

| Role | Token | Value |
|---|---|---|
| App background | bg.app | #08090a |
| Shell surface | surface.shell | #0f1011 |
| Elevated surface | surface.elevated | #17181a |
| Border | border.subtle | #26282c |
| Primary text | text.primary | #f7f8f8 |
| Secondary text | text.secondary | #a3a7ad |
| Muted text | text.muted | #6f747d |
| Accent | accent.primary | #5e6ad2 |
| Info | semantic.info | #60a5fa |
| Success | semantic.success | #34d399 |
| Warning | semantic.warning | #fbbf24 |
| Danger | semantic.danger | #f87171 |

Keep semantic colors meaningful. Do not use medical colors as decoration.

### Figma Design System & Tokens
The design system, tokens, and variables are maintained in the Figma file at:
[Hospital AI Assistant Design System Specs](https://www.figma.com/design/QucDTsPwShazdDCLLqUHHW/Untitled?node-id=43-16&t=WBFw6pS24Jjm5WB4-1)

Local variables have been created under the **Design Tokens** collection using slash notation (e.g. `bg/app`, `surface/shell`, `semantic/danger`).

### Application Error & HTTP Status Code Mappings

| Error Class | Code | HTTP Status | Color Token | UX Context / Presentation |
|---|---|---|---|---|
| `PermissionDeniedError` | `FORBIDDEN` | 403 | `semantic.danger` (#f87171) | Accessing unauthorized patient context, sync, or settings writes. Logs a denied audit event. |
| `NotFoundError` | `NOT_FOUND` | 404 | `semantic.warning` (#fbbf24) | Requested thread, document, or trace record not found. Displays warning alert or fallback message. |
| `ValidationAppError` | `VALIDATION_ERROR` | 422 | `semantic.warning` (#fbbf24) | Upload payload or composer query parameter issues. Renders direct inline validation hints. |
| `ExternalServiceError` | `EXTERNAL_SERVICE_ERROR` | 502 | `semantic.danger` (#f87171) | Failure connecting to external HMS API. Prompts user to check integration status. |
| `AppError` | `APP_ERROR` | 500 | `semantic.danger` (#f87171) | Catch-all server failure. Sanitized in UI to avoid leaking stack traces. |
| Successful request | - | 200 / 201 | `semantic.success` (#34d399) | Successful patient queries, uploads, settings updates, and sync actions. |

### Typography System

We pair **Figtree** (headings) with **Noto Sans** (body text) to optimize legibility, visual trust, and inclusive accessibility (WCAG AAA alignment).

* **Heading/H1** (32px, Bold, line height 40px): Main dashboard and page titles.
* **Heading/H2** (24px, Bold, line height 32px): Primary sections and sidebar headers.
* **Heading/H3** (18px, Medium, line height 24px): Card titles, modals, and thread group headers.
* **Body/Bold** (14px, Bold, line height 22px): Table headers, buttons, and emphasized labels.
* **Body/Medium** (14px, Medium, line height 22px): Chat input fields, selected dropdown labels, and active navigation states.
* **Body/Regular** (14px, Regular, line height 22px): Main chat bubbles, document summary text, and paragraphs.
* **Body/Muted** (12px, Regular, line height 18px): Timestamp records, metadata items, and audit trace logs.

## 4. Core Components

| Component | Purpose | Must Have |
|---|---|---|
| Chat Workspace Shell | Main app entry | Conversation sidebar, chat area, evidence panel |
| Conversation Sidebar | Shared thread navigation | New, rename, delete, share, active state, empty state |
| Prompt Composer | Ask general or patient-scoped questions | Keyboard submit, loading state, scope-aware placeholder |
| Patient Context Gate | Prevent wrong-patient PHI access | Selected patient, permission status, denied state |
| AI Answer Block | Safe response display | Answer, citations, confidence, disclaimer, no-evidence state |
| Citation Chip | Link claim to source | Document/page/chunk label and selected state |
| Evidence Panel | Verify answer | Source metadata, excerpt/summary, unavailable state |
| Audit Cue | Explain sensitive access behavior | Trace ID or audit-ready state when available |
| Metrics Card | Prove impact | Later dashboard/admin phase only; do not add to Phase 1 first screen |

## 5. AI Answer Layout

```text
Question Scope
Question
Answer
Evidence / Citations
Confidence
Safety Note
```

For patient-linked answers, the layout must also include the selected patient context and a visible permission result. The UI must not show patient evidence until permission validation is complete.

## 6. Metrics to Capture

| Metric ID | Metric | Description |
|---|---|---|
| MET-001 | query_latency_ms | Total response time |
| MET-002 | retrieval_latency_ms | Retrieval time |
| MET-003 | generation_latency_ms | LLM generation time |
| MET-004 | documents_retrieved | Docs/chunks retrieved |
| MET-005 | citations_count | Number of citations |
| MET-006 | baseline_manual_time_sec | Estimated manual baseline |
| MET-007 | actual_ai_time_sec | Actual AI workflow time |
| MET-008 | estimated_time_saved_sec | Baseline - actual |
| MET-009 | estimated_cost_saved | Time saved * hourly cost |
| MET-010 | helpful_feedback_rate | User feedback metric |
| MET-011 | no_evidence_rate | Unsupported query rate |
| MET-012 | unauthorized_block_count | Blocked access attempts |
| MET-013 | shared_thread_reuse_count | Shared conversation reuse |

## 7. Metric Event Schema

```sql
CREATE TABLE metric_events (
    id UUID PRIMARY KEY,
    query_id UUID,
    user_id UUID,
    task_type VARCHAR(64) NOT NULL,
    baseline_manual_time_sec INTEGER,
    actual_ai_time_sec INTEGER,
    estimated_time_saved_sec INTEGER,
    estimated_cost_saved NUMERIC(12,2),
    documents_retrieved INTEGER,
    citations_count INTEGER,
    query_latency_ms INTEGER,
    retrieval_latency_ms INTEGER,
    generation_latency_ms INTEGER,
    shared_thread_id UUID,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);
```

Treat this schema as a planning target until backend migrations are validated. Do not back-edit existing base migrations when adding metric fields.

## 8. Baseline Assumptions

| Workflow | Manual Baseline | AI Target | Target Reduction |
|---|---:|---:|---:|
| Patient summary | 10-15 min | <30 sec | ~95% |
| Document lookup | 5-10 min | <30 sec | ~90% |
| Scanned PDF search | 5-15 min | <60 sec | ~80-90% |
| Medication/allergy pre-check | 3-5 min | <15 sec | ~90% |
| Lab trend lookup | 5-10 min | <30 sec | ~90% |

## 9. Cost Saving Formula

```text
cost_saved = time_saved_hours * average_staff_hourly_cost
```

Example:

```text
100 lookups/day * 10 minutes saved / 60 * $20/hour = ~$333/day
```

## 10. CV / Portfolio Template

```text
Built a permission-aware hospital knowledge assistant with a chat-first workflow, cited answers, and patient-scoped evidence controls.
Reduced patient information lookup time from ~10-15 minutes to under 30 seconds in simulated clinical workflows.
Decreased manual document review effort by ~80% through permission-aware semantic search with citations.
Implemented audit and metric tracking to estimate operational cost savings of ~$300/day.
```
