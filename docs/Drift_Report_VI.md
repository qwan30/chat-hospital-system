# Báo Cáo Lệch Pha Code & Document (Drift Report)

Báo cáo này liệt kê chi tiết các điểm sai lệch giữa tài liệu thiết kế và hiện trạng mã nguồn thực tế.

## 1. Lệch Pha về Testing (Test Plan vs Tests)
- **Cấu trúc thư mục E2E Frontend**: Tài liệu `docs/09-testing/test-plan.md` (Mục 5.1 & 5.2) đề cập đến việc sử dụng thư mục `app/frontend/e2e/flows/` và `e2e/helpers/`. Tuy nhiên, trong thực tế toàn bộ các file test nằm phẳng tại thư mục `app/frontend/e2e/`, không có thư mục `flows/` hay `helpers/`.
- **Thiếu file helpers E2E**: Tài liệu định nghĩa `e2e/helpers/auth.ts` và `e2e/helpers/interactions.ts` nhưng thực tế chỉ có một file `_helpers.ts` nằm ngang hàng.
- **Tên các bộ test E2E**: Tài liệu chỉ ra 6 bộ test cụ thể (`login-flow`, `chat-flow`, `patient-flow`, `document-flow`, `navigation-flow`, `error-flow`). Thực tế mã nguồn có các file test với tên khác: `auth-flow.spec.ts`, `business-flow.spec.ts`, `chat-general.spec.ts`, `chat-gpt-flow.spec.ts`, `chat-patient.spec.ts`, `full-plan-verification.spec.ts`, `graph-patient.spec.ts`, `rbac-flow.spec.ts`, `screenshot-all.spec.ts`.
- **Thay đổi tên test RAG Backend**: Trong thực tế các file test RAG được chia tách chuyên biệt với các tên cụ thể thay vì chung chung, bao gồm: `test_rag_trace.py`, `test_graph_rag_integration.py`, `test_retrieval_postgres_integration.py`, `test_retrieval_sql.py`.

## 2. Lệch Pha về Architecture (Architecture Docs vs Code Structure)
(Chưa có dữ liệu)

## 3. Lệch Pha về API (API Docs vs Backend Endpoints)
(Chưa có dữ liệu)

## 4. Đánh giá Tổng quan & Đề xuất Cập nhật
(Chưa có dữ liệu)
