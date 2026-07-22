# Task 6 final AI evaluation and security review

## Verdict

**NO-GO** for an AI-quality or healthcare-safety release.

The branch now fails closed on the two P1 defects discovered during this review, and its deterministic evaluation infrastructure reports missing evidence honestly. It does not, however, contain the external evidence required to pass release: the 50-case sentinel has no two-reviewer approval, the controlled-scan OCR engine is unavailable, and retrieval, Graph RAG, and chat have no real evaluation adapter. Those omissions prevent the planned quality and safety gates from being measured; they are not waivable skips.

## P1 remediation completed

### HMS write authorization

The full backend run and an isolated rerun proved that a `doctor` could cross HMS write boundaries for appointment import, patient sync, and full sync. The request reached the external HMS connector instead of raising `PermissionDeniedError`.

GitNexus rated `_require_hms_sync_write` **CRITICAL** because it fronts five routes: appointments, lab results, medical records, full sync, and patient sync. The remediation preserves the existing clinical document-upload policy while passing an immutable `HMS_WRITE_ROLES = {records_staff, admin}` policy to every HMS sync route and to the appointment evidence importer. Denials remain audited with the role and accepted roles.

Evidence after the fix:

- The three formerly failing authorization cases pass.
- The broader HMS, patient BFF, portfolio-hardening, document, OCR, and evaluation selection passes `75 passed`.
- No external HMS request is made by the denied cases.

### Silent OCR loss and Paddle 3 contract

`OcrService.extract_pages` previously returned a successful `OcrPage(text="")` for an image-only PDF when PaddleOCR was unavailable. That could move a scanned clinical document forward without recognized content.

The remediation now:

- raises an explicit `ExternalServiceError` for an image-only page when the OCR engine is unavailable;
- raises when an installed OCR engine returns no recognized text;
- parses the documented PaddleOCR 3.x `Result.json["res"]` contract (`rec_texts`, `rec_scores`);
- changes the optional CPU extra to `paddleocr>=3.0.0,<4.0.0` and `paddlepaddle>=3.2.0,<4.0.0`;
- adds regression tests for unavailable-engine failure, Paddle 3 result parsing, and dependency metadata.

The heavy Paddle packages were not installed during this review. The release runner therefore continues to report `engine_unavailable`, correctly blocking controlled-scan OCR quality claims.

## Verification evidence

### Backend and static gates

| Gate | Result | Evidence |
| --- | --- | --- |
| Full backend pytest before remediation | Failed | `433 passed, 3 failed, 3 skipped`; all failures were HMS write-authorization tests. |
| Isolated failing cases before remediation | Failed | `3 failed`; reproduced independently of suite order. |
| Focused remediation/regression suite | Passed | `75 passed` across HMS import, patient BFF, portfolio API, OCR service, document processing, and evaluation tests. |
| Full backend pytest after remediation | Passed | `439 passed, 3 skipped` in 159.76 seconds. |
| Ruff check | Passed | `py -3.12 -m ruff check src tests`. |
| Ruff format, changed scope | Passed | Five changed Python files formatted. |
| Ruff format, repository scope | Existing debt | One unrelated pre-existing file, `tests/test_golden_dataset.py`, would be reformatted. |
| API contract verifier | Passed with documented gap | 48 backend paths, 4 frontend paths; `/api` remains a known TODO, while auth and chat-stream routes match. |

### Source-backed evaluation runs

The final deterministic replays used dataset `synthetic-100-v2` at Git SHA `2ab2b6c7e940f19cb9ee1e5c1a018f69b33c305c` and wrote all four required artifacts (`run.json`, `cases.jsonl`, `junit.xml`, `summary.md`) under isolated temporary directories.

| Run | Exit | Results | Blocking gates |
| --- | ---: | --- | --- |
| `smoke/deterministic`, `corpus` | 1 | 50 passed, 0 failed, 0 skipped | `sentinel_independent_review`: 0 of 50 approved by two reviewers. |
| `release/deterministic`, all components | 1 | 302 passed, 1 failed, 900 skipped | Sentinel review; image OCR `engine_unavailable`; retrieval, graph, and chat adapters absent. |

