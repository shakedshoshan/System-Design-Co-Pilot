from __future__ import annotations

import json
import pytest

from app.graph.phase1_product.build import build_phase1_graph
from app.graph.phase1_product.nodes import route_after_guided
from app.graph.state.phase1 import Phase1State


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


def _base_state() -> Phase1State:
    return {
        "session_id": "550e8400-e29b-41d4-a716-446655440000",
        "user_message": "Build a URL shortener",
        "message_history": [
            {"role": "user", "content": "Build a URL shortener"},
        ],
        "requirements_draft": "",
        "open_questions": [],
        "force_synthesize": False,
        "ready_for_prd": False,
        "assistant_reply": "",
        "prd_json": "",
    }


@pytest.mark.asyncio
async def test_route_after_guided_respects_flags() -> None:
    s0 = _base_state()
    s1 = {**_base_state(), "ready_for_prd": True}
    s2 = {**_base_state(), "force_synthesize": True}
    assert route_after_guided(s0) == "done"
    assert route_after_guided(s1) == "prd_synthesis"
    assert route_after_guided(s2) == "prd_synthesis"


@pytest.mark.asyncio
async def test_graph_stops_after_guided_when_not_ready() -> None:
    guided = json.dumps(
        {
            "assistant_message": "Who is the primary user?",
            "updated_requirements_draft": "URL shortener — scope TBD",
            "open_questions": ["Target scale?"],
            "ready_for_prd": False,
        }
    )
    llm = FakeLLM([guided])
    graph = build_phase1_graph(llm, max_output_chars=8000)
    out = await graph.ainvoke(_base_state())
    assert llm._i == 1
    assert "Who is the primary user?" in out["assistant_reply"]
    assert out.get("prd_json") == ""


@pytest.mark.asyncio
async def test_graph_runs_prd_when_ready() -> None:
    guided = json.dumps(
        {
            "assistant_message": "Drafting PRD.",
            "updated_requirements_draft": "Full draft here.",
            "open_questions": [],
            "ready_for_prd": True,
        }
    )
    prd = json.dumps(
        {
            "title": "URL Shortener",
            "summary": "Short links",
            "features": ["Create short URL"],
            "user_stories": ["As a user I shorten a link"],
            "edge_cases": ["Collision handling"],
        }
    )
    llm = FakeLLM([guided, prd])
    graph = build_phase1_graph(llm, max_output_chars=8000)
    out = await graph.ainvoke(_base_state())
    assert llm._i == 2
    assert "URL Shortener" in out["prd_json"]
    assert "structured PRD" in out["assistant_reply"]


@pytest.mark.asyncio
async def test_graph_force_synthesize_runs_prd_even_if_not_ready() -> None:
    guided = json.dumps(
        {
            "assistant_message": "More detail needed.",
            "updated_requirements_draft": "Partial",
            "open_questions": ["Q?"],
            "ready_for_prd": False,
        }
    )
    prd = json.dumps(
        {
            "title": "T",
            "summary": "S",
            "features": [],
            "user_stories": [],
            "edge_cases": [],
        }
    )
    llm = FakeLLM([guided, prd])
    graph = build_phase1_graph(llm, max_output_chars=8000)
    out = await graph.ainvoke({**_base_state(), "force_synthesize": True})
    assert llm._i == 2
    assert '"title": "T"' in out["prd_json"]
