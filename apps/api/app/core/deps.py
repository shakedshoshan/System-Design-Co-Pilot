"""Dependency injection for the API. Call dependencies in route handlers like:

async def my_route(request_id: RequestIdDep, db: DbSessionDep, llm: LlmDep):
    ...

explanation:
- RequestIdDep: get the request ID from the request context
- DbSessionDep: get the database session
- LlmDep: get the LLM provider
- SettingsDep: get the settings
"""

from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.exceptions import AppError
from app.core.request_context import get_request_id, new_request_id
from app.db.session import get_db
from app.services.llm.openai_provider import OpenAILLMProvider


def require_request_id() -> str:
    return get_request_id() or new_request_id()


SettingsDep = Annotated[Settings, Depends(get_settings)]
RequestIdDep = Annotated[str, Depends(require_request_id)]
DbSessionDep = Annotated[Session, Depends(get_db)]


def get_llm_provider(request: Request, settings: Settings) -> OpenAILLMProvider:
    client = getattr(request.app.state, "openai_client", None)
    if client is None:
        raise AppError(
            code="llm_not_configured",
            message="OPENAI_API_KEY is not set or the LLM client is unavailable.",
            status_code=503,
        )
    return OpenAILLMProvider(client, settings.llm_model)


LlmDep = Annotated[OpenAILLMProvider, Depends(get_llm_provider)]
