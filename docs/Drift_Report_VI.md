# Báo Cáo Lệch Pha Code & Document (Drift Report)

Báo cáo này liệt kê chi tiết các điểm sai lệch giữa tài liệu thiết kế và hiện trạng mã nguồn thực tế.

## 1. Lệch Pha về Testing (Test Plan vs Tests)
- **Cấu trúc thư mục E2E Frontend**: Tài liệu `docs/09-testing/test-plan.md` (Mục 5.1 & 5.2) đề cập đến việc sử dụng thư mục `app/frontend/e2e/flows/` và `e2e/helpers/`. Tuy nhiên, trong thực tế toàn bộ các file test nằm phẳng tại thư mục `app/frontend/e2e/`, không có thư mục `flows/` hay `helpers/`.
- **Thiếu file helpers E2E**: Tài liệu định nghĩa `e2e/helpers/auth.ts` và `e2e/helpers/interactions.ts` nhưng thực tế chỉ có một file `_helpers.ts` nằm ngang hàng.
- **Tên các bộ test E2E**: Tài liệu chỉ ra 6 bộ test cụ thể (`login-flow`, `chat-flow`, `patient-flow`, `document-flow`, `navigation-flow`, `error-flow`). Thực tế mã nguồn có các file test với tên khác: `auth-flow.spec.ts`, `business-flow.spec.ts`, `chat-general.spec.ts`, `chat-gpt-flow.spec.ts`, `chat-patient.spec.ts`, `full-plan-verification.spec.ts`, `graph-patient.spec.ts`, `rbac-flow.spec.ts`, `screenshot-all.spec.ts`.
- **Thay đổi tên test RAG Backend**: Trong thực tế các file test RAG được chia tách chuyên biệt với các tên cụ thể thay vì chung chung, bao gồm: `test_rag_trace.py`, `test_graph_rag_integration.py`, `test_retrieval_postgres_integration.py`, `test_retrieval_sql.py`.

## 2. Lệch Pha về Architecture (Architecture Docs vs Code Structure)
- **Backend API Routes (API Layer)**: Tài liệu `docs/04-architecture/module-breakdown.md` liệt kê 14 route modules. Tuy nhiên, cấu trúc thực tế trong `app/backend/src/hospital_ai/api/routes/` bao gồm 16 modules. Hai route `graph.py` và `medication_safety.py` có trong code nhưng chưa được ghi nhận trong document.
- **Backend Services (Service Layer)**: Tài liệu định nghĩa 18 modules trong service layer. Trong thực tế, thư mục `app/backend/src/hospital_ai/services/` chứa nhiều file và thư mục hơn (như `chunking.py`, `jwt_auth.py`, `memory.py`, `ocr.py`, `reranking.py`, `storage.py` và thư mục `loaders/`) nhưng chưa được cập nhật vào tài liệu.
- **Frontend Components Structure**: Theo tài liệu, frontend components được phân chia theo rất nhiều domain cụ thể (như `app-shell/`, `auth/`, `chat/`, `patient/`, `document/`, `evidence/`,...). Nhưng thực tế, mã nguồn tại `app/frontend/src/components/` chỉ có 3 thư mục `hms/`, `shell/`, và `ui/`. Phần lớn các feature components đang nằm gộp chung trong thư mục `components/hms/` thay vì chia nhỏ theo domain như kiến trúc quy định.

## 3. Lệch Pha về API (API Docs vs Backend Endpoints)
- **Thiếu endpoints trong tài liệu (Undocumented Endpoints)**: Rất nhiều endpoints có trong code nhưng không được nhắc đến trong `api-contract.md`:
  - `access_requests.py`: Có thêm `GET /`, `GET /{request_id}`, `PUT /{request_id}/review`.
  - `audit.py`: Có thêm `GET /events`.
  - `chat_threads.py`: Thiếu toàn bộ các endpoints liên quan đến messages và participants (như `POST/GET /{thread_id}/messages`, các operations CRUD cho participants, cập nhật và xóa thread).
  - `documents.py`: Có thêm truy xuất page (`GET /{document_id}/pages/{page_number}`, `.../image`) và tìm kiếm (`POST /search`).
  - Toàn bộ endpoints của `graph.py` và `medication_safety.py` hoàn toàn không có trong API Docs.
  - `hms.py`: Có thêm nhiều endpoint đồng bộ chi tiết như `/sync/appointments`, `/sync/lab-results`, `/sync/medical-records`, `/sync/full` và `GET /health`.
  - `patients.py`: Có thêm `GET /search` và `GET /{patient_id}/timeline`.
- **Sai lệch đường dẫn (Path Drift)**:
  - `documents.py`: Docs ghi `POST /api/v1/documents/upload`, nhưng code thực tế là `POST /`. Docs ghi `/{id}/retry-ocr`, nhưng code là `/{document_id}/retry-index`.
- **Endpoints có trong Docs nhưng không có trong Code (Ghost Endpoints)**:
  - `GET /api/v1/hms/jobs/{job_id}`: Không tồn tại trong mã nguồn.
  - `GET /api/v1/patients`: Trong code dùng `GET /search` thay vì `GET /`.
  - `GET /api/v1/patients/{id}/summary` và `GET /api/v1/patients/{id}/meds`: Không tồn tại trong `patients.py` (tính năng medication review đã được chuyển sang module riêng `medication_safety.py`).

## 4. Đánh giá Tổng quan & Đề xuất Cập nhật
(Chưa có dữ liệu)
