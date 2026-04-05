from __future__ import annotations

from typing import TypedDict


class Phase2State(TypedDict):
    """LangGraph state for one architecture pipeline run (PRD → five agent artifacts).

    The runner hydrates `prd_content` and optional `user_notes`; each node appends one
    JSON string field. Persisted artifact types map to these keys in the runner.
    """

    session_id: str
    prd_content: str
    user_notes: str
    architecture_pattern_json: str
    architecture_technology_json: str
    architecture_scalability_json: str
    architecture_tradeoffs_json: str
    architecture_red_team_json: str
