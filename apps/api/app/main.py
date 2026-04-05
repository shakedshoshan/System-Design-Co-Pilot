from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging_config import setup_logging
from app.http.errors import register_exception_handlers
from app.middleware.access_log import AccessLogMiddleware
from app.middleware.request_context import RequestContextMiddleware
from app.routers import health
from app.routers.architecture_copilot import router as architecture_copilot_router


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(
        json_logs=settings.json_logs,
        level=settings.log_level_int,
        log_file=settings.resolved_log_file,
        log_max_bytes=settings.log_max_mb * 1024 * 1024,
        log_backup_count=settings.log_backup_count,
    )
    application = FastAPI(
        title="System Design Co-Pilot API",
        description=(
            "JSON responses use a common envelope: success `{data, meta}`, "
            "errors `{error, meta}`. Pass `X-Request-ID` or receive one in the response."
        ),
    )
    register_exception_handlers(application)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )
    application.add_middleware(AccessLogMiddleware)
    application.add_middleware(RequestContextMiddleware)
    application.include_router(health.router)
    application.include_router(architecture_copilot_router)
    return application


app = create_app()
