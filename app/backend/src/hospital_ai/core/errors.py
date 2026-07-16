from typing import Any, Optional


class AppError(Exception):
    status_code = 500
    code = "APP_ERROR"

    def __init__(self, message: str, metadata: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.metadata = metadata or {}


class PermissionDeniedError(AppError):
    status_code = 403
    code = "FORBIDDEN"


class NotFoundError(AppError):
    status_code = 404
    code = "NOT_FOUND"


class ValidationAppError(AppError):
    status_code = 422
    code = "VALIDATION_ERROR"


class ExternalServiceError(AppError):
    status_code = 502
    code = "EXTERNAL_SERVICE_ERROR"
