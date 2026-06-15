# Master Test Plan

> Project: AI Copilot for Hospital Management System (HMS)  
> Project Code: HOSP-AI-001  
> Version: 4.0  
> Status: Approved  
> Owner: QA Lead / PM  
> Last Updated: 2026-06-15  

---

## 1. Test Strategy

This document outlines the testing strategy, testing levels, quality gates, and AI evaluation metrics for the AI Copilot for HMS (HOSP-AI-001).

| Strategy Element | Definition & Policy |
|---|---|
| **Objective** | Verify functional correctness, access control security, clinical data privacy, performance latency, OCR parsing, RAG evaluation accuracy, and HMS integration sync correctness. |
| **Scope** | Unit tests, Integration tests, API tests, Permissions checks, OCR validation, RAG quality evaluation, end-to-end System workflows, and Performance stress testing. |
| **Out of Scope** | Full regulatory medical device certification, exhaustive network penetration testing, and clinical drug efficacy validations. |
| **Core Safety Principle** | AI outputs must remain strictly evidence-based and assistive. Under no circumstances should the chatbot generate clinical claims without valid source citations. |

---

## 2. HMS Integration Test Levels

In addition to standard unit and system testing, the QA lifecycle enforces specific integration test scenarios to verify sync and security boundaries across the boundary layers:

| Integration Test | Verification Objective | Verification Method |
|---|---|---|
| **HMS Snapshot Sync** | Verify the BFF successfully pulls EMR data snapshot and merges it with AI summary. | Mock HMS endpoints and verify response matching. |
| **HMS Permission Revocation** | Verify that if access is revoked on HMS, RAG retrieval immediately blocks queries. | Set permission key to False and execute query; assert HTTP 403. |
| **HMS Change Feed Sync** | Verify incremental changes from `/ai/changes` are processed and cached correctly. | Mock insertion events and inspect `patients` table and `hms_sync_logs` updates. |
| **Access Request Approval** | Verify that submitting justification requests grants access once approved on HMS. | Execute POST `/access-requests` -> mock HMS approval -> verify 200 OK query. |
| **Document OCR Workflows**| Verify file processing lifecycle states (Retry, Approve, Archive). | Trigger OCR fail -> select retry -> verify state returns to processing. |
| **Global Search Verification**| Verify Ctrl+K Global Search returns matches across patients, files, and threads. | Execute global search query -> assert multi-type result JSON fields. |
| **Dashboard Summary Validation**| Verify dashboard summary aggregates data from both HMS health checks and local metrics. | Fetch dashboard metrics -> verify metrics counts match DB test data values. |

---

## 3. Entry / Exit Quality Gates

| Stage | Entry Criteria (When to Start) | Exit Criteria (When to Promote) |
|---|---|---|
| **System Test** | - Successful build deployed in staging.<br>- Test database seeded with synthetic records. | - Zero critical (P0/P1) issues unresolved.<br>- Overall test case pass rate ≥ 95%. |
| **UAT** | - System test exit criteria fully met.<br>- User documentation and tutorials available. | - Clinician SME validation complete.<br>- Signed-off UAT checklist. |
| **Release** | - UAT exit criteria fully met.<br>- Production rollback plan validated. | - Production deployment smoke tests pass.<br>- Baseline metrics initialized in production DB. |

---

## 4. AI & RAG Evaluation Metrics

Since standard deterministic assertions are insufficient for generative AI models, we measure retrieve-generate quality using the following targets:

| RAG Quality Metric | Target Goal | Verification Method |
|---|---|---|
| **Citation Rate** (when evidence exists) | `≥95%` | Automated evaluation (Ragas / Groundedness parser) |
| **Faithfulness** (claims supported by citations) | `≥90%` | LLM-as-a-judge comparison over evaluation dataset |
| **Retrieval Accuracy** (Top-k contains correct source) | `≥80%` | MRR / NDCG calculations on benchmark documents |
| **Safe Refusal Rate** (when evidence is missing) | `≥90%` | Verification of `INSUFFICIENT_EVIDENCE` responses |
| **Context Leakage** (unauthorized chunks passed to LLM) | **0% (Zero leaks)** | Permission retrieval tests |
| **Summary Latency** (MVP dataset compilation) | `<30 seconds` | Performance test logging |

---

## 5. E2E Real-User Interaction Tests

### 5.1 Overview

A comprehensive E2E test suite simulates real clinical user interactions using Playwright. Unlike passive rendering checks, these tests perform actual browser actions — typing, clicking, submitting forms, waiting for responses — exactly as a clinician, nurse, or admin would.

**Location**: `app/frontend/e2e/flows/`  
**Framework**: Playwright (Chromium headless)  
**Run command**: `npx playwright test e2e/flows/ --workers=1`

### 5.2 Test Architecture

| Layer | File | Purpose |
|-------|------|---------|
| **Auth helpers** | `e2e/helpers/auth.ts` | `loginViaSSO()`, `loginViaEmailForm()`, `setupContext()`, `mockAllApiRoutes()` |
| **Interaction helpers** | `e2e/helpers/interactions.ts` | `waitForLoadingToFinish()`, `typeAndSubmit()`, `clickAndWait()`, `navigateViaSidebar()` |
| **Flow tests** | `e2e/flows/*.spec.ts` | Real-user interaction tests organized by feature area |

### 5.3 Test Suites & Status

| Suite | Tests | Status | Key Real-User Interactions |
|-------|-------|--------|---------------------------|
| **login-flow** | 12 | ✅ 100% | SSO click → dashboard, email/password form fill, invalid credentials error, empty field validation |
| **chat-flow** | 7 | ✅ 100% | Type clinical question, suggestion cards, multi-turn conversation, thread navigation |
| **patient-flow** | 11 | ✅ 100% | Type search → filter, click patient → detail + tabs, AI Summary, Meds Review, Access Denied |
| **document-flow** | 5 | ✅ 100% | Document list badges, upload dropzone, file input, detail page |
| **navigation-flow** | 16 | ✅ 100% | All 7 sidebar clicks, all 7 direct URLs, user menu, search trigger |
| **error-flow** | 5 | ✅ 100% | API 500, auth expiry → login, 404, rate limit 429, slow network |
| **Total** | **56** | **✅ 100%** | All passing (2.9 min, single worker) |

### 5.4 Mock Strategy

Tests use Playwright's `context.route()` to mock all API responses. The auth mock supports:
- `dev-admin` token → Alex Admin (admin role)
- `dev-doctor` token → Dr. Sarah Chen (physician role)
- `e2e-test-token` → Dr. Sarah Chen (auto-login via localStorage)
- Unknown tokens → 401 (error state testing)

### 5.5 CI Commands

```bash
cd app/frontend && npx playwright test e2e/flows/ --workers=1   # All 56 tests
npx playwright test e2e/flows/login-flow.spec.ts                 # Single suite
npx playwright show-report                                        # HTML report
```

---

## Change Log
| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-04-27 | QA Lead | Initial master test plan |
| 2.0 | 2026-06-07 | Agent | Restructured and separated test plan, cases, and RTM matrices |
| 3.0 | 2026-06-07 | Agent | Added EMR/HMS integration test scenarios and verified gates |
| 4.0 | 2026-06-15 | Agent | Added E2E real-user interaction tests (56 tests, Playwright, 100% pass) |
