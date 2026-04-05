from __future__ import annotations

"""Compile Phase 2 LangGraph: sequential architecture agents (plan §6)."""

from langgraph.graph import END, START, StateGraph

from app.graph.phase2_architecture.nodes import (
    make_architecture_pattern_node,
    make_red_team_node,
    make_scalability_node,
    make_technology_node,
    make_tradeoffs_node,
)
from app.graph.state.phase2 import Phase2State
from app.services.llm.openai_provider import OpenAILLMProvider


def build_phase2_graph(
    llm: OpenAILLMProvider,
    *,
    max_output_chars: int,
    model: str | None = None,
):
    """Linear pipeline: pattern → technology → scalability → tradeoffs → red team."""
    g = StateGraph(Phase2State)
    g.add_node(
        "architecture_pattern",
        make_architecture_pattern_node(llm, max_output_chars=max_output_chars, model=model),
    )
    g.add_node(
        "technology_expert",
        make_technology_node(llm, max_output_chars=max_output_chars, model=model),
    )
    g.add_node(
        "scalability",
        make_scalability_node(llm, max_output_chars=max_output_chars, model=model),
    )
    g.add_node(
        "tradeoffs",
        make_tradeoffs_node(llm, max_output_chars=max_output_chars, model=model),
    )
    g.add_node(
        "red_team",
        make_red_team_node(llm, max_output_chars=max_output_chars, model=model),
    )
    g.add_edge(START, "architecture_pattern")
    g.add_edge("architecture_pattern", "technology_expert")
    g.add_edge("technology_expert", "scalability")
    g.add_edge("scalability", "tradeoffs")
    g.add_edge("tradeoffs", "red_team")
    g.add_edge("red_team", END)
    return g.compile()
