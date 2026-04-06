from __future__ import annotations

"""Compile the Phase 1 LangGraph: guided questioning → optional PRD synthesis.

*Edges* (connections between nodes) are declared here via `add_edge` /
`add_conditional_edges`. *Nodes* live in `nodes.py`; *state* in `app.graph.state.phase1`;
*routing* (conditional path function) in `routing.py`.

Flow (one invocation per POST /chat):
  START → guided_questioning → [conditional] → prd_synthesis? → END

The conditional function reads merged state after the guided node (notably `ready_for_prd`
and the initial `force_synthesize` flag from the API).
"""

from langgraph.graph import END, START, StateGraph

from app.graph.phase1_product.edges import CONDITIONAL_BRANCH_DONE, CONDITIONAL_BRANCH_TO_PRD
from app.graph.phase1_product.nodes import (
    make_guided_questioning_node,
    make_prd_synthesis_node,
)
from app.graph.phase1_product.routing import route_after_guided
from app.graph.state.phase1 import Phase1State
from app.services.llm.openai_provider import OpenAILLMProvider


def build_phase1_graph(
    llm: OpenAILLMProvider,
    *,
    max_output_chars: int,
    model: str | None = None,
):
    """Wire nodes and edges; return a compiled graph. Called once per chat turn (cheap vs LLM)."""
    workflow = StateGraph(Phase1State)
    workflow.add_node(
        "guided_questioning",
        make_guided_questioning_node(llm, max_output_chars=max_output_chars, model=model),
    )
    workflow.add_node(
        "prd_synthesis",
        make_prd_synthesis_node(llm, max_output_chars=max_output_chars, model=model),
    )
    workflow.add_edge(START, "guided_questioning")
    workflow.add_conditional_edges(
        "guided_questioning",
        route_after_guided,
        {
            CONDITIONAL_BRANCH_TO_PRD: "prd_synthesis",
            CONDITIONAL_BRANCH_DONE: END,
        },
    )
    workflow.add_edge("prd_synthesis", END)
    return workflow.compile()
