from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Literal, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.kafka.events.agent_run import AgentRunCompletedPayload, AgentRunStartedPayload
from app.kafka.events.artifact import ArtifactUpdatedPayload
from app.kafka.events.messaging import MessageSubmittedPayload
from app.kafka.events.session import SessionCreatedPayload

EVENT_SESSION_CREATED = "session.created"
EVENT_MESSAGE_SUBMITTED = "message.submitted"
EVENT_AGENT_RUN_STARTED = "agent.run.started"
EVENT_AGENT_RUN_COMPLETED = "agent.run.completed"
EVENT_ARTIFACT_UPDATED = "artifact.updated"

SCHEMA_VERSION = 1


class SessionCreatedEvent(BaseModel):
    schema_version: Literal[1] = SCHEMA_VERSION
    event_type: Literal["session.created"] = EVENT_SESSION_CREATED
    occurred_at: datetime
    idempotency_key: str
    correlation_id: UUID
    session_id: UUID
    payload: SessionCreatedPayload


class MessageSubmittedEvent(BaseModel):
    schema_version: Literal[1] = SCHEMA_VERSION
    event_type: Literal["message.submitted"] = EVENT_MESSAGE_SUBMITTED
    occurred_at: datetime
    idempotency_key: str
    correlation_id: UUID
    session_id: UUID
    payload: MessageSubmittedPayload


class AgentRunStartedEvent(BaseModel):
    schema_version: Literal[1] = SCHEMA_VERSION
    event_type: Literal["agent.run.started"] = EVENT_AGENT_RUN_STARTED
    occurred_at: datetime
    idempotency_key: str
    correlation_id: UUID
    session_id: UUID
    payload: AgentRunStartedPayload


class AgentRunCompletedEvent(BaseModel):
    schema_version: Literal[1] = SCHEMA_VERSION
    event_type: Literal["agent.run.completed"] = EVENT_AGENT_RUN_COMPLETED
    occurred_at: datetime
    idempotency_key: str
    correlation_id: UUID
    session_id: UUID
    payload: AgentRunCompletedPayload


class ArtifactUpdatedEvent(BaseModel):
    schema_version: Literal[1] = SCHEMA_VERSION
    event_type: Literal["artifact.updated"] = EVENT_ARTIFACT_UPDATED
    occurred_at: datetime
    idempotency_key: str
    correlation_id: UUID
    session_id: UUID
    payload: ArtifactUpdatedPayload


DomainEvent = Annotated[
    Union[
        SessionCreatedEvent,
        MessageSubmittedEvent,
        AgentRunStartedEvent,
        AgentRunCompletedEvent,
        ArtifactUpdatedEvent,
    ],
    Field(discriminator="event_type"),
]


def new_correlation_id() -> UUID:
    return uuid4()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_idempotency_key() -> str:
    return str(uuid4())
