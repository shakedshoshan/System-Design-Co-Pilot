from __future__ import annotations

import json
from typing import Any

from pydantic import TypeAdapter

from app.kafka.envelope import DomainEvent

_event_adapter: TypeAdapter[DomainEvent] = TypeAdapter(DomainEvent)


def dumps_event(event: DomainEvent) -> bytes:
    data = event.model_dump(mode="json")
    return json.dumps(data, default=str).encode("utf-8")


def loads_event(raw: bytes) -> DomainEvent:
    data: Any = json.loads(raw.decode("utf-8"))
    return _event_adapter.validate_python(data)
