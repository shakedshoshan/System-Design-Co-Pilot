from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.deps import RequestIdDep, SettingsDep
from app.schemas.responses import Meta, SuccessEnvelope, error_body
from app.services.db_ping import check_database

router = APIRouter(tags=["health"])


@router.get("/health", response_model=SuccessEnvelope)
def health(request_id: RequestIdDep) -> SuccessEnvelope:
    return SuccessEnvelope(data={"status": "ok"}, meta=Meta(request_id=request_id))


@router.get("/ready", response_model=SuccessEnvelope)
def ready(
    settings: SettingsDep,
    request_id: RequestIdDep,
) -> JSONResponse | SuccessEnvelope:
    if not settings.database_url:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=error_body(
                code="not_ready",
                message="Database URL is not configured",
                request_id=request_id,
                details={"database": "not_configured"},
            ),
        )
    try:
        check_database(settings.database_url)
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=error_body(
                code="not_ready",
                message="Database is not reachable",
                request_id=request_id,
                details={"database": "unreachable"},
            ),
        )
    return SuccessEnvelope(
        data={"status": "ok", "database": "connected"},
        meta=Meta(request_id=request_id),
    )
