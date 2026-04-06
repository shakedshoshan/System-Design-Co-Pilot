from __future__ import annotations

import asyncio
import logging
import signal
import sys
from pathlib import Path

_API_ROOT = Path(__file__).resolve().parents[2] / "api"
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))

from openai import AsyncOpenAI

from app.core.config import get_settings
from app.kafka.producer import KafkaEventProducer
from app.services.llm.openai_provider import OpenAILLMProvider
from worker_app.consumers.events_consumer import run_events_consumer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("worker.main")


async def async_main() -> None:
    settings = get_settings()
    if not settings.database_url:
        raise SystemExit("DATABASE_URL is required for the worker")
    if not settings.openai_api_key:
        raise SystemExit("OPENAI_API_KEY is required for the worker")

    client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        timeout=settings.llm_timeout_seconds,
    )
    llm = OpenAILLMProvider(client, settings.llm_model)
    producer = KafkaEventProducer(settings)
    await producer.start()
    stop = asyncio.Event()

    def _on_stop() -> None:
        stop.set()

    try:
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, _on_stop)
    except NotImplementedError:
        logger.warning("signal_handlers_not_supported_on_this_platform")

    try:
        await run_events_consumer(settings, llm, producer, stop)
    finally:
        await producer.stop()
        await client.close()


def main() -> None:
    asyncio.run(async_main())