The single failed release case is `ocr-image-engine`, with the explicit reason `missing image OCR dependencies: paddleocr, paddlepaddle`. The 900 skips are exactly 300 cases each for retrieval, graph, and chat. Corresponding hard `evaluation_adapter_configured` gates fail, so those skips cannot produce a passing verdict.

## Requirement-by-requirement audit

| Planned requirement | Current evidence | Status |
| --- | --- | --- |
| Three reusable global evaluation skills and safe installer | Tracked packages, installer hardening, validation reports, and global junction installation from Task 1. | Implemented. |
| Canonical corpus manifest and quarantine | 100 PDFs, 100 CSVs, 200 metadata records, 100 identities; duplicate sources excluded; six public-knowledge artifacts quarantined. | Implemented and deterministically validated. |
| 300 source-backed cases and 50-case sentinel | Exact planned category counts and source locators are checked in; validation rejects forged facts. | Implemented, but review approval is incomplete. |
| Two independent sentinel reviewers | Checked-in review status is `draft` with no reviewer identities. | **Missing; release blocker.** |
| Unified CLI and four artifacts | Smoke and release commands produce JSON, JSONL, JUnit, and Markdown with correct exit semantics. | Implemented. |
| OCR CER/WER/clinical-field evaluation on 100 controlled scans | Native gold and deterministic variants exist, but no image OCR engine executed. | **Not measured; release blocker.** |
| PaddleOCR 3/PaddlePaddle 3.2 contract | Dependency metadata and documented result parser are tested; actual engine execution is unavailable in this environment. | Code contract implemented; runtime proof missing. |
| Retrieval ablations at 10/50/100/200 documents | No real retrieval evaluation adapter is configured; 300 cases skipped with a failed hard gate. | **Missing; release blocker.** |
| Graph RAG entity/relation/path/provenance metrics | Product safety regression tests pass, but the release suite has no graph adapter and produces no planned quality metrics. | **Missing; release blocker.** |
| Chat fact, faithfulness, citation, refusal, and sync/SSE parity metrics | Existing deterministic route tests cover several safety contracts; the 300-case release suite has no chat adapter. | **Incomplete; release blocker.** |
| Hard permission/citation/provenance/safety gates | Evaluation contracts are fail-closed. Existing product regression tests cover join-chain permission, graph lifecycle scope, citation validation, refusals, and stream completion. | Implemented as code/tests; full 300-case product execution missing. |
| CI without pass-by-construction behavior | Old self-assignment test removed, `continue-on-error` removed, artifacts uploaded always, PR/release selection tested. | Implemented. |
| Live lane honesty | No credentials are configured and the runner records explicit skipped state rather than fallback scores. | Implemented; no live evidence claimed. |
| Full release evidence and frozen accepted baseline | Release exits 1 and no accepted quality baseline can be frozen from missing metrics. | **Not achieved.** |

## Security review

- Retrieval has executable adversarial coverage for unauthorized patients and mismatched patient-document-page-chunk joins.
- Graph RAG has coverage for exact patient relation scope, soft-deleted source pages/documents, inactive permissions, and source provenance.
- Synchronous and SSE chat have coverage for no-evidence refusal, hallucinated-citation rejection, cited-only evidence, graph-only evidence parity, and sanitized terminal refusal state.
- OCR processing now fails closed rather than silently accepting an image-only page without a recognition engine.
- HMS writes now require both the records/admin role boundary and the existing patient upload scope, with denial audit evidence.

No additional confirmed P0/P1 defect was found in the reviewed paths after these remediations. This statement is limited to deterministic source/test evidence; absent product evaluation adapters mean it is not a live-model or production certification.

## Required evidence before GO

1. Complete and persist two genuinely independent reviews for all 50 sentinel cases, resolving every disagreement.
2. Install and execute the pinned CPU OCR stack against all 100 controlled pages; pass CER, WER, reading-order, page-success, and critical-field gates.
3. Bind real retrieval, Graph RAG, and sync/SSE chat adapters to the evaluation contracts and execute all 300 cases plus 10/50/100/200 scaling ablations.
4. Freeze an accepted baseline only after the quality and hard safety gates pass, then rerun CI/release against the committed candidate.

Until those artifacts exist, the only defensible verdict is **NO-GO**.
