from __future__ import annotations

"""Compile the Phase 1 LangGraph: guided questioning → optional PRD synthesis.

Flow (one invocation per POST /chat):
  START → guided_questioning → [conditional] → prd_synthesis? → END

The conditional function reads merged state after the guided node (notably `ready_for_prd`
and the initial `force_synthesize` flag from the API).
"""

from langgraph.graph import END, START, StateGraph

from app.graph.phase1_product.nodes import (
    make_guided_questioning_node,
    make_prd_synthesis_node,
    route_after_guided,
)
from app.graph.state.phase1 import Phase1State
from app.services.llm.openai_provider import OpenAILLMProvider


def build_phase1_graph(
    llm: OpenAILLMProvider,
    *,
    max_output_chars: int,
    model: str | None = None,
):
    """Wire nodes and return a compiled graph. Called once per chat turn (cheap vs LLM)."""
    workflow = StateGraph(Phase1State)
    workflow.add_node(
        "guided_questioning",
        make_guided_questioning_node(llm, max_output_chars=max_output_chars, model=model),
    )
    workflow.add_node(
        "prd_synthesis",
        make_prd_synthesis_node(llm, max_output_chars=max_output_chars, model=model),
    )
    # Every turn starts with clarification / draft update.
    workflow.add_edge(START, "guided_questioning")
    # Branch: synthesize PRD only when model is ready OR user forced synthesis.
    workflow.add_conditional_edges(
        "guided_questioning",
        route_after_guided,
        {
            "prd_synthesis": "prd_synthesis",
            "done": END,
        },
    )
    workflow.add_edge("prd_synthesis", END)
    return workflow.compile()
