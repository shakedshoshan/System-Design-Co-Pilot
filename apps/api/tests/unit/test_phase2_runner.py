from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.db.models import Artifact
from app.services.phase2.runner import run_phase2_pipeline


@pytest.mark.asyncio
async def test_run_phase2_pipeline_writes_five_versioned_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services.phase2 import runner as runner_mod

    session_id = uuid4()
    out_state = {
        "architecture_pattern_json": '{"pattern_summary": "x"}',
        "architecture_technology_json": '{"recommended_stack": "y"}',
        "architecture_scalability_json": '{"scaling_strategy": "z"}',
        "architecture_tradeoffs_json": '{"cap_and_consistency_notes": "c"}',
        "architecture_red_team_json": '{"risks": ["r"]}',
    }
    graph = MagicMock()
    graph.ainvoke = AsyncMock(return_value=out_state)
    monkeypatch.setattr(runner_mod, "build_phase2_graph", lambda *a, **k: graph)

    prd_row = MagicMock()
    prd_row.content = "PRD text"
    scalars = [prd_row, 0, 0, 0, 0, 0]
    db = MagicMock()
    db.scalar = MagicMock(side_effect=scalars)
    added: list[Artifact] = []

    def capture_add(obj: object) -> None:
        if isinstance(obj, Artifact):
            added.append(obj)
            obj.id = uuid4()

    db.add = capture_add
    db.flush = MagicMock()

    settings = MagicMock()
    settings.llm_max_output_chars = 8000
    settings.llm_model = "gpt-4o"
    llm = MagicMock()

    result = await run_phase2_pipeline(db, session_id, settings, llm, user_notes="note")

    assert graph.ainvoke.await_count == 1
    assert len(added) == 5
    assert {a.artifact_type for a in added} == {
        "architecture_pattern",
        "architecture_technology",
        "architecture_scalability",
        "architecture_tradeoffs",
        "architecture_red_team",
    }
    assert all(a.version == 1 for a in added)
    assert len(result.artifacts) == 5
    assert "Architecture pipeline complete" in result.assistant_summary
