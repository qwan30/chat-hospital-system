# Acceptance Criteria Guide

> Project: HOSP-AI-001 · Version: 1.0 · Owner: QA Lead · Last Updated: 2026-06-14  

## 1. Format

All acceptance criteria use **Given/When/Then**: `Given [precondition] · When [trigger] · Then [expected outcome]`

## 2. Project Examples

### Chat with Cited Answer (from UC-001)

| AC ID | Given | When | Then |
|-------|-------|------|------|
| AC-001 | User authenticated with patient read scope | User submits clinical question | AI answer with ≥1 citation to document chunk |
| AC-002 | No relevant evidence exists | User submits question | Safe refusal ("Insufficient evidence"), no fabricated citations |

### Permission Enforcement (from UC-001/UC-002)

| AC ID | Given | When | Then |
|-------|-------|------|------|
| AC-003 | User lacks treatment relationship | User queries patient data | HTTP 403 + audit_logs denial entry |
| AC-004 | Permission scope expired | User accesses patient overview | HTTP 403 with expired-access message |

### Document Upload (from UC-003)

| AC ID | Given | When | Then |
|-------|-------|------|------|
| AC-005 | User has upload permission | User uploads valid PDF | Status="uploaded", OCR job enqueued |
| AC-006 | OCR completes successfully | Worker finishes processing | Status="indexed", chunks searchable |
| AC-007 | OCR fails | Worker encounters error | Status="ocr_failed", ocr_error populated, retry available |

## 3. Testability Checklist

Every AC must be: **Specific** (one behavior) · **Observable** (verifiable outcome) · **Independent** · **Traceable** (linked to UC/FR/BR) · **Testable** (automatable)

## 4. Priority Mapping

| Priority | Test Level | Automation |
|----------|-----------|------------|
| P1 (Must) | Unit + Integration + E2E (critical) | Required |
| P2 (Should) | Unit + Integration | Required |
| P3 (Could) | Unit | Recommended |

## 5. Non-Functional AC Examples

| Category | Example |
|----------|---------|
| Performance | Given 50 concurrent users, When all submit chat queries, Then P95 <30 sec |
| Security | Given expired JWT, When any API call, Then HTTP 401 |
| Audit | Given sensitive query, When query completes, Then audit_logs row exists with matching trace_id |

## Change Log
| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-06-14 | Agent | Created with project-specific AC examples |
