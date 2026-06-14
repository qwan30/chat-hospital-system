---
title: Project Foundation
project: HOSP-AI-001 — AI Hospital Knowledge Assistant
status: Approved
version: 1.0.0
owner: Tech Lead
reviewers:
  - Product Owner
  - System Architect
  - QA Lead
created_at: 2026-04-27
last_updated_at: 2026-06-14
---

# Project Foundation — HOSP-AI-001

## 1. Mục đích tài liệu

Tài liệu này xác định nền tảng kỹ thuật và tiêu chuẩn phát triển cho dự án **AI-Powered Hospital Knowledge Assistant (HOSP-AI-001)**.

Mục tiêu:

* Thống nhất cách hệ thống được thiết kế và phát triển.
* Giảm quyết định kỹ thuật mang tính cá nhân.
* Giúp thành viên mới hiểu nhanh cấu trúc dự án.
* Tạo rào chắn để AI và developer sinh code đúng định hướng.
* Đảm bảo hệ thống có thể bảo trì, kiểm thử và mở rộng.
* Làm cơ sở cho code review, CI/CD và Definition of Done.

Tài liệu này không thay thế:

* PRD — xem `docs/02-product/prd.md`.
* SRS — xem `docs/03-requirements/functional-requirements.md`.
* API specification — xem `docs/05-api/api-contract.md`.
* ADR cho từng quyết định kiến trúc — xem `docs/04-architecture/adr/`.

---

## 2. Thông tin dự án

| Thuộc tính              | Nội dung                                                            |
|-------------------------|---------------------------------------------------------------------|
| Tên dự án               | HOSP-AI-001 — AI-Powered Hospital Knowledge Assistant               |
| Loại hệ thống           | Web Application (Next.js 16 frontend + FastAPI backend)             |
| Product Owner           | Product Owner (see stakeholders.md)                                 |
| Tech Lead               | Tech Lead / System Architect                                        |
| QA Lead                 | QA Lead                                                             |
| Repository              | chatbot-hospital-system                                             |
| Production URL          | Hospital Secure Intranet (internal only)                            |
| Tài liệu sản phẩm      | `docs/02-product/prd.md`                                            |
| Tài liệu yêu cầu       | `docs/03-requirements/functional-requirements.md`                   |
| API documentation       | `docs/05-api/api-contract.md` + Swagger at `/docs`                  |

---

## 3. Bối cảnh và mục tiêu

### 3.1. Bài toán

Bệnh viện cần một trợ lý AI có khả năng tra cứu hồ sơ bệnh nhân, tài liệu y khoa phi cấu trúc, và lịch hẹn HMS một cách nhanh chóng, chính xác và an toàn. Hệ thống phải cung cấp câu trả lời có trích dẫn nguồn, kiểm soát quyền truy cập theo phạm vi điều trị, và ghi nhật ký kiểm toán đầy đủ để tuân thủ HIPAA.

### 3.2. Người dùng chính

| Nhóm người dùng | Mục tiêu | Nhu cầu chính |
|-----------------|----------|---------------|
| Bác sĩ (Doctor) | Tra cứu nhanh thông tin bệnh nhân | Hỏi đáp AI có trích dẫn, tóm tắt bệnh án |
| Y tá (Nurse) | Theo dõi thuốc và chỉ số | Tra cứu thuốc, tương tác thuốc |
| Dược sĩ (Pharmacist) | Kiểm tra tương tác thuốc | Cảnh báo dị ứng, tương tác thuốc |
| Nhân viên phòng lab | Tra cứu kết quả xét nghiệm | Tìm kiếm ngữ nghĩa kết quả lab |
| Nhân viên hồ sơ | Upload và quản lý tài liệu | OCR, indexing tài liệu y khoa |
| Bảo mật (Security) | Kiểm toán truy cập | Xem audit logs, phát hiện vi phạm |
| Admin / IT | Quản trị hệ thống | Cấu hình, metrics, giám sát |

### 3.3. Mục tiêu kinh doanh

* **BG-001**: Giảm thời gian tra cứu thông tin bệnh nhân từ 10–15 phút xuống dưới 30 giây.
* **BG-002**: Giảm khối lượng tra cứu EMR thủ công từ 5–10 tài liệu xuống 1 câu trả lời AI có trích dẫn.
* **BG-003**: Đảm bảo ≥95% câu trả lời có trích dẫn nguồn chính xác.
* **BG-004**: Tăng năng suất nhân viên ≥80%.
* **BG-005**: Ghi nhận 100% truy vấn nhạy cảm vào audit log (tuân thủ HIPAA).
* **BG-006**: Duy trì độ trễ đồng bộ cache HMS dưới 15 phút.

