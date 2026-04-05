from typing import Annotated

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.core.request_context import get_request_id, new_request_id


def require_request_id() -> str:
    return get_request_id() or new_request_id()


SettingsDep = Annotated[Settings, Depends(get_settings)]
RequestIdDep = Annotated[str, Depends(require_request_id)]
