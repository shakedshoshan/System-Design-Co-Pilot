from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

from fastapi import Request

from app.core.config import Settings
from app.kafka.envelope import (
    MessageSubmittedEvent,
    SessionCreatedEvent,
    SessionCreatedPayload,
    new_correlation_id,
    new_idempotency_key,
    utcnow,
)
from app.kafka.events.messaging import MessageSubmittedPayload
from app.kafka.producer import KafkaEventProducer

logger = logging.getLogger("app.events.publish")


def _producer(request: Request) -> KafkaEventProducer | None:
    return getattr(request.app.state, "kafka_producer", None)


async def publish_session_created_if_enabled(
    *,
    request: Request,
    settings: Settings,
    session_id: UUID,
    title: str | None,
    phase: str,
    created_at: datetime,
) -> None:
    if not settings.kafka_enabled:
        return
    producer = _producer(request)
    if producer is None:
        return
    event = SessionCreatedEvent(
        occurred_at=utcnow(),
        idempotency_key=f"session.created:{session_id}",
        correlation_id=new_correlation_id(),
        session_id=session_id,
        payload=SessionCreatedPayload(title=title, phase=phase, created_at=created_at),
    )
    try:
        await producer.publish(event)
    except Exception:
        logger.exception(
            "kafka_publish_session_created_failed", extra={"session_id": str(session_id)}
        )


async def publish_phase1_enqueued(
    *,
    request: Request,
    settings: Settings,
    session_id: UUID,
    user_message_id: UUID,
    force_synthesize_prd: bool,
    idempotency_key: str,
    correlation_id: UUID,
) -> None:
    producer = _producer(request)
    if producer is None:
        raise RuntimeError("Kafka producer is not available")
    event = MessageSubmittedEvent(
        occurred_at=utcnow(),
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
        session_id=session_id,
        payload=MessageSubmittedPayload(
            run_kind="phase1",
            user_message_id=user_message_id,
            force_synthesize_prd=force_synthesize_prd,
            architecture_notes=None,
        ),
    )
    await producer.publish(event)


async def publish_phase2_enqueued(
    *,
    request: Request,
    settings: Settings,
    session_id: UUID,
    user_message_id: UUID | None,
    architecture_notes: str | None,
    idempotency_key: str,
    correlation_id: UUID,
) -> None:
    producer = _producer(request)
    if producer is None:
        raise RuntimeError("Kafka producer is not available")
    event = MessageSubmittedEvent(
        occurred_at=utcnow(),
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
        session_id=session_id,
        payload=MessageSubmittedPayload(
            run_kind="phase2",
            user_message_id=user_message_id,
            force_synthesize_prd=False,
            architecture_notes=architecture_notes,
        ),
    )
    await producer.publish(event)


def new_job_keys() -> tuple[str, UUID]:
    return new_idempotency_key(), new_correlation_id()
