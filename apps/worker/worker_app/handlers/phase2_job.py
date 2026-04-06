from __future__ import annotations

import logging

import openai

from app.core.config import Settings
from app.db.models import DesignSession, Message
from app.db.session import session_factory
from app.kafka.envelope import MessageSubmittedEvent
from app.kafka.producer import KafkaEventProducer
from app.services.kafka_idempotency import (
    claim_message_submitted_job,
    release_message_submitted_claim,
)
from app.services.llm.guardrails import sanitize_assistant_output
from app.services.llm.openai_provider import OpenAILLMProvider
from app.services.phase2.runner import run_phase2_pipeline, session_has_prd
from worker_app.kafka_out import (
    emit_agent_run_completed,
    emit_agent_run_started,
    emit_artifact_updated,
)

logger = logging.getLogger("worker.phase2")


def _release_claim(idempotency_key: str) -> None:
    db = session_factory()()
    try:
        release_message_submitted_claim(db, idempotency_key=idempotency_key)
    finally:
        db.close()


async def process_phase2_job(
    event: MessageSubmittedEvent,
    *,
    settings: Settings,
    llm: OpenAILLMProvider,
    producer: KafkaEventProducer,
) -> None:
    idem = event.idempotency_key
    sid = event.session_id
    correlation_id = event.correlation_id
    notes = (event.payload.architecture_notes or "").strip()

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
            run_kind="phase2",
            job_idempotency_key=idem,
        )
    except Exception:
        _release_claim(idem)
        raise

    work_db = session_factory()()
    try:
        row = work_db.get(DesignSession, sid)
        if row is None or row.phase != "architecture":
            logger.warning(
                "phase2_invalid_session_phase",
                extra={"session_id": str(sid), "phase": getattr(row, "phase", None)},
            )
            _release_claim(idem)
            await emit_agent_run_completed(
                producer,
                session_id=sid,
                correlation_id=correlation_id,
                run_kind="phase2",
                job_idempotency_key=idem,
                success=False,
                error_summary="invalid_session_phase",
            )
            return
        if not session_has_prd(work_db, sid):
            _release_claim(idem)
            await emit_agent_run_completed(
                producer,
                session_id=sid,
                correlation_id=correlation_id,
                run_kind="phase2",
                job_idempotency_key=idem,
                success=False,
                error_summary="prd_required",
            )
            return

        result = await run_phase2_pipeline(
            work_db,
            sid,
            settings,
            llm,
            user_notes=notes,
        )
        reply = sanitize_assistant_output(
            result.assistant_summary,
            max_chars=settings.llm_max_output_chars,
        )
        assistant_msg = Message(session_id=sid, role="assistant", content=reply)
        work_db.add(assistant_msg)
        work_db.commit()
        await emit_agent_run_completed(
            producer,
            session_id=sid,
            correlation_id=correlation_id,
            run_kind="phase2",
            job_idempotency_key=idem,
            success=True,
        )
        for art in result.artifacts:
            await emit_artifact_updated(
                producer,
                session_id=sid,
                correlation_id=correlation_id,
                artifact_id=art.id,
                artifact_type=art.artifact_type,
                version=art.version,
            )
    except openai.RateLimitError:
        work_db.rollback()
        _release_claim(idem)
        await emit_agent_run_completed(
            producer,
            session_id=sid,
            correlation_id=correlation_id,
            run_kind="phase2",
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
            run_kind="phase2",
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
            run_kind="phase2",
            job_idempotency_key=idem,
            success=False,
            error_summary=type(e).__name__,
        )
        raise
    finally:
        work_db.close()
