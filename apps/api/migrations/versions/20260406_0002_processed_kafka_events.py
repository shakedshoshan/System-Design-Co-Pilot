"""processed_kafka_events for Kafka consumer idempotency.

Revision ID: 20260406_0002
Revises: 20260405_0001
Create Date: 2026-04-06

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260406_0002"
down_revision: Union[str, None] = "20260405_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "processed_kafka_events",
        sa.Column("idempotency_key", sa.String(length=512), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("idempotency_key", name="processed_kafka_events_pkey"),
    )


def downgrade() -> None:
    op.drop_table("processed_kafka_events")
