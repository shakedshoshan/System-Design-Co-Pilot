from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class CreateSessionRequest(BaseModel):
    title: str | None = Field(None, max_length=512)


class SessionSummary(BaseModel):
    id: UUID
    title: str | None
    phase: str


class ChatRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=32_000)
    product_action: Literal["default", "synthesize_prd"] = "default"


class ChatResult(BaseModel):
    user_message_id: UUID
    assistant_message_id: UUID
    assistant_content: str
    prd_artifact_id: UUID | None = None
    prd_version: int | None = None
    phase1_ready_for_architecture: bool | None = None