### 3.4. Ngoài phạm vi

Phiên bản hiện tại (MVP) không giải quyết:

* Chẩn đoán y khoa tự động (chỉ hỗ trợ tra cứu và tóm tắt).
* Tích hợp với các hệ thống EMR không phải HMS.
* Ứng dụng mobile native (web responsive only).
* Xử lý ngôn ngữ tự nhiên đa ngôn ngữ (chỉ tiếng Anh cho dữ liệu y khoa).
* Thanh toán hoặc billing.

---

## 4. Các nguyên tắc kỹ thuật

1. Business rule phải được mô tả trong spec trước khi triển khai.
2. Code nghiệp vụ không phụ thuộc trực tiếp vào framework hoặc hạ tầng.
3. Mọi thay đổi quan trọng phải được bảo vệ bằng automated test.
4. Không áp dụng pattern chỉ vì pattern đang phổ biến.
5. Chỉ thêm độ phức tạp khi có yêu cầu hoặc số liệu chứng minh.
6. Mỗi module phải có trách nhiệm và ownership rõ ràng.
7. Các quyết định kiến trúc quan trọng phải được ghi lại bằng ADR.
8. Logging, monitoring, security và rollback không được xem là công việc làm sau.
9. AI có thể sinh code, test và tài liệu nhưng không tự quyết định business rule.
10. Khi implementation khác spec, phải xác định lại spec trước khi sửa code.
11. **Local-first PHI**: Dữ liệu bệnh nhân không được gửi ra external cloud LLM.

---

## 5. Yêu cầu phi chức năng

### 5.1. Hiệu năng

| Chỉ số                          | Mục tiêu                |
|----------------------------------|-------------------------|
| API response time P50            | <200 ms                 |
| API response time P95            | <1000 ms                |
| Chat query latency (end-to-end)  | <30 sec (MVP target)    |
| Số người dùng đồng thời         | ~50 clinicians          |
| Thời gian xử lý OCR job         | <60 sec per page (CPU)  |
| Thời gian khởi động ứng dụng    | <10 sec                 |

### 5.2. Khả dụng

| Chỉ số                      | Mục tiêu                     |
|------------------------------|-------------------------------|
| Availability                 | 99.5% (hospital intranet)    |
| RTO                          | <4 hours                     |
| RPO                          | <1 hour                      |
| Maximum acceptable downtime  | 2 hours during business hours |

### 5.3. Khả năng mở rộng

Hệ thống phải có khả năng:

* Scale ngang FastAPI instances (stateless BFF).
* Chạy nhiều RQ worker instances.
* Cache document chunks và embeddings trong PostgreSQL + pgvector.
* Tích hợp thêm LLM providers qua LLM Manager pattern.

Không cài đặt Redis cluster, Kafka, hoặc ElasticSearch cho MVP.

### 5.4. Bảo mật

* HTTPS bắt buộc trên tất cả endpoints.
* JWT authentication cầu nối từ HMS (không có user registry riêng).
* ABAC + RBAC enforcement ở cả API gateway và RAG retrieval layer.
* Audit log bắt buộc cho mọi truy vấn nhạy cảm.
* Dữ liệu PHI không rời khỏi mạng nội bộ bệnh viện.
* Secret quản lý qua biến môi trường, không commit vào git.
* Rate limiting: chat 10/phút, search 20/phút.

### 5.5. Khả năng quan sát

* Structured logging với correlation ID (trace_id).
* OpenTelemetry tracing xuyên suốt các service boundaries.
* Health check endpoints (`/api/v1/health`).
* Metrics endpoint (`/api/v1/feedback/metrics/summary`).
* Alert cho: API 5xx >2%, chat latency P95 >5s, OCR queue backlog >30min.

---

## 6. Kiến trúc tổng thể

### 6.1. Kiểu kiến trúc được chọn

```
Modular Backend-for-Frontend (BFF) + Service Layer
```

Lý do: FastAPI BFF đóng vai trò single entry point cho Next.js UI. Service layer tách biệt business logic khỏi API handlers. PostgreSQL là database duy nhất cho cả transactional data và vector search.

| Lựa chọn | Kết luận |
|-----------|----------|
| Modular Monolith (BFF) | **SELECTED** — triển khai đơn giản, transaction thuận tiện |
| Microservices | Rejected — tăng độ phức tạp, không cần cho MVP |
| Layered Architecture | Rejected — dùng BFF pattern thay thế |

