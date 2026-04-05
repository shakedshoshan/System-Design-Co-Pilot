from __future__ import annotations

from app.graph.phase2_architecture.nodes.llm_node import call_structured_json_node, prd_context_block
from app.graph.phase2_architecture.parsing import parse_scalability_output
from app.graph.phase2_architecture.prompts import SCALABILITY_SYSTEM
from app.graph.phase2_architecture.schemas import ScalabilityOutput
from app.graph.state.phase2 import Phase2State
from app.services.llm.openai_provider import OpenAILLMProvider


def make_scalability_node(
    llm: OpenAILLMProvider,
    *,
    max_output_chars: int,
    model: str | None = None,
):
    async def scalability(state: Phase2State) -> dict:
        user_body = (
            prd_context_block(state)
            + f"\n## Architecture pattern (JSON)\n{state.get('architecture_pattern_json') or ''}\n\n"
            f"## Technology (JSON)\n{state.get('architecture_technology_json') or ''}\n\n"
            "Produce the JSON object per your instructions."
        )
        out = await call_structured_json_node(
            llm,
            system=SCALABILITY_SYSTEM,
            user_body=user_body,
            model=model,
            parse_fn=parse_scalability_output,
            fallback_factory=lambda snippet: ScalabilityOutput(
                scaling_strategy="Unparsed model output.",
                load_estimation_notes=snippet[:4000],
            ),
            max_output_chars=max_output_chars,
            log_key="phase2_scalability_json_fallback",
            session_id=state["session_id"],
        )
        return {"architecture_scalability_json": out}

    return scalability
