"""Kafka event contracts and producer (Step 7). See README.md."""

from app.kafka.envelope import (
    AgentRunCompletedEvent,
    AgentRunStartedEvent,
    ArtifactUpdatedEvent,
    DomainEvent,
    MessageSubmittedEvent,
    SessionCreatedEvent,
    new_correlation_id,
    new_idempotency_key,
    utcnow,
)
from app.kafka.producer import KafkaEventProducer
from app.kafka.topics import DEFAULT_EVENTS_TOPIC

__all__ = [
    "AgentRunCompletedEvent",
    "AgentRunStartedEvent",
    "ArtifactUpdatedEvent",
    "DEFAULT_EVENTS_TOPIC",
    "DomainEvent",
    "KafkaEventProducer",
    "MessageSubmittedEvent",
    "SessionCreatedEvent",
    "new_correlation_id",
    "new_idempotency_key",
    "utcnow",
]
