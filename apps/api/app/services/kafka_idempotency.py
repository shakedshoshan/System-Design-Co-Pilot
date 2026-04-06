"""Postgres-backed claim for Kafka job processing (INSERT .. ON CONFLICT DO NOTHING)."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.db.models import ProcessedKafkaEvent


def claim_message_submitted_job(db: Session, *, idempotency_key: str) -> bool:
    """Return True if this worker won the race to process this job; False if already claimed."""
    stmt = (
        insert(ProcessedKafkaEvent)
        .values(idempotency_key=idempotency_key, event_type="message.submitted")
        .on_conflict_do_nothing(index_elements=["idempotency_key"])
        .returning(ProcessedKafkaEvent.idempotency_key)
    )
    row = db.execute(stmt).fetchone()
    return row is not None


def release_message_submitted_claim(db: Session, *, idempotency_key: str) -> None:
    """Remove claim after a failed job so Kafka redelivery can retry."""
    db.execute(
        sa.delete(ProcessedKafkaEvent).where(
            ProcessedKafkaEvent.idempotency_key == idempotency_key
        )
    )
    db.commit()
