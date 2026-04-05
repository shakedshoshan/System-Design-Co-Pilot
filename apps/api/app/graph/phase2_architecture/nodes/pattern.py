from __future__ import annotations

from app.graph.phase2_architecture.nodes.llm_node import call_structured_json_node, prd_context_block
from app.graph.phase2_architecture.parsing import parse_pattern_output
from app.graph.phase2_architecture.prompts import ARCHITECTURE_PATTERN_SYSTEM
from app.graph.phase2_architecture.schemas import ArchitecturePatternOutput
from app.graph.state.phase2 import Phase2State
from app.services.llm.openai_provider import OpenAILLMProvider


def make_architecture_pattern_node(
    llm: OpenAILLMProvider,
    *,
    max_output_chars: int,
    model: str | None = None,
):
    async def architecture_pattern(state: Phase2State) -> dict:
        user_body = prd_context_block(state) + "\nProduce the JSON object per your instructions."
        out = await call_structured_json_node(
            llm,
            system=ARCHITECTURE_PATTERN_SYSTEM,
            user_body=user_body,
            model=model,
            parse_fn=parse_pattern_output,
            fallback_factory=lambda snippet: ArchitecturePatternOutput(
                pattern_summary="Model output could not be parsed.",
                narrative=snippet[:4000],
            ),
            max_output_chars=max_output_chars,
            log_key="phase2_pattern_json_fallback",
            session_id=state["session_id"],
        )
        return {"architecture_pattern_json": out}

    return architecture_pattern
