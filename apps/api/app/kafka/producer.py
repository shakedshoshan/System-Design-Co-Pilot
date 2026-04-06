from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError

from app.kafka.serialization import dumps_event

if TYPE_CHECKING:
    from app.core.config import Settings
    from app.kafka.envelope import DomainEvent

logger = logging.getLogger("app.kafka.producer")


class KafkaEventProducer:
    """Async producer for `DomainEvent` JSON envelopes."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        if self._producer is not None:
            return
        p = AIOKafkaProducer(
            bootstrap_servers=self._settings.kafka_bootstrap_servers,
            enable_idempotence=True,
        )
        await p.start()
        self._producer = p
        logger.info(
            "kafka_producer_started",
            extra={"bootstrap": self._settings.kafka_bootstrap_servers},
        )

    async def stop(self) -> None:
        if self._producer is None:
            return
        try:
            await self._producer.stop()
        finally:
            self._producer = None
            logger.info("kafka_producer_stopped")

    async def publish(self, event: DomainEvent, *, topic: str | None = None) -> None:
        if self._producer is None:
            raise RuntimeError("KafkaEventProducer is not started")
        t = topic or self._settings.kafka_topic_events
        key = str(event.session_id).encode("utf-8")
        payload = dumps_event(event)
        try:
            await self._producer.send_and_wait(t, value=payload, key=key)
        except KafkaError as e:
            logger.exception("kafka_publish_failed", extra={"topic": t, "event_type": event.event_type})
            raise
