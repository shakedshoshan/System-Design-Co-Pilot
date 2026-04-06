from __future__ import annotations

import logging

from app.core.config import Settings
from app.kafka.envelope import MessageSubmittedEvent
from app.kafka.producer import KafkaEventProducer
from app.services.llm.openai_provider import OpenAILLMProvider
from worker_app.handlers.phase1_job import process_phase1_job
from worker_app.handlers.phase2_job import process_phase2_job

logger = logging.getLogger("worker.dispatch")


async def dispatch_message_submitted(
    event: MessageSubmittedEvent,
    *,
    settings: Settings,
    llm: OpenAILLMProvider,
    producer: KafkaEventProducer,
) -> None:
    kind = event.payload.run_kind
    if kind == "phase1":
        await process_phase1_job(event, settings=settings, llm=llm, producer=producer)
    elif kind == "phase2":
        await process_phase2_job(event, settings=settings, llm=llm, producer=producer)
    else:
        logger.warning("unknown_run_kind", extra={"run_kind": kind})
