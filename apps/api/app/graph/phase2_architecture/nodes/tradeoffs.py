from __future__ import annotations

from app.graph.phase2_architecture.nodes.llm_node import call_structured_json_node, prd_context_block
from app.graph.phase2_architecture.parsing import parse_tradeoffs_output
from app.graph.phase2_architecture.prompts import TRADEOFFS_SYSTEM
from app.graph.phase2_architecture.schemas import TradeoffsOutput
from app.graph.state.phase2 import Phase2State
from app.services.llm.openai_provider import OpenAILLMProvider


def make_tradeoffs_node(
    llm: OpenAILLMProvider,
    *,
    max_output_chars: int,
    model: str | None = None,
):
    async def tradeoffs(state: Phase2State) -> dict:
        user_body = (
            prd_context_block(state)
            + f"\n## Pattern (JSON)\n{state.get('architecture_pattern_json') or ''}\n\n"
            f"## Technology (JSON)\n{state.get('architecture_technology_json') or ''}\n\n"
            f"## Scalability (JSON)\n{state.get('architecture_scalability_json') or ''}\n\n"
            "Produce the JSON object per your instructions."
        )
        out = await call_structured_json_node(
            llm,
            system=TRADEOFFS_SYSTEM,
            user_body=user_body,
            model=model,
            parse_fn=parse_tradeoffs_output,
            fallback_factory=lambda snippet: TradeoffsOutput(
                cost_complexity_notes=snippet[:4000],
            ),
            max_output_chars=max_output_chars,
            log_key="phase2_tradeoffs_json_fallback",
            session_id=state["session_id"],
        )
        return {"architecture_tradeoffs_json": out}

    return tradeoffs
