# Phase 2 R2 Storage Implementation Plan

> For agentic workers: use executing-plans task-by-task with TDD and review checkpoints.

Goal: add a backend-only local/R2 storage abstraction and wire upload, OCR, page images, document content, source hashing, and workers to it.

Architecture: keep LocalStorageService compatible with existing local paths; define StorageService; add R2StorageService using the S3-compatible Python client; return r2://<object-key> URIs; use byte responses in API routes and the same factory in workers.

Tech stack: Python 3.11, FastAPI, Pydantic v1, PyMuPDF, RQ, boto3 S3 client pointed at Cloudflare R2, pytest/pytest-asyncio.

## Global constraints

- Local storage remains the default for tests and local development.
- Exact env names: HOSPITAL_AI_STORAGE_BACKEND, HOSPITAL_AI_R2_ENDPOINT, HOSPITAL_AI_R2_BUCKET, HOSPITAL_AI_R2_REGION, HOSPITAL_AI_R2_ACCESS_KEY_ID, HOSPITAL_AI_R2_SECRET_ACCESS_KEY.
- R2 document values use r2://<object-key> and are never converted to Path.
- R2 credentials never enter frontend code, VITE_* variables, API responses, logs, or errors.
- Every new production behavior has a failing test observed before implementation.
- No deployment, cloud resource creation, database migration, or unrelated dirty-file changes.

## Task 1: Contract/config/security tests

Files: create app/backend/tests/test_storage_contracts.py; modify app/backend/src/hospital_ai/core/config.py, app/backend/.env.example, app/backend/pyproject.toml.

Produce Settings fields storage_backend, r2_endpoint, r2_bucket, r2_region, r2_access_key_id, r2_secret_access_key. Produce StorageService, parse_r2_uri, and get_storage_service in services/storage.py. Add boto3>=1.34.0,<2.0.0.

Step 1, RED: write tests for env loading, unknown backend rejection, r2:// traversal rejection, and frontend source not containing R2_ACCESS_KEY_ID or R2_SECRET_ACCESS_KEY.

Step 2, verify RED from app/backend:
$env:PYTHONPATH="src"
.\\.venv\\Scripts\\python.exe -m pytest tests/test_storage_contracts.py -q
Expected: missing symbol/settings failures.

Step 3, add only the six Settings fields, exact .env.example names, and boto3 dependency.

Step 4, rerun the same command; settings tests pass while factory/parser tests remain red.

Step 5, commit:
git add app/backend/tests/test_storage_contracts.py app/backend/src/hospital_ai/core/config.py app/backend/.env.example app/backend/pyproject.toml
git commit -m "feat: define r2 storage configuration contract"

## Task 2: Local and R2 backends

Files: modify app/backend/src/hospital_ai/services/storage.py and tests/test_storage_contracts.py; create app/backend/tests/test_r2_storage.py.

Interface:
- async save_upload(*, patient_id, document_id, file) -> str
- read_bytes(storage_uri: str) -> bytes
- source_sha256(storage_uri: str) -> str
- save_page_image(patient_id, document_id, page_number, image_bytes) -> str
- read_page_image(patient_id, document_id, page_number) -> bytes
- get_storage_service(settings) -> StorageService

Step 1, RED: tests assert fake S3 put_object gets configured Bucket, generated Key, exact Body, and ContentType; get_object returns exact bytes; page PNG round-trips; SHA-256 equals hashlib.sha256(payload).hexdigest(); local upload is readable below storage_root; and default factory returns LocalStorageService.

Step 2, verify RED:
.\\.venv\\Scripts\\python.exe -m pytest tests/test_storage_contracts.py tests/test_r2_storage.py -q

Step 3, implement StorageService, parse_r2_uri, safe local-root resolution, LocalStorageService, R2StorageService, and get_storage_service. Construct boto3 only inside R2StorageService; require endpoint/bucket/access key/secret in R2 mode; generate names from sanitized filename and UUID/page values; raise FileNotFoundError for missing objects without credential text.

Step 4, run the same test command. Refactor only while green.

Step 5, request code review for Tasks 1-2 and fix all Critical/Important findings before API integration.

## Task 3: API serving and OCR bytes

Files: modify app/backend/src/hospital_ai/api/routes/documents.py, services/ocr.py, tests/test_documents.py, tests/test_ocr_service.py; create tests/test_storage_api_integration.py.

Step 1, RED: add tests for R2 upload URI, get_document_content returning byte Response with database MIME/body, page-image Response with image/png/exact bytes, and OcrService reading PDF bytes and saving PNG through the service instead of Path(storage_uri).

Step 2, verify RED:
.\\.venv\\Scripts\\python.exe -m pytest tests/test_storage_api_integration.py tests/test_documents.py::test_document_content_is_served_after_read_authorization tests/test_ocr_service.py -q

Step 3, use get_storage_service(settings) in upload/content/page routes; authorize before reads; use asyncio.to_thread for byte reads; return Response; map missing objects to NotFoundError. Change OCR text extraction to decode storage_service.read_bytes(uri) and PyMuPDF to open from bytes. Keep mock://, local://mock, and hms:// behavior unchanged.

Step 4, run:
.\\.venv\\Scripts\\python.exe -m pytest tests/test_storage_api_integration.py tests/test_documents.py tests/test_ocr_service.py -q

## Task 4: Worker r2:// processing and source hash

Files: modify app/backend/src/hospital_ai/workers/jobs.py and existing document/worker tests; create tests/test_r2_worker_integration.py.

Step 1, RED: fake R2 service contains text at r2://patients/...; patch get_storage_service; run processing; assert OCR gets bytes, no Path conversion, indexed_source_sha256 equals object hash, and generated PNG is readable from the service.

Step 2, verify RED:
.\\.venv\\Scripts\\python.exe -m pytest tests/test_r2_worker_integration.py tests/workers/test_documents_pipeline.py -q

Step 3, replace LocalStorageService construction with get_storage_service(settings), replace local-only _source_sha256 with service.source_sha256, and retain None for pending, hms://, and virtual docs. Keep current queue/DLQ policy unless a focused test proves storage errors are swallowed before RQ can retry.

Step 4, verify:
$env:PYTHONDONTWRITEBYTECODE="1"
$env:PYTHONPATH="src"
.\\.venv\\Scripts\\python.exe -m pytest tests/test_r2_worker_integration.py tests/workers/test_documents_pipeline.py tests/test_documents.py tests/test_ocr_service.py tests/test_storage_contracts.py tests/test_r2_storage.py tests/test_storage_api_integration.py -q
.\\.venv\\Scripts\\python.exe -m ruff check src/hospital_ai/services/storage.py src/hospital_ai/services/ocr.py src/hospital_ai/api/routes/documents.py src/hospital_ai/workers/jobs.py tests/test_storage_contracts.py tests/test_r2_storage.py tests/test_storage_api_integration.py tests/test_r2_worker_integration.py
git diff --check

## Task 5: Final verification, review, PR

Step 1: run complete backend focused suite, frontend tests/lint/typecheck, compose config checks, and scripts/verify_contracts.py as applicable. Record exact results; do not claim cloud deployment.

Step 2: use requesting-code-review with merge base and branch HEAD; resolve every Critical/Important finding and rerun covering tests.

Step 3: stage only Phase 2 files, run GitNexus detect_changes with scope=staged, inspect git diff --cached, then commit:
git commit -m "feat: add r2 document storage backend"

Step 4: push:
git push -u origin fix/r2-storage-phase2
Open PR to main with summary, exact tests, backend-only credential statement, non-goals, and rollback instructions. Do not rewrite existing r2:// records without a migration.

