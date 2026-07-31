# Test Factory and Document Status Refactoring Design

## 1. Goal Description
The recent migration (`13dde695c97d`) updated the `ck_documents_status` constraint, collapsing specific failure states (`ocr_failed`, `index_failed`) into a generic `failed` state. This caused cascading failures across ~130 tests due to hardcoded string literals and over-specified test data. 
This spec outlines a refactoring plan to:
1. Restore lost error context in the production database (OCR vs Indexing failures).
2. Decouple the test suite from raw database schemas using Enums and test data factories.

## 2. Council Debate Summary

**Architect:** We must restore the lost failure granularity in production by adding `error_code`/`error_stage` and introduce a central test factory with Enums to prevent future test breakages.
**Skeptic:** Strongly opposes changing the production schema *just* for testing, noting that composite indexing on `status` + `error_stage` is worse than discrete statuses. 
**Critic:** Highlights that tests broke because they over-specified data they didn't care about. Recommends localized, scope-specific builders over a monolithic `make_document` god object.

**Verdict & Synthesis:** 
- The Skeptic and Critic are correct that test pain shouldn't dictate production schema. However, they missed that the production schema *already* changed and lost critical failure context. We *must* restore this context.
- We will adopt the Critic's recommendation of using scope-specific or minimal test builders rather than a monolithic factory that bloats over time.
- Tests should only specify the fields they actually assert on (minimizing coupling).

## 3. Proposed Changes

### Database & Models
- Re-evaluate the `documents` table schema: Since `status` is now a generic `failed`, ensure `ocr_error` or a new `error_code` column explicitly captures the failure stage (e.g., `OCR_FAILED`, `INDEX_FAILED`). 
- Update `hospital_ai/db/models.py` to map these fields properly.

### Test Architecture (Factories & Enums)
- **Enums:** Introduce `DocumentStatus` and `DocumentProcessingStage` Enums in `src/hospital_ai/core/enums.py` (or similar) to be used by both production code and tests.
- **Factory Pattern:** Create `tests/factories/document_factory.py`.
  - Instead of a single god-object factory, provide minimal, targeted factories (e.g., `make_ready_document`, `make_failed_document(stage="ocr")`).
  - By default, the factory will only set fields required by the DB constraints and fill the rest with sensible defaults or UUIDs.

### Refactoring Tests
- Migrate all `Document(status="...")` calls in `tests/` to use the new factories.
- Remove hardcoded status strings in tests.
- Ensure tests that don't care about the document's internal status use a generic factory method.

## 4. Open Questions / User Review Required
> [!IMPORTANT]
> **Database Rollback vs Column Addition:** Should we revert the recent migration that collapsed the statuses back to the old discrete statuses (`ocr_failed`, `index_failed`) for performance/indexing reasons (as the Skeptic pointed out), OR keep the new generic `failed` status and rely on `ocr_error`/`error_code` columns?

> [!WARNING]
> **Factory Library:** Do you prefer using a third-party library like `factory_boy` for this, or just pure Python helper functions in `tests/factories/`?

## 5. Verification Plan
- Run `pytest` and ensure all 559 tests pass.
- Verify that tests failing for OCR specifically check the `error_code` rather than the `status` string.
