from __future__ import annotations

"""Compile Phase 2 LangGraph: sequential architecture agents (plan §6).

*Edges* for the linear chain live in `edges.py` (`wire_phase2_linear_edges`).
*Nodes* are under `nodes/`; *state* in `app.graph.state.phase2`.
"""

from langgraph.graph import StateGraph

from app.graph.phase2_architecture.edges import PHASE2_NODE_IDS, wire_phase2_linear_edges
from app.graph.phase2_architecture.nodes import (
    make_architecture_pattern_node,
    make_red_team_node,
    make_scalability_node,
    make_technology_node,
    make_tradeoffs_node,
)
from app.graph.state.phase2 import Phase2State
from app.services.llm.openai_provider import OpenAILLMProvider

_NODE_FACTORIES = (
    make_architecture_pattern_node,
    make_technology_node,
    make_scalability_node,
    make_tradeoffs_node,
    make_red_team_node,
)


def build_phase2_graph(
    llm: OpenAILLMProvider,
    *,
    max_output_chars: int,
    model: str | None = None,
):
    """Linear pipeline: pattern → technology → scalability → tradeoffs → red team."""
    g = StateGraph(Phase2State)
    for node_id, factory in zip(PHASE2_NODE_IDS, _NODE_FACTORIES, strict=True):
        g.add_node(
            node_id,
            factory(llm, max_output_chars=max_output_chars, model=model),
        )
    wire_phase2_linear_edges(g)
    return g.compile()