### 6.2. Quy tắc phụ thuộc

```
Next.js UI → FastAPI BFF (routes/) → Service Layer (services/) → Database (db/)
                                                                  → LLM Manager
                                                                  → Embedding Service
                                                                  → HMS Connector
```

Quy tắc:
* Routes chỉ điều phối request, authentication và response mapping.
* Services chứa toàn bộ business logic.
* Không đặt business logic trong API route handlers.
* LLM, Embedding, và Storage được abstract hóa qua provider interfaces.

### 6.3. Cấu trúc source code

```
app/
├── backend/
│   ├── alembic/versions/    # 6 migration scripts (0001–0006)
│   ├── scripts/             # seed, demo, smoke tests, UAT checker
│   └── src/hospital_ai/
│       ├── api/routes/      # 14 route modules
│       ├── core/            # config, errors, logging, security
│       ├── db/              # models (13 tables), session, migrations
│       ├── schemas/         # Pydantic request/response models
│       ├── services/        # 18 service modules
│       │   ├── embedding/   # 3 providers (deterministic, ollama, openai)
│       │   └── llm/         # 3 providers (stub, ollama, openai)
│       └── workers/         # RQ job definitions + queue
├── frontend/
│   └── src/
│       ├── app/(app)/       # 14 Next.js App Router pages
│       ├── components/      # 60+ feature components + 30 UI primitives
│       └── lib/             # API client, auth context, constants
```

---

## 7. Domain-Driven Design (Partial)

### 7.1. Bounded Context

| Context | Trách nhiệm | Dữ liệu sở hữu |
|---------|-------------|----------------|
| Identity & Auth | JWT validation, user identity bridge | users |
| Patient Management | Patient CRUD, permissions, access scopes | patients, patient_permissions |
| Document Processing | Upload, OCR, chunking, vector embedding | documents, document_pages, document_chunks |
| AI Chat & RAG | Query, retrieval, LLM generation | ai_queries, retrieved_evidence, chat_threads, chat_messages |
| Audit & Compliance | Security audit trail | audit_logs |
| HMS Integration | Data sync, appointment/lab fetching | hms_sync_logs |
| System Settings | Runtime configuration | system_settings |

### 7.2. Ubiquitous Language

| Thuật ngữ | Định nghĩa |
|-----------|------------|
| Patient | Đối tượng được chăm sóc y tế (MRN, department, status) |
| MRN | Medical Record Number |
| Permission Scope | Phạm vi truy cập: read, summary, medication, upload, admin |
| Document Chunk | Đoạn văn bản đã được vector hóa (pgvector embedding 1024-dim) |
| AI Query | Câu hỏi lâm sàng gửi đến hệ thống AI |
| Retrieved Evidence | Chunk được chọn làm bằng chứng cho câu trả lời |
| RAG Pipeline | Retrieve → Rerank → Generate (3 pipelines: simple_qa, decompose_qa, patient_summary) |
| Chat Thread | Cuộc hội thoại clinician-AI (patient-linked hoặc general) |
| HMS | Hospital Management System — hệ thống EMR nguồn |
| Trace ID | UUID xuyên suốt các service để tracking và audit |

---

## 8. CQRS & Data Strategy

```
[X] Tách Command/Query trong service layer (không tách database)
[ ] Read model riêng — chưa cần cho MVP
```

**Database:** PostgreSQL + pgvector (single database cho transactions + vector search).
**Queue:** Redis + RQ cho background jobs (OCR, indexing, HMS sync).
**Cache:** In-memory embedding cache (2048 entries) + optional Redis cache.

---

## 9. API Standards

* **Style:** REST JSON qua FastAPI, prefix `/api/v1`.
* **Versioning:** URL path-based.
* **Error format:** `{"error": "CODE", "message": "...", "metadata": {"trace_id": "uuid"}}`.
* **Rate limiting:** slowapi — chat 10/min, search 20/min.
* **14 route modules** — auth, patients, documents, chat, chat_stream, rag_trace, chat_threads, hms, audit, settings, dashboard, search, access_requests, feedback.

---

## 10. Authentication & Authorization

* **Auth:** JWT Bearer token cầu nối từ HMS — không có user registry riêng.
* **RBAC:** 7 roles (doctor, nurse, pharmacist, lab_staff, records_staff, security, admin).
* **ABAC:** Patient permissions với scope (read/summary/medication/upload/admin) + expiration.
* **Enforcement:** API gateway (deps.py) + RAG retrieval layer (PermissionService).

