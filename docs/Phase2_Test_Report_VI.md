# Báo cáo Kiểm thử Phase 2

## 1. Backend API & Auth
- **Trạng thái chạy test**: Thất bại (Lỗi cấu hình/tương thích phiên bản Python).
- **Lỗi phát sinh**: `ImportError while loading conftest`. Cụ thể, khi parse annotation `Mapped[str | None]` trong file `src/hospital_ai/db/models.py`, SQLAlchemy văng lỗi `MappedAnnotationError: Could not resolve all types within mapped annotation: "Mapped[str | None]"`. Nguyên nhân có thể do chạy bằng môi trường Python không tương thích với cú pháp union type (ví dụ Python 3.9) hoặc thiếu `from __future__ import annotations`.
- **Số lượng pass/fail**: 0 pass / 0 fail (Test chưa thể khởi chạy vì lỗi nạp môi trường).
- **Coverage**: N/A.

## 2. HMS Data Sync
*(Sẽ cập nhật sau)*

## 3. Graph RAG & AI Engine
*(Sẽ cập nhật sau)*

## 4. Frontend UI Components
*(Sẽ cập nhật sau)*

## 5. Tổng kết Phase 2
*(Sẽ cập nhật sau)*
