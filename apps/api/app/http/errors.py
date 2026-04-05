import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.request_context import get_request_id, new_request_id
from app.schemas.responses import error_body

logger = logging.getLogger("app.errors")


def _request_id() -> str:
    return get_request_id() or new_request_id()


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> object:
        return _json(
            exc.status_code,
            error_body(
                code=exc.code,
                message=exc.message,
                request_id=_request_id(),
                details=exc.details,
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        _request: Request,
        exc: StarletteHTTPException,
    ) -> object:
        detail = exc.detail
        if isinstance(detail, str):
            message = detail
            details = None
        else:
            message = "Request could not be completed"
            details = detail
        code = f"http_{exc.status_code}"
        return _json(
            exc.status_code,
            error_body(
                code=code,
                message=message,
                request_id=_request_id(),
                details=details,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(
        _request: Request,
        exc: RequestValidationError,
    ) -> object:
        return _json(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_body(
                code="validation_error",
                message="Request validation failed",
                request_id=_request_id(),
                details=exc.errors(),
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        _request: Request,
        exc: Exception,
    ) -> object:
        rid = _request_id()
        logger.exception(
            "unhandled_exception",
            extra={"request_id": rid},
        )
        settings = get_settings()
        if settings.app_env == "production":
            message = "An unexpected error occurred"
            details = None
        else:
            message = str(exc)
            details = {"type": type(exc).__name__}
        return _json(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_body(
                code="internal_error",
                message=message,
                request_id=rid,
                details=details,
            ),
        )


def _json(status_code: int, content: dict[str, object]) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=content)
