from __future__ import annotations

from pydantic import BaseModel, Field


class ScalabilityOutput(BaseModel):
    """Scalability and performance analysis."""

    bottlenecks: list[str] = Field(default_factory=list)
    scaling_strategy: str = ""
    performance_recommendations: list[str] = Field(default_factory=list)
    load_estimation_notes: str = ""
    data_growth_notes: str = ""
