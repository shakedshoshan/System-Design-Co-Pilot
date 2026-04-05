from __future__ import annotations

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


class ChatResult(BaseModel):
    user_message_id: UUID
    assistant_message_id: UUID
    assistant_content: str
