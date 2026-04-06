from __future__ import annotations

from uuid import uuid4

from app.kafka.envelope import MessageSubmittedEvent, utcnow, new_correlation_id, new_idempotency_key
from app.kafka.events.messaging import MessageSubmittedPayload
from app.kafka.serialization import dumps_event, loads_event


def test_message_submitted_round_trip_json() -> None:
    sid = uuid4()
    uid = uuid4()
    corr = new_correlation_id()
    idem = new_idempotency_key()
    original = MessageSubmittedEvent(
        occurred_at=utcnow(),
        idempotency_key=idem,
        correlation_id=corr,
        session_id=sid,
        payload=MessageSubmittedPayload(
            run_kind="phase1",
            user_message_id=uid,
            force_synthesize_prd=True,
            architecture_notes=None,
        ),
    )
    raw = dumps_event(original)
    restored = loads_event(raw)
    assert isinstance(restored, MessageSubmittedEvent)
    assert restored.session_id == sid
    assert restored.payload.user_message_id == uid
    assert restored.payload.run_kind == "phase1"
    assert restored.payload.force_synthesize_prd is True
