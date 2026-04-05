from __future__ import annotations

from pydantic import BaseModel, Field


class RedTeamOutput(BaseModel):
    """Adversarial review."""

    risks: list[str] = Field(default_factory=list)
    failure_scenarios: list[str] = Field(default_factory=list)
    weak_assumptions: list[str] = Field(default_factory=list)
    suggested_mitigations: list[str] = Field(default_factory=list)
