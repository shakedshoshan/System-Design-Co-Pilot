"""Publish telemetry events from the worker (same topic as API)."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from app.kafka.envelope import (
    AgentRunCompletedEvent,
    AgentRunCompletedPayload,
    AgentRunStartedEvent,
    AgentRunStartedPayload,
    ArtifactUpdatedEvent,
    ArtifactUpdatedPayload,
    new_idempotency_key,
    utcnow,
)
from app.kafka.producer import KafkaEventProducer


async def emit_agent_run_started(
    producer: KafkaEventProducer,
    *,
    session_id: UUID,
    correlation_id: UUID,
    run_kind: Literal["phase1", "phase2"],
    job_idempotency_key: str,
) -> None:
    ev = AgentRunStartedEvent(
        occurred_at=utcnow(),
        idempotency_key=f"{job_idempotency_key}:agent.started",
        correlation_id=correlation_id,
        session_id=session_id,
        payload=AgentRunStartedPayload(correlation_id=correlation_id, run_kind=run_kind),
    )
    await producer.publish(ev)


async def emit_agent_run_completed(
    producer: KafkaEventProducer,
    *,
    session_id: UUID,
    correlation_id: UUID,
    run_kind: Literal["phase1", "phase2"],
    job_idempotency_key: str,
    success: bool,
    error_summary: str | None = None,
) -> None:
    ev = AgentRunCompletedEvent(
        occurred_at=utcnow(),
        idempotency_key=f"{job_idempotency_key}:agent.completed",
        correlation_id=correlation_id,
        session_id=session_id,
        payload=AgentRunCompletedPayload(
            correlation_id=correlation_id,
            run_kind=run_kind,
            success=success,
            error_summary=error_summary,
        ),
    )
    await producer.publish(ev)


async def emit_artifact_updated(
    producer: KafkaEventProducer,
    *,
    session_id: UUID,
    correlation_id: UUID,
    artifact_id: UUID,
    artifact_type: str,
    version: int,
) -> None:
    ev = ArtifactUpdatedEvent(
        occurred_at=utcnow(),
        idempotency_key=new_idempotency_key(),
        correlation_id=correlation_id,
        session_id=session_id,
        payload=ArtifactUpdatedPayload(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            version=version,
            correlation_id=correlation_id,
        ),
    )
    await producer.publish(ev)
