from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SessionCreatedPayload(BaseModel):
    """Payload for `session.created`."""

    title: str | None = None
    phase: str
    created_at: datetime = Field(..., description="Session row timestamp")
