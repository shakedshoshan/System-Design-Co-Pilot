from __future__ import annotations

import logging
from uuid import UUID

import openai
from fastapi import APIRouter, status
from sqlalchemy import select

from app.core.deps import DbSessionDep, LlmDep, RequestIdDep, SettingsDep
from app.core.exceptions import AppError
from app.db.models import DesignSession, Message
from app.schemas.architecture_copilot.sessions import (
    ChatRequest,
    ChatResult,
    CreateSessionRequest,
    SessionSummary,
)
from app.schemas.responses import success_body
from app.services.llm.guardrails import sanitize_assistant_output, sanitize_user_message
from app.services.llm.prompts import DEFAULT_SYSTEM_PROMPT

logger = logging.getLogger("app.sessions")

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED)
def create_session(
    body: CreateSessionRequest,
    db: DbSessionDep,
    request_id: RequestIdDep,
) -> dict:
    """Create an empty design session (needed to call chat before a UI exists)."""
    row = DesignSession(title=body.title)
    db.add(row)
    db.commit()
    db.refresh(row)
    summary = SessionSummary(id=row.id, title=row.title, phase=row.phase)
    return success_body({"session": summary.model_dump(mode="json")}, request_id=request_id)


@router.post("/{session_id}/chat")
async def chat_in_session(
    session_id: UUID,
    body: ChatRequest,
    db: DbSessionDep,
    settings: SettingsDep,
    llm: LlmDep,
    request_id: RequestIdDep,
) -> dict:
    session = db.get(DesignSession, session_id)
    if session is None:
        raise AppError(
            code="session_not_found",
            message="Session not found.",
            status_code=404,
        )

    user_text = sanitize_user_message(body.content, max_chars=32_000)
    user_msg = Message(session_id=session_id, role="user", content=user_text)
    db.add(user_msg)
    db.flush()

    stmt = (
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.desc())
        .limit(settings.llm_context_message_limit)
    )
    history = list(reversed(list(db.scalars(stmt).all())))

    api_messages: list[dict[str, str]] = [
        {"role": "system", "content": DEFAULT_SYSTEM_PROMPT},
    ]
    for m in history:
        if m.role not in ("user", "assistant", "system"):
            continue
        api_messages.append({"role": m.role, "content": m.content})

    try:
        raw_reply = await llm.chat_completion(api_messages)
    except openai.RateLimitError as e:
        logger.warning("chat_rate_limited", extra={"session_id": str(session_id)})
        raise AppError(
            code="llm_rate_limited",
            message="The model provider rate limit was hit. Try again shortly.",
            status_code=429,
            details={"provider": "openai"},
        ) from e
    except openai.APIError as e:
        logger.warning(
            "chat_provider_error",
            extra={"session_id": str(session_id), "err": type(e).__name__},
        )
        raise AppError(
            code="llm_provider_error",
            message="The language model request failed.",
            status_code=502,
            details={"provider": "openai", "error_type": type(e).__name__},
        ) from e

    reply = sanitize_assistant_output(
        raw_reply, max_chars=settings.llm_max_output_chars
    )
    assistant_msg = Message(session_id=session_id, role="assistant", content=reply)
    db.add(assistant_msg)
    db.commit()
    db.refresh(user_msg)
    db.refresh(assistant_msg)

    result = ChatResult(
        user_message_id=user_msg.id,
        assistant_message_id=assistant_msg.id,
        assistant_content=reply,
    )
    return success_body({"chat": result.model_dump(mode="json")}, request_id=request_id)
