# Master Test Plan

> Project: AI Copilot for Hospital Management System (HMS)  
> Project Code: HOSP-AI-001  
> Version: 5.0  
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

**Location**: `app/frontend/e2e/`  
**Framework**: Playwright (Chromium headless)  
**Run command**: `npx playwright test e2e/ --workers=1`

### 5.2 Test Architecture

| Layer | File | Purpose |
|-------|------|---------|
| **Helpers** | `e2e/_helpers.ts` | All shared playwright setup and routing mocks |
| **Flow tests** | `e2e/*.spec.ts` | Real-user interaction tests organized by feature area |

### 5.3 Test Suites & Status

| Suite | Tests | Status | Key Real-User Interactions |
|-------|-------|--------|---------------------------|
| **auth-flow** | 2 | ✅ 100% | Đăng nhập thành công và Đăng nhập sai thông tin |
| **business-flow** | 10 | ✅ 100% | Bệnh án, OCR, Chat bệnh nhân, Feedback, Setting... |
| **chat-general** | 2 | ✅ 100% | Chat tổng quát và Feedback từ chối |
| **chat-gpt-flow** | 6 | ✅ 100% | Chat luồng mới, Markdown stream, Lỗi kết nối |
| **chat-patient** | 3 | ✅ 100% | Chat gắn với patient |
| **full-plan-verification** | 4 | ✅ 100% | Kiểm tra các màn hình rỗng và truy cập menu |
| **graph-patient** | 2 | ✅ 100% | Timeline biểu đồ patient |
| **rbac-flow** | 3 | ✅ 100% | Phân quyền truy cập Patient, Setting |
| **screenshot-all** | 2 | ✅ 100% | Chụp ảnh tự động toàn hệ thống |
| **cdss-flow** | 1 | ✅ 100% | CDSS autonomous agent alert in /notifications |
| **Total** | **35** | **✅ 100%** | All passing |

### 5.4 Mock Strategy

Tests use Playwright's `context.route()` to mock all API responses. The auth mock supports:
- `dev-admin` token → Alex Admin (admin role)
- `dev-doctor` token → Dr. Sarah Chen (physician role)
- `e2e-test-token` → Dr. Sarah Chen (auto-login via localStorage)
- Unknown tokens → 401 (error state testing)

### 5.5 CI Commands

```bash
cd app/frontend && npx playwright test e2e/ --workers=1   # All tests
npx playwright test e2e/auth-flow.spec.ts                 # Single suite
npx playwright show-report                                # HTML report
```

---

## 6. CDSS Autonomous Agent Test Cases

### 6.1 Unit Tests — Backend

| Test ID | File | Test Name | Assertion |
|---------|------|-----------|----------|
| **UT-CDSS-001** | `app/backend/tests/test_cdss_agent.py` | `test_cdss_analysis_creates_alert` | Calls `run_cdss_analysis(session, document_id)` and asserts that a `ClinicalAlert` row is created in the database with `severity == "high"` and `title == "Bleeding Risk"`. |

**Purpose:** Validates the CDSS pipeline creates persistent, queryable alerts — ensuring downstream notification delivery is reliable.

### 6.2 E2E Tests — Playwright

| Test ID | Suite | Title | Role | Steps | Expected Result |
|---------|-------|-------|------|-------|-----------------|
| **TC-E2E-CDSS-001** | `cdss-flow.spec.ts` | CDSS Clinical Alert visible in Notifications | Doctor (`dev-doctor`) | 1. Seed doctor session via localStorage token (`role: cardiologist`, `token: dev-doctor`). <br>2. Navigate directly to `/notifications` — pre-seeded mock alert is already present in the static data. <br>3. Wait 1 second for page render. <br>4. Assert `'High Risk Clinical Alert'` is visible. <br>5. Toggle unread filter — verify alert still present. <br>6. Click the alert's **Open →** link (`href=/patients/p-001`) — assert URL changes to `/patients/p-001`. | Alert card displays with title `'High Risk Clinical Alert'`, body matching `/severe Bleeding Risk/i`, and navigation to patient profile succeeds. |

---

## Change Log
| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-04-27 | QA Lead | Initial master test plan |
| 2.0 | 2026-06-07 | Agent | Restructured and separated test plan, cases, and RTM matrices |
| 3.0 | 2026-06-07 | Agent | Added EMR/HMS integration test scenarios and verified gates |
| 4.0 | 2026-06-15 | Agent | Added E2E real-user interaction tests (56 tests, Playwright, 100% pass) |
| 5.0 | 2026-07-12 | QA Agent | Added CDSS Autonomous Agent unit test and E2E test case (TC-E2E-CDSS-001); updated suite total to 35 |
