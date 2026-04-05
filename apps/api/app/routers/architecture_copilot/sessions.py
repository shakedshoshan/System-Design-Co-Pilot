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
    ArchitectureArtifactRef,
    ArchitectureRunRequest,
    ArchitectureRunResult,
    ChatRequest,
    ChatResult,
    CreateSessionRequest,
    SessionSummary,
    UpdateSessionRequest,
)
from app.schemas.responses import success_body
from app.services.llm.guardrails import sanitize_assistant_output, sanitize_user_message
from app.services.llm.prompts import DEFAULT_SYSTEM_PROMPT
from app.services.phase1.runner import run_phase1_turn
from app.services.phase2.runner import run_phase2_pipeline, session_has_prd

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


@router.patch("/{session_id}")
def update_session(
    session_id: UUID,
    body: UpdateSessionRequest,
    db: DbSessionDep,
    request_id: RequestIdDep,
) -> dict:
    """Move session to the architecture phase after a PRD exists (Step 6)."""
    row = db.get(DesignSession, session_id)
    if row is None:
        raise AppError(
            code="session_not_found",
            message="Session not found.",
            status_code=404,
        )
    if row.phase not in ("product", "architecture"):
        raise AppError(
            code="invalid_phase_transition",
            message="Session phase is not eligible for this update.",
            status_code=400,
        )
    if row.phase == "architecture":
        summary = SessionSummary(id=row.id, title=row.title, phase=row.phase)
        return success_body({"session": summary.model_dump(mode="json")}, request_id=request_id)
    if not session_has_prd(db, session_id):
        raise AppError(
            code="prd_required",
            message="Save a PRD artifact before moving to the architecture phase.",
            status_code=400,
        )
    row.phase = "architecture"
    db.commit()
    db.refresh(row)
    summary = SessionSummary(id=row.id, title=row.title, phase=row.phase)
    return success_body({"session": summary.model_dump(mode="json")}, request_id=request_id)


@router.post("/{session_id}/architecture/run")
async def run_architecture_pipeline(
    session_id: UUID,
    body: ArchitectureRunRequest,
    db: DbSessionDep,
    settings: SettingsDep,
    llm: LlmDep,
    request_id: RequestIdDep,
) -> dict:
    """Run the five-agent architecture graph and persist versioned artifacts."""
    session = db.get(DesignSession, session_id)
    if session is None:
        raise AppError(
            code="session_not_found",
            message="Session not found.",
            status_code=404,
        )
    if session.phase != "architecture":
        raise AppError(
            code="invalid_phase",
            message="Session must be in the architecture phase. PATCH phase first.",
            status_code=400,
        )
    if not session_has_prd(db, session_id):
        raise AppError(
            code="prd_required",
            message="A PRD artifact is required to run the architecture pipeline.",
            status_code=400,
        )

    notes = (body.notes or "").strip()
    user_msg_id: UUID | None = None
    if notes:
        user_text = sanitize_user_message(notes, max_chars=32_000)
        user_msg = Message(session_id=session_id, role="user", content=user_text)
        db.add(user_msg)
        db.flush()
        user_msg_id = user_msg.id

    try:
        result = await run_phase2_pipeline(
            db,
            session_id,
            settings,
            llm,
            user_notes=notes,
        )
    except openai.RateLimitError as e:
        db.rollback()
        logger.warning("architecture_run_rate_limited", extra={"session_id": str(session_id)})
        raise AppError(
            code="llm_rate_limited",
            message="The model provider rate limit was hit. Try again shortly.",
            status_code=429,
            details={"provider": "openai"},
        ) from e
    except openai.APIError as e:
        db.rollback()
        logger.warning(
            "architecture_run_provider_error",
            extra={"session_id": str(session_id), "err": type(e).__name__},
        )
        raise AppError(
            code="llm_provider_error",
            message="The language model request failed.",
            status_code=502,
            details={"provider": "openai", "error_type": type(e).__name__},
        ) from e

    reply = sanitize_assistant_output(
        result.assistant_summary,
        max_chars=settings.llm_max_output_chars,
    )
    assistant_msg = Message(session_id=session_id, role="assistant", content=reply)
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    payload = ArchitectureRunResult(
        user_message_id=user_msg_id,
        assistant_message_id=assistant_msg.id,
        assistant_content=reply,
        artifacts=[
            ArchitectureArtifactRef(
                artifact_type=a.artifact_type,
                id=a.id,
                version=a.version,
            )
            for a in result.artifacts
        ],
    )
    return success_body({"architecture_run": payload.model_dump(mode="json")}, request_id=request_id)


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

    # `synthesize_prd` skips waiting for guided agent's ready_for_prd and runs PRD synthesis.
    force_prd = body.product_action == "synthesize_prd"

    # Step 5: product phase uses LangGraph (guided Q → optional PRD). Other phases keep Step 4 single-call chat.
    if session.phase == "product":
        try:
            phase1 = await run_phase1_turn(
                db,
                session_id,
                settings,
                llm,
                force_synthesize=force_prd,
            )
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
            phase1.assistant_reply, max_chars=settings.llm_max_output_chars
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
            prd_artifact_id=phase1.prd_artifact_id,
            prd_version=phase1.prd_version,
            phase1_ready_for_architecture=phase1.wrote_prd,
        )
        return success_body({"chat": result.model_dump(mode="json")}, request_id=request_id)

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
        prd_artifact_id=None,
        prd_version=None,
        phase1_ready_for_architecture=None,
    )
    return success_body({"chat": result.model_dump(mode="json")}, request_id=request_id)
