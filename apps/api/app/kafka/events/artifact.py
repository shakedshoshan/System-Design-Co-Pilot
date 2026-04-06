from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class ArtifactUpdatedPayload(BaseModel):
    artifact_id: UUID
    artifact_type: str
    version: int
    correlation_id: UUID = Field(..., description="Ties to the agent run that wrote this row")
