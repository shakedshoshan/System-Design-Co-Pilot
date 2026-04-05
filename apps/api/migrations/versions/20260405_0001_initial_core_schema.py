"""Initial core schema: sessions, messages, artifacts, event_logs.

Revision ID: 20260405_0001
Revises:
Create Date: 2026-04-05

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260405_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=True),
        sa.Column("phase", sa.String(length=32), server_default="product", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("extra", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_messages_session_id"), "messages", ["session_id"], unique=False)
    op.create_table(
        "artifacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("artifact_type", sa.String(length=64), nullable=False),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "session_id", "artifact_type", "version", name="uq_artifact_session_type_version"
        ),
    )
    op.create_index(
        op.f("ix_artifacts_session_id"), "artifacts", ["session_id"], unique=False
    )
    op.create_index(
        op.f("ix_artifacts_artifact_type"), "artifacts", ["artifact_type"], unique=False
    )
    op.create_table(
        "event_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("level", sa.String(length=16), nullable=False),
        sa.Column("kind", sa.String(length=128), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_event_logs_created_at"), "event_logs", ["created_at"], unique=False
    )
    op.create_index(op.f("ix_event_logs_level"), "event_logs", ["level"], unique=False)
    op.create_index(op.f("ix_event_logs_kind"), "event_logs", ["kind"], unique=False)
    op.create_index(
        op.f("ix_event_logs_session_id"), "event_logs", ["session_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_event_logs_session_id"), table_name="event_logs")
    op.drop_index(op.f("ix_event_logs_kind"), table_name="event_logs")
    op.drop_index(op.f("ix_event_logs_level"), table_name="event_logs")
    op.drop_index(op.f("ix_event_logs_created_at"), table_name="event_logs")
    op.drop_table("event_logs")
    op.drop_index(op.f("ix_artifacts_artifact_type"), table_name="artifacts")
    op.drop_index(op.f("ix_artifacts_session_id"), table_name="artifacts")
    op.drop_table("artifacts")
    op.drop_index(op.f("ix_messages_session_id"), table_name="messages")
    op.drop_table("messages")
    op.drop_table("sessions")
