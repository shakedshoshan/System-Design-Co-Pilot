from __future__ import annotations

from pydantic import BaseModel, Field


class TradeoffRow(BaseModel):
    """One row in a tradeoff table."""

    topic: str = ""
    options: str = ""
    tradeoff: str = ""
    decision: str = ""
    rationale: str = ""


class TradeoffsOutput(BaseModel):
    """Tradeoff and decision agent."""

    tradeoffs: list[TradeoffRow] = Field(default_factory=list)
    cap_and_consistency_notes: str = ""
    cost_complexity_notes: str = ""
