"""Main entry point and application factory for the Hospital AI Knowledge Assistant API.
Điểm vào chính (entry point) và nhà máy tạo ứng dụng FastAPI cho Hệ thống Trợ lý Tri thức Y tế AI.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from hospital_ai.api.limiter import limiter
from hospital_ai.api.router import api_router
from hospital_ai.api.routes import metrics_endpoint
from hospital_ai.core.config import Settings, get_settings
from hospital_ai.core.errors import (
    AppError,
    ExternalServiceError,
    NotFoundError,
    PermissionDeniedError,
    ValidationAppError,
)
from hospital_ai.core.exceptions import (
    AuthenticationException,
    CitationHallucinationException,
    DocumentProcessingException,
    EmbeddingProviderException,
    EntityNotFoundException,
    HMSIntegrationException,
    LLMProviderException,
    MedicalDataAccessException,
    PermissionDeniedException,
    RAGRetrievalException,
    ValidationException,
)
from hospital_ai.core.logging import configure_logging
from hospital_ai.core.telemetry import setup_metrics, setup_telemetry

# ── Domain Exception → HTTP Status Code Mapping ─────────────────────
# Keeps the domain layer framework-free — only the presentation layer
# (this file) knows about HTTP status codes.
DOMAIN_EXCEPTION_STATUS_MAP: dict[type[AppError], int] = {
    # Security / Access Control
    MedicalDataAccessException: 403,
    PermissionDeniedException: 403,
    PermissionDeniedError: 403,
    AuthenticationException: 401,
    # AI / RAG Quality
    CitationHallucinationException: 422,
    RAGRetrievalException: 502,
    # Document Processing
    DocumentProcessingException: 422,
    # External Integration
    HMSIntegrationException: 502,
    LLMProviderException: 502,
    EmbeddingProviderException: 502,
    ExternalServiceError: 502,
    # Data Integrity
    EntityNotFoundException: 404,
    NotFoundError: 404,
    ValidationException: 400,
    ValidationAppError: 422,
}


def _resolve_status_code(exc: AppError) -> int:
    """Map a domain exception to its HTTP status code.
    Chuyển đổi (map) ngoại lệ nghiệp vụ (domain exception) sang mã trạng thái HTTP tương ứng.

    Walks the MRO to find the most specific registered mapping.
    Falls back to 500 for unregistered exception types.
    Duyệt thứ tự kế thừa (MRO) để tìm mã HTTP phù hợp nhất. Trả về 500 cho ngoại lệ không xác định.
    """
    for cls in type(exc).__mro__:
        if cls in DOMAIN_EXCEPTION_STATUS_MAP:
            return DOMAIN_EXCEPTION_STATUS_MAP[cls]
    return 500


def create_app(settings: Settings | None = None) -> FastAPI:
    """Factory function to create and configure the FastAPI application.
    Hàm nhà máy (factory function) khởi tạo và cấu hình toàn bộ ứng dụng FastAPI.

    Args:
        settings: Optional Settings override (defaults to get_settings()).
                  Tùy chọn ghi đè cấu hình Settings (mặc định lấy từ `get_settings()`).

    Returns:
        Configured FastAPI application instance.
        Đối tượng ứng dụng FastAPI đã được thiết lập đầy đủ router, middleware và handler.
    """
    active_settings = settings or get_settings()
    configure_logging()
    setup_metrics(active_settings)
    setup_telemetry()

    app = FastAPI(
        title="Hospital AI Knowledge Assistant API",
        version="0.1.0",
        default_response_class=JSONResponse,
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    if active_settings.cors_origin_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=active_settings.cors_origin_list,
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    app.include_router(api_router, prefix=active_settings.api_v1_prefix)
    app.include_router(metrics_endpoint.router)

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        """Catch all domain exceptions and map them to HTTP JSON responses.
        Bắt toàn bộ các ngoại lệ nghiệp vụ (domain exception) và chuyển thành phản hồi HTTP JSON chuẩn.

        Uses DOMAIN_EXCEPTION_STATUS_MAP to resolve the appropriate status
        code based on the exception's MRO. All domain exceptions produce
        a consistent JSON envelope with code, message, and metadata.
        Sử dụng DOMAIN_EXCEPTION_STATUS_MAP để xác định mã status code phù hợp.
        Tất cả phản hồi đều tuân theo cấu trúc JSON chuẩn gồm code, message và metadata.
        """
        status_code = _resolve_status_code(exc)
        return JSONResponse(
            status_code=status_code,
            content={"error": exc.code, "message": exc.message, "metadata": exc.metadata},
        )

    return app
