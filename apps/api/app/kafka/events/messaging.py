from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class MessageSubmittedPayload(BaseModel):
    """Payload for `message.submitted` — worker runs Phase 1 or Phase 2 graph."""

    run_kind: Literal["phase1", "phase2"]
    user_message_id: UUID | None = None
    force_synthesize_prd: bool = False
    architecture_notes: str | None = Field(
        None, description="Free-form notes for architecture run (may be empty)"
    )
