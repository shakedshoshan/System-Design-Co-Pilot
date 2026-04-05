from __future__ import annotations

from pydantic import BaseModel, Field


class TechnologyOutput(BaseModel):
    """Technology expert: stack, stores, messaging."""

    recommended_stack: str = ""
    databases: list[str] = Field(default_factory=list)
    messaging_and_integration: str = ""
    justification: str = ""
    alternatives_considered: list[str] = Field(default_factory=list)
