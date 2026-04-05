from __future__ import annotations

from app.graph.phase2_architecture.nodes.llm_node import call_structured_json_node, prd_context_block
from app.graph.phase2_architecture.parsing import parse_technology_output
from app.graph.phase2_architecture.prompts import TECHNOLOGY_SYSTEM
from app.graph.phase2_architecture.schemas import TechnologyOutput
from app.graph.state.phase2 import Phase2State
from app.services.llm.openai_provider import OpenAILLMProvider


def make_technology_node(
    llm: OpenAILLMProvider,
    *,
    max_output_chars: int,
    model: str | None = None,
):
    async def technology_expert(state: Phase2State) -> dict:
        prior = state.get("architecture_pattern_json") or ""
        user_body = (
            prd_context_block(state)
            + f"\n## Architecture pattern analysis (JSON)\n{prior}\n\n"
            "Produce the JSON object per your instructions."
        )
        out = await call_structured_json_node(
            llm,
            system=TECHNOLOGY_SYSTEM,
            user_body=user_body,
            model=model,
            parse_fn=parse_technology_output,
            fallback_factory=lambda snippet: TechnologyOutput(
                recommended_stack="Unparsed model output.",
                justification=snippet[:4000],
            ),
            max_output_chars=max_output_chars,
            log_key="phase2_technology_json_fallback",
            session_id=state["session_id"],
        )
        return {"architecture_technology_json": out}

    return technology_expert
