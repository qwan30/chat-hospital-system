"""Các lớp lỗi (Exceptions) mức ứng dụng có định nghĩa sẵn HTTP status_code và mã lỗi code.

Phục vụ việc trả về nhanh phản hồi lỗi qua các middleware hay router API đơn giản.
"""

from typing import Any


class AppError(Exception):
    """Lớp lỗi nền tảng cho các exception có kèm mã trạng thái HTTP (mặc định 500)."""
    status_code = 500
    code = "APP_ERROR"

    def __init__(self, message: str, metadata: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.metadata = metadata or {}


class PermissionDeniedError(AppError):
    """Lỗi từ chối quyền truy cập (HTTP 403 Forbidden)."""
    status_code = 403
    code = "FORBIDDEN"


class NotFoundError(AppError):
    """Lỗi không tìm thấy dữ liệu hoặc tài nguyên yêu cầu (HTTP 404 Not Found)."""
    status_code = 404
    code = "NOT_FOUND"


class ValidationAppError(AppError):
    """Lỗi xác thực dữ liệu đầu vào không hợp lệ (HTTP 422 Unprocessable Entity)."""
    status_code = 422
    code = "VALIDATION_ERROR"


class ExternalServiceError(AppError):
    """Lỗi giao tiếp với dịch vụ bên ngoài như HMS hoặc LLM API (HTTP 502 Bad Gateway)."""
    status_code = 502
    code = "EXTERNAL_SERVICE_ERROR"

