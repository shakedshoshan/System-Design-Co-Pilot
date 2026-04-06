from __future__ import annotations

"""Conditional routing after the guided-questioning node (LangGraph *conditional edges*).

`route_after_guided` is the router function passed to `StateGraph.add_conditional_edges`.
Return values must match the keys in `workflow.build_phase1_graph` path_map and
`edges.CONDITIONAL_BRANCH_*` constants.
"""

from typing import Literal

from app.graph.state.phase1 import Phase1State


def route_after_guided(state: Phase1State) -> Literal["prd_synthesis", "done"]:
    """Next step: PRD synthesis if forced or model is satisfied; otherwise end the turn."""
    if state.get("force_synthesize") or state.get("ready_for_prd"):
        return "prd_synthesis"
    return "done"
