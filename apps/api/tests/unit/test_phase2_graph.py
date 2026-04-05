from __future__ import annotations

import json

import pytest

from app.graph.phase2_architecture.build import build_phase2_graph
from app.graph.state.phase2 import Phase2State


class FakeLLM:
    def __init__(self, replies: list[str]) -> None:
        self.replies = replies
        self._i = 0

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
    ) -> str:
        r = self.replies[self._i]
        self._i += 1
        return r


def _base_state() -> Phase2State:
    return {
        "session_id": "550e8400-e29b-41d4-a716-446655440000",
        "prd_content": '{"title": "URL Shortener", "summary": "Short links"}',
        "user_notes": "",
        "architecture_pattern_json": "",
        "architecture_technology_json": "",
        "architecture_scalability_json": "",
        "architecture_tradeoffs_json": "",
        "architecture_red_team_json": "",
    }


def _minimal_jsons() -> list[str]:
    return [
        json.dumps(
            {
                "pattern_summary": "API + worker",
                "structural_style": "modular monolith",
                "service_decomposition": ["api", "redirect"],
                "diagram_mermaid": "graph LR;A-->B",
                "narrative": "Simple split",
            }
        ),
        json.dumps(
            {
                "recommended_stack": "Python/FastAPI",
                "databases": ["Postgres"],
                "messaging_and_integration": "HTTP",
                "justification": "Fits PRD",
                "alternatives_considered": ["Go"],
            }
        ),
        json.dumps(
            {
                "bottlenecks": ["DB writes"],
                "scaling_strategy": "Read replicas",
                "performance_recommendations": ["Cache hot keys"],
                "load_estimation_notes": "1k RPS",
                "data_growth_notes": "Shard by hash",
            }
        ),
        json.dumps(
            {
                "tradeoffs": [
                    {
                        "topic": "Consistency",
                        "options": "Strong vs eventual",
                        "tradeoff": "Latency",
                        "decision": "Strong for creation",
                        "rationale": "Correctness",
                    }
                ],
                "cap_and_consistency_notes": "CP",
                "cost_complexity_notes": "Low",
            }
        ),
        json.dumps(
            {
                "risks": ["Single region"],
                "failure_scenarios": ["DB down"],
                "weak_assumptions": ["Traffic uniform"],
                "suggested_mitigations": ["Multi-AZ"],
            }
        ),
    ]


@pytest.mark.asyncio
async def test_phase2_graph_runs_five_agents_in_order() -> None:
    replies = _minimal_jsons()
    llm = FakeLLM(replies)
    graph = build_phase2_graph(llm, max_output_chars=8000)
    out = await graph.ainvoke(_base_state())
    assert llm._i == 5
    assert "modular monolith" in out["architecture_pattern_json"]
    assert "FastAPI" in out["architecture_technology_json"]
    assert "Read replicas" in out["architecture_scalability_json"]
    assert "Consistency" in out["architecture_tradeoffs_json"]
    assert "Single region" in out["architecture_red_team_json"]
