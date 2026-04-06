from __future__ import annotations

import logging
from uuid import UUID

import openai
from fastapi import APIRouter, Query, Request, Response, status
from sqlalchemy import select

from app.core.deps import DbSessionDep, RequestIdDep, SettingsDep, get_llm_provider
from app.core.exceptions import AppError
from app.db.models import Artifact, DesignSession, Message
from app.schemas.architecture_copilot.sessions import (
    ArchitectureArtifactRef,
    ArchitectureRunRequest,
    ArchitectureRunResult,
    ArtifactDetail,
    ArtifactMeta,
    ArtifactsListResult,
    ChatRequest,
    ChatResult,
    CreateSessionRequest,
    MessageItem,
    MessagesListResult,
    QueuedAgentRun,
    SessionListItem,
    SessionsListResult,
    SessionSummary,
    UpdateSessionRequest,
)
from app.schemas.responses import success_body
from app.services.events.publish import (
    new_job_keys,
    publish_phase1_enqueued,
    publish_phase2_enqueued,
    publish_session_created_if_enabled,
)
from app.services.llm.guardrails import sanitize_assistant_output, sanitize_user_message
from app.services.llm.prompts import DEFAULT_SYSTEM_PROMPT
from app.services.phase1.runner import run_phase1_turn
from app.services.phase2.runner import run_phase2_pipeline, session_has_prd

logger = logging.getLogger("app.sessions")

router = APIRouter()


