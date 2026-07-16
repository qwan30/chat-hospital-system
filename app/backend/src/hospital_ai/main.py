from typing import Optional

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

    Walks the MRO to find the most specific registered mapping.
    Falls back to 500 for unregistered exception types.
    """
    for cls in type(exc).__mro__:
        if cls in DOMAIN_EXCEPTION_STATUS_MAP:
            return DOMAIN_EXCEPTION_STATUS_MAP[cls]
    return 500


def create_app(settings: Optional[Settings] = None) -> FastAPI:
    """Factory function to create and configure the FastAPI application.

    Args:
        settings: Optional Settings override (defaults to get_settings()).

    Returns:
        Configured FastAPI application instance.
    """
    active_settings = settings or get_settings()
    configure_logging(log_format=active_settings.log_format)
    setup_metrics(active_settings)
    setup_telemetry()

    app = FastAPI(
        title="Hospital AI Knowledge Assistant API",
        version="0.1.0",
        default_response_class=JSONResponse,
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Instrument FastAPI with OpenTelemetry if enabled
    if active_settings.otel_enabled:
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
            FastAPIInstrumentor().instrument_app(app)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("Failed to instrument FastAPI with OpenTelemetry: %s", e)

    # Instrument FastAPI with Prometheus if enabled
    if active_settings.prometheus_enabled:
        try:
            from prometheus_fastapi_instrumentator import Instrumentator
            Instrumentator().instrument(app).expose(app, endpoint="/metrics")
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("Failed to initialize Prometheus metrics: %s", e)

    if active_settings.cors_origin_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=active_settings.cors_origin_list,
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    app.include_router(api_router, prefix=active_settings.api_v1_prefix)
    if active_settings.prometheus_enabled:
        app.include_router(metrics_endpoint.router)

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        """Catch all domain exceptions and map them to HTTP JSON responses.

        Uses DOMAIN_EXCEPTION_STATUS_MAP to resolve the appropriate status
        code based on the exception's MRO. All domain exceptions produce
        a consistent JSON envelope with code, message, and metadata.
        """
        status_code = _resolve_status_code(exc)
        return JSONResponse(
            status_code=status_code,
            content={"error": exc.code, "message": exc.message, "metadata": exc.metadata},
        )

    return app
