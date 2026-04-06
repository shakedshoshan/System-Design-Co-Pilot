from __future__ import annotations

import logging

import openai

from app.core.config import Settings
from app.db.models import Message
from app.db.session import session_factory
from app.kafka.envelope import MessageSubmittedEvent
from app.kafka.producer import KafkaEventProducer
from app.services.kafka_idempotency import (
    claim_message_submitted_job,
    release_message_submitted_claim,
)
from app.services.llm.guardrails import sanitize_assistant_output
from app.services.llm.openai_provider import OpenAILLMProvider
from app.services.phase1.runner import run_phase1_turn
from worker_app.kafka_out import (
    emit_agent_run_completed,
    emit_agent_run_started,
    emit_artifact_updated,
)

logger = logging.getLogger("worker.phase1")


def _release_claim(idempotency_key: str) -> None:
    db = session_factory()()
    try:
        release_message_submitted_claim(db, idempotency_key=idempotency_key)
    finally:
        db.close()


async def process_phase1_job(
    event: MessageSubmittedEvent,
    *,
    settings: Settings,
    llm: OpenAILLMProvider,
    producer: KafkaEventProducer,
) -> None:
    idem = event.idempotency_key
    sid = event.session_id
    correlation_id = event.correlation_id

    if event.payload.user_message_id is None:
        logger.warning("phase1_missing_user_message_id", extra={"session_id": str(sid)})
        return

    claim_db = session_factory()()
    try:
        if not claim_message_submitted_job(claim_db, idempotency_key=idem):
            return
        claim_db.commit()
    finally:
        claim_db.close()

    try:
        await emit_agent_run_started(
            producer,
            session_id=sid,
            correlation_id=correlation_id,
            run_kind="phase1",
            job_idempotency_key=idem,
        )
    except Exception:
        _release_claim(idem)
        raise

    work_db = session_factory()()
    try:
        phase1 = await run_phase1_turn(
            work_db,
            sid,
            settings,
            llm,
            force_synthesize=event.payload.force_synthesize_prd,
        )
        reply = sanitize_assistant_output(
            phase1.assistant_reply,
            max_chars=settings.llm_max_output_chars,
        )
        assistant_msg = Message(session_id=sid, role="assistant", content=reply)
        work_db.add(assistant_msg)
        work_db.commit()
        await emit_agent_run_completed(
            producer,
            session_id=sid,
            correlation_id=correlation_id,
            run_kind="phase1",
            job_idempotency_key=idem,
            success=True,
        )
        if phase1.prd_artifact_id is not None and phase1.prd_version is not None:
            await emit_artifact_updated(
                producer,
                session_id=sid,
                correlation_id=correlation_id,
                artifact_id=phase1.prd_artifact_id,
                artifact_type="prd",
                version=phase1.prd_version,
            )
    except openai.RateLimitError:
        work_db.rollback()
        _release_claim(idem)
        await emit_agent_run_completed(
            producer,
            session_id=sid,
            correlation_id=correlation_id,
            run_kind="phase1",
            job_idempotency_key=idem,
            success=False,
            error_summary="rate_limited",
        )
        raise
    except openai.APIError as e:
        work_db.rollback()
        _release_claim(idem)
        await emit_agent_run_completed(
            producer,
            session_id=sid,
            correlation_id=correlation_id,
            run_kind="phase1",
            job_idempotency_key=idem,
            success=False,
            error_summary=type(e).__name__,
        )
        raise
    except Exception as e:
        work_db.rollback()
        _release_claim(idem)
        await emit_agent_run_completed(
            producer,
            session_id=sid,
            correlation_id=correlation_id,
            run_kind="phase1",
            job_idempotency_key=idem,
            success=False,
            error_summary=type(e).__name__,
        )
        raise
    finally:
        work_db.close()
