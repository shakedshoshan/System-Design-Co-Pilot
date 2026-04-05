from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


class Meta(BaseModel):
    request_id: str
    timestamp: str = Field(default_factory=utc_now_iso)


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Any | None = None


class ErrorEnvelope(BaseModel):
    error: ErrorDetail
    meta: Meta


class SuccessEnvelope(BaseModel):
    data: dict[str, Any]
    meta: Meta


def success_body(data: dict[str, Any], *, request_id: str) -> dict[str, Any]:
    return SuccessEnvelope(data=data, meta=Meta(request_id=request_id)).model_dump()


def error_body(
    *,
    code: str,
    message: str,
    request_id: str,
    details: Any | None = None,
) -> dict[str, Any]:
    return ErrorEnvelope(
        error=ErrorDetail(code=code, message=message, details=details),
        meta=Meta(request_id=request_id),
    ).model_dump()
