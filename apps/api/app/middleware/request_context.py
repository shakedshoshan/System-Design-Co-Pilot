from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.request_context import new_request_id, set_request_id

_REQUEST_ID_HEADER = "X-Request-ID"


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach a stable request id for logs, responses, and tracing."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        incoming = request.headers.get(_REQUEST_ID_HEADER)
        rid = incoming.strip() if incoming and incoming.strip() else new_request_id()
        set_request_id(rid)
        response = await call_next(request)
        response.headers[_REQUEST_ID_HEADER] = rid
        return response
