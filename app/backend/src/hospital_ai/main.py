from typing import Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from hospital_ai.api.router import api_router
from hospital_ai.core.config import Settings, get_settings
from hospital_ai.core.errors import AppError
from hospital_ai.core.logging import configure_logging


def create_app(settings: Optional[Settings] = None) -> FastAPI:
    active_settings = settings or get_settings()
    configure_logging()

    app = FastAPI(
        title="Hospital AI Knowledge Assistant API",
        version="0.1.0",
        default_response_class=JSONResponse,
    )
    if active_settings.cors_origin_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=active_settings.cors_origin_list,
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    app.include_router(api_router, prefix=active_settings.api_v1_prefix)

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.code, "message": exc.message, "metadata": exc.metadata},
        )

    return app
