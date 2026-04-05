from __future__ import annotations

"""Parse LLM output into Phase 2 Pydantic models (shared JSON extraction from Phase 1)."""

import json

from app.graph.phase1_product.json_extract import extract_json_object
from app.graph.phase2_architecture.schemas import (
    ArchitecturePatternOutput,
    RedTeamOutput,
    ScalabilityOutput,
    TechnologyOutput,
    TradeoffsOutput,
)


def _parse(model_cls, raw: str):
    try:
        payload = extract_json_object(raw)
        return model_cls.model_validate_json(payload)
    except (json.JSONDecodeError, ValueError):
        return None


def parse_pattern_output(raw: str) -> ArchitecturePatternOutput | None:
    return _parse(ArchitecturePatternOutput, raw)


def parse_technology_output(raw: str) -> TechnologyOutput | None:
    return _parse(TechnologyOutput, raw)


def parse_scalability_output(raw: str) -> ScalabilityOutput | None:
    return _parse(ScalabilityOutput, raw)


def parse_tradeoffs_output(raw: str) -> TradeoffsOutput | None:
    return _parse(TradeoffsOutput, raw)


def parse_red_team_output(raw: str) -> RedTeamOutput | None:
    return _parse(RedTeamOutput, raw)
