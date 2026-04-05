import logging
import time
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.request_context import get_request_id

logger = logging.getLogger("app.http")


class AccessLogMiddleware(BaseHTTPMiddleware):
    """Structured access log (stdout / file) with timing for monitoring."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        start = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            rid = get_request_id() or "-"
            logger.info(
                "%s %s -> %s (%sms)",
                request.method,
                request.url.path,
                status_code,
                duration_ms,
                extra={
                    "request_id": rid,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                },
            )
