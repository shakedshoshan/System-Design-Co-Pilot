from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class AgentRunStartedPayload(BaseModel):
    correlation_id: UUID
    run_kind: Literal["phase1", "phase2"]


class AgentRunCompletedPayload(BaseModel):
    correlation_id: UUID
    run_kind: Literal["phase1", "phase2"]
    success: bool
    error_summary: str | None = None
