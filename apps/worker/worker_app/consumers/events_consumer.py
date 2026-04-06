from __future__ import annotations

import asyncio
import logging

from aiokafka import AIOKafkaConsumer

from app.core.config import Settings
from app.kafka.envelope import MessageSubmittedEvent
from app.kafka.producer import KafkaEventProducer
from app.kafka.serialization import loads_event
from app.services.llm.openai_provider import OpenAILLMProvider
from worker_app.handlers.dispatch import dispatch_message_submitted

logger = logging.getLogger("worker.consumer")


async def run_events_consumer(
    settings: Settings,
    llm: OpenAILLMProvider,
    producer: KafkaEventProducer,
    stop: asyncio.Event,
) -> None:
    consumer = AIOKafkaConsumer(
        settings.kafka_topic_events,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=settings.kafka_consumer_group,
        enable_auto_commit=False,
        auto_offset_reset="earliest",
    )
    await consumer.start()
    logger.info(
        "kafka_consumer_started",
        extra={
            "topic": settings.kafka_topic_events,
            "group": settings.kafka_consumer_group,
        },
    )
    try:
        while not stop.is_set():
            try:
                msg = await asyncio.wait_for(consumer.getone(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            try:
                event = loads_event(msg.value)
            except Exception:
                logger.exception("kafka_invalid_envelope")
                await consumer.commit()
                continue
            if isinstance(event, MessageSubmittedEvent):
                try:
                    await dispatch_message_submitted(
                        event, settings=settings, llm=llm, producer=producer
                    )
                except Exception:
                    logger.exception(
                        "kafka_handler_failed",
                        extra={"session_id": str(event.session_id)},
                    )
                    continue
            await consumer.commit()
    finally:
        await consumer.stop()
        logger.info("kafka_consumer_stopped")
