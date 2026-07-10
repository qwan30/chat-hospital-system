# Báo cáo Kiểm thử Phase 2

## 1. Backend API & Auth
- **Trạng thái chạy test**: Thất bại (Lỗi cấu hình/tương thích phiên bản Python).
- **Lỗi phát sinh**: `ImportError while loading conftest`. Cụ thể, khi parse annotation `Mapped[str | None]` trong file `src/hospital_ai/db/models.py`, SQLAlchemy văng lỗi `MappedAnnotationError: Could not resolve all types within mapped annotation: "Mapped[str | None]"`. Nguyên nhân có thể do chạy bằng môi trường Python không tương thích với cú pháp union type (ví dụ Python 3.9) hoặc thiếu `from __future__ import annotations`.
- **Số lượng pass/fail**: 0 pass / 0 fail (Test chưa thể khởi chạy vì lỗi nạp môi trường).
- **Coverage**: N/A.

## 2. HMS Data Sync
- **Trạng thái chạy test**: Thất bại (Bị chặn bởi lỗi syntax cục bộ).
- **Lỗi phát sinh**: `MappedAnnotationError: Could not resolve all types within mapped annotation: "Mapped[str | None]"`. Lỗi cấu hình Python 3.9 tương tự như phần API & Auth đã chặn toàn bộ quá trình chạy test của file `test_hms_sync.py` và `test_hms_appointment_import.py`.
- **Số lượng pass/fail**: 0 pass / 0 fail.
- **Vấn đề bảo mật (PHI leakage)**: Chưa thể xác minh bằng test tự động do không thể khởi chạy test. Cần khắc phục lỗi môi trường/syntax để đảm bảo các bài test xác minh ngăn chặn rò rỉ dữ liệu y tế (PHI) được thực thi thành công.

## 3. Graph RAG & AI Engine
- **Trạng thái chạy test**: Thất bại (Bị chặn bởi lỗi syntax cục bộ).
- **Lỗi phát sinh**: `MappedAnnotationError: Could not resolve all types within mapped annotation: "Mapped[str | None]"`. Tương tự như các phần trước, lỗi cấu hình Python 3.9 tại `src/hospital_ai/db/models.py` đã làm sập `conftest`, ngăn chặn hoàn toàn việc thực thi các bài test liên quan đến Graph RAG và AI Engine.
- **Số lượng pass/fail**: 0 pass / 0 fail.
- **Đánh giá rủi ro**: Việc không thể chạy test tự động cho luồng AI/RAG mang lại rủi ro rất cao. Không có test tự động, chúng ta không thể đảm bảo quá trình Graph RAG truy xuất đúng tài liệu, không đánh giá được chất lượng truy vấn, và đặc biệt là không thể tự động xác minh tính an toàn (Safe refusal) đối với các câu hỏi không hợp lệ hoặc thông tin ngoài miền, dẫn đến nguy cơ cao sinh ra thông tin ảo (hallucination) trong môi trường y tế.

## 4. Frontend UI Components
*(Sẽ cập nhật sau)*

## 5. Tổng kết Phase 2
*(Sẽ cập nhật sau)*