---

## 11. Validation (3-Layer)

1. **Input validation:** Pydantic schemas tại API boundary.
2. **Business validation:** Permission checks, citation validation, drug conflict detection.
3. **Data constraints:** CHECK, UNIQUE, FK constraints trong PostgreSQL.

---

## 12. Coding Standards

* Backend (Python): snake_case functions, PascalCase classes, PEP 8 + Ruff.
* Frontend (TypeScript): camelCase, PascalCase components, ESLint.
* Database: snake_case tables/columns.
* Function <50 lines, file <800 lines, nesting <4 levels, params <5.

---

## 13. Testing Strategy

| Loại | Framework | Target |
|------|-----------|--------|
| Unit | Vitest (FE) + pytest (BE) | 80% line coverage |
| Integration | pytest-asyncio | API + DB flows |
| E2E | Playwright | Critical user journeys |
| RAG Eval | Custom eval scripts | Citation accuracy ≥95% |

---

## 14. CI/CD Pipeline

```
Lint → Typecheck → Unit Tests → Build → Integration Tests → Security Scan → Deploy
```

PR không được merge khi: build/test thất bại, lint/typecheck lỗi, security vulnerability, migration chưa review.

---

## 15. Environments

| Environment | Data | Access |
|-------------|------|--------|
| Local | Synthetic | Developer PC (16GB RAM) |
| Dev | Synthetic / de-identified | Dev team |
| QA | Synthetic / masked EMR | QA + testers |
| UAT | Masked clinical data | Clinician SMEs |
| Production | Real patient records | Hospital intranet only |

---

## 16. Git Workflow

Trunk-based với feature branches. Convention:
```
feat(chat): add streaming response support
fix(permissions): prevent scope bypass
docs(api): update contract for chat-threads
test(chat): add citation validation
```

---

## 17. Code Review — Key Checks

* [ ] Business logic đúng layer (service, không phải route).
* [ ] Permission check trước retrieval.
* [ ] Citation validation enforced.
* [ ] No hardcoded secrets.
* [ ] Test coverage cho chức năng mới.
* [ ] Audit log cho thao tác nhạy cảm.
* [ ] Error handling không swallow.

---

## 18. Definition of Ready & Done

**Ready:** Clear business goal, defined scope, testable ACs, API contract clear, risks noted.
**Done:** Code meets spec, tests pass, review complete, lint/typecheck clean, docs updated, migration tested, security checklist verified.

---

## 19. AI Usage Rules

AI được phép: sinh implementation từ spec, viết tests, refactor, tạo docs, phân tích impact.
AI không được: quyết định business rule y tế, thay đổi quyền truy cập, tạo breaking changes, xóa dữ liệu.
Mọi code AI → phải review, CI pass, có tests, tuân thủ spec.

---

## 20. ADR Catalog

| ID | Decision | Status |
|----|----------|--------|
| ADR-001 | FastAPI BFF pattern | Accepted |
| ADR-002 | PostgreSQL + pgvector for vector storage | Accepted |
| ADR-003 | PyMuPDF for OCR, optional PaddleOCR | Accepted |
| ADR-004 | RQ (Redis Queue) for async jobs | Accepted |
| ADR-005 | LLM Manager multi-provider (Stub/Ollama/OpenAI) | Accepted |
| ADR-006 | JWT auth bridged from HMS | Accepted |
| ADR-007 | Local-first PHI processing | Accepted |

---

## 21. Ownership

| Scope | Owner |
|-------|-------|
| Architecture | System Architect |
| Backend | Backend Lead |
| Frontend | Frontend Lead |
| Database | Backend Lead |
| Security | Security Lead |
| QA | QA Lead |
| DevOps | DevOps Lead |

---

## 22. Open Questions

| ID | Question | Owner | Status |
|----|----------|-------|--------|
| OPEN-001 | Production LLM model choice (Qwen2.5 7B vs larger) | Tech Lead | Open |
| OPEN-002 | Dedicated embedding service needed? | Backend Lead | Open |
| OPEN-003 | Backup strategy for PostgreSQL + pgvector | DevOps Lead | Open |
| OPEN-004 | Monitoring stack (Prometheus/Grafana vs cloud) | DevOps Lead | Open |

---

## 23. Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 0.1.0 | 2026-04-27 | System Architect | Initial draft |
| 1.0.0 | 2026-06-14 | Agent | Completed from codebase analysis — 14 routes, 13 tables, LLM Manager, RQ workers, 7 ADRs |
