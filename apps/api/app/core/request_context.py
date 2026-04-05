from contextvars import ContextVar
from uuid import uuid4

_request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_request_id() -> str | None:
    return _request_id_ctx.get()


def set_request_id(value: str | None) -> None:
    _request_id_ctx.set(value)


def new_request_id() -> str:
    return str(uuid4())
