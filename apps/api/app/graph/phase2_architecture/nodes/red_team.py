from __future__ import annotations

from app.graph.phase2_architecture.nodes.llm_node import call_structured_json_node, prd_context_block
from app.graph.phase2_architecture.parsing import parse_red_team_output
from app.graph.phase2_architecture.prompts import RED_TEAM_SYSTEM
from app.graph.phase2_architecture.schemas import RedTeamOutput
from app.graph.state.phase2 import Phase2State
from app.services.llm.openai_provider import OpenAILLMProvider


def make_red_team_node(
    llm: OpenAILLMProvider,
    *,
    max_output_chars: int,
    model: str | None = None,
):
    async def red_team(state: Phase2State) -> dict:
        user_body = (
            prd_context_block(state)
            + "\n## Full prior architecture package (JSON sections)\n"
            f"### Pattern\n{state.get('architecture_pattern_json') or ''}\n\n"
            f"### Technology\n{state.get('architecture_technology_json') or ''}\n\n"
            f"### Scalability\n{state.get('architecture_scalability_json') or ''}\n\n"
            f"### Tradeoffs\n{state.get('architecture_tradeoffs_json') or ''}\n\n"
            "Produce the JSON object per your instructions."
        )
        out = await call_structured_json_node(
            llm,
            system=RED_TEAM_SYSTEM,
            user_body=user_body,
            model=model,
            parse_fn=parse_red_team_output,
            fallback_factory=lambda snippet: RedTeamOutput(
                risks=[snippet[:2000]] if snippet else ["Unparsed red-team output."],
            ),
            max_output_chars=max_output_chars,
            log_key="phase2_red_team_json_fallback",
            session_id=state["session_id"],
        )
        return {"architecture_red_team_json": out}

    return red_team