@router.get("")
def list_sessions(
    db: DbSessionDep,
    request_id: RequestIdDep,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict:
    """List design sessions, most recently updated first."""
    stmt = (
        select(DesignSession)
        .order_by(DesignSession.updated_at.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = list(db.scalars(stmt).all())
    payload = SessionsListResult(
        sessions=[
            SessionListItem(
                id=r.id,
                title=r.title,
                phase=r.phase,
                updated_at=r.updated_at,
            )
            for r in rows
        ]
    )
    return success_body(payload.model_dump(mode="json"), request_id=request_id)


@router.get("/{session_id}/artifacts")
def list_session_artifacts(
    session_id: UUID,
    db: DbSessionDep,
    request_id: RequestIdDep,
) -> dict:
    """List artifact metadata for a session (no bodies)."""
    session = db.get(DesignSession, session_id)
    if session is None:
        raise AppError(
            code="session_not_found",
            message="Session not found.",
            status_code=404,
        )
    stmt = (
        select(Artifact)
        .where(Artifact.session_id == session_id)
        .order_by(Artifact.artifact_type.asc(), Artifact.version.desc())
    )
    rows = list(db.scalars(stmt).all())
    payload = ArtifactsListResult(
        artifacts=[
            ArtifactMeta(
                id=a.id,
                artifact_type=a.artifact_type,
                version=a.version,
                created_at=a.created_at,
            )
            for a in rows
        ]
    )
    return success_body(payload.model_dump(mode="json"), request_id=request_id)


@router.get("/{session_id}/artifacts/{artifact_id}")
def get_session_artifact(
    session_id: UUID,
    artifact_id: UUID,
    db: DbSessionDep,
    request_id: RequestIdDep,
) -> dict:
    """Fetch one artifact body (markdown/JSON text as stored)."""
    session = db.get(DesignSession, session_id)
    if session is None:
        raise AppError(
            code="session_not_found",
            message="Session not found.",
            status_code=404,
        )
    a = db.get(Artifact, artifact_id)
    if a is None or a.session_id != session_id:
        raise AppError(
            code="artifact_not_found",
            message="Artifact not found for this session.",
            status_code=404,
        )
    detail = ArtifactDetail(
        id=a.id,
        session_id=a.session_id,
        artifact_type=a.artifact_type,
        version=a.version,
        content=a.content,
        created_at=a.created_at,
    )
    return success_body({"artifact": detail.model_dump(mode="json")}, request_id=request_id)


@router.get("/{session_id}")
def get_session(
    session_id: UUID,
    db: DbSessionDep,
    request_id: RequestIdDep,
) -> dict:
    """Return one session for deep links / UI header."""
    row = db.get(DesignSession, session_id)
    if row is None:
        raise AppError(
            code="session_not_found",
            message="Session not found.",
            status_code=404,
        )
    item = SessionListItem(
        id=row.id,
        title=row.title,
        phase=row.phase,
        updated_at=row.updated_at,
    )
    return success_body({"session": item.model_dump(mode="json")}, request_id=request_id)


@router.get("/{session_id}/messages")
def list_session_messages(
    session_id: UUID,
    db: DbSessionDep,
    request_id: RequestIdDep,
    limit: int = Query(100, ge=1, le=500),
) -> dict:
    """List chat messages for a session (ascending by time). Use after 202 async chat/run."""
    session = db.get(DesignSession, session_id)
    if session is None:
        raise AppError(
            code="session_not_found",
            message="Session not found.",
            status_code=404,
        )
    stmt = (
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
        .limit(limit)
    )
    rows = list(db.scalars(stmt).all())
    payload = MessagesListResult(
        messages=[
            MessageItem(
                id=m.id,
                role=m.role,
                content=m.content,
                created_at=m.created_at,
                extra=m.extra,
            )
            for m in rows
        ]
    )
    return success_body({"messages": payload.model_dump(mode="json")}, request_id=request_id)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_session(
    body: CreateSessionRequest,
    db: DbSessionDep,
    request_id: RequestIdDep,
    request: Request,
    settings: SettingsDep,
) -> dict:
    """Create an empty design session (needed to call chat before a UI exists)."""
    row = DesignSession(title=body.title)
    db.add(row)
    db.commit()
    db.refresh(row)
    await publish_session_created_if_enabled(
        request=request,
        settings=settings,
        session_id=row.id,
        title=row.title,
        phase=row.phase,
        created_at=row.created_at,
    )
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
    request_id: RequestIdDep,
    request: Request,
    response: Response,
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

    if settings.kafka_enabled and settings.kafka_async_runs:
        producer = getattr(request.app.state, "kafka_producer", None)
        if producer is None:
            raise AppError(
                code="kafka_unavailable",
                message="Kafka is enabled but the producer is not initialized.",
                status_code=503,
            )
        idem_key, correlation_id = new_job_keys()
        try:
            await publish_phase2_enqueued(
                request=request,
                settings=settings,
                session_id=session_id,
                user_message_id=user_msg_id,
                architecture_notes=notes or None,
                idempotency_key=idem_key,
                correlation_id=correlation_id,
            )
        except Exception as e:
            db.rollback()
            logger.exception(
                "architecture_run_kafka_publish_failed",
                extra={"session_id": str(session_id)},
            )
            raise AppError(
                code="kafka_publish_failed",
                message="Could not enqueue the architecture run to Kafka.",
                status_code=503,
                details={"error_type": type(e).__name__},
            ) from e
        db.commit()
        response.status_code = status.HTTP_202_ACCEPTED
        q = QueuedAgentRun(
            correlation_id=correlation_id,
            idempotency_key=idem_key,
            user_message_id=user_msg_id,
        )
        return success_body({"queued_agent_run": q.model_dump(mode="json")}, request_id=request_id)

    llm = get_llm_provider(request, settings)
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
    request_id: RequestIdDep,
    request: Request,
    response: Response,
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

    force_prd = body.product_action == "synthesize_prd"

    if session.phase == "product":
        if settings.kafka_enabled and settings.kafka_async_runs:
            producer = getattr(request.app.state, "kafka_producer", None)
            if producer is None:
                raise AppError(
                    code="kafka_unavailable",
                    message="Kafka is enabled but the producer is not initialized.",
                    status_code=503,
                )
            idem_key, correlation_id = new_job_keys()
            try:
                await publish_phase1_enqueued(
                    request=request,
                    settings=settings,
                    session_id=session_id,
                    user_message_id=user_msg.id,
                    force_synthesize_prd=force_prd,
                    idempotency_key=idem_key,
                    correlation_id=correlation_id,
                )
            except Exception as e:
                db.rollback()
                logger.exception(
                    "chat_kafka_publish_failed", extra={"session_id": str(session_id)}
                )
                raise AppError(
                    code="kafka_publish_failed",
                    message="Could not enqueue the chat turn to Kafka.",
                    status_code=503,
                    details={"error_type": type(e).__name__},
                ) from e
            db.commit()
            db.refresh(user_msg)
            response.status_code = status.HTTP_202_ACCEPTED
            q = QueuedAgentRun(
                correlation_id=correlation_id,
                idempotency_key=idem_key,
                user_message_id=user_msg.id,
            )
            return success_body({"queued_agent_run": q.model_dump(mode="json")}, request_id=request_id)

        llm = get_llm_provider(request, settings)
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

    llm = get_llm_provider(request, settings)
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
