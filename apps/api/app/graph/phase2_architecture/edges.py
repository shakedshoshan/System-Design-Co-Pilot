from __future__ import annotations

"""Phase 2 graph *edges* (linear pipeline).

Node IDs listed here are the single source of truth for `START → … → END` wiring.
`workflow.build_phase2_graph` registers nodes with these exact names, then calls
`wire_phase2_linear_edges`.
"""

from langgraph.graph import END, START, StateGraph

# Order = execution order. Must stay aligned with node registration in `workflow.py`.
PHASE2_NODE_IDS: tuple[str, ...] = (
    "architecture_pattern",
    "technology_expert",
    "scalability",
    "tradeoffs",
    "red_team",
)


def wire_phase2_linear_edges(workflow: StateGraph) -> None:
    """Register fixed edges: START → first → … → last → END."""
    ids = PHASE2_NODE_IDS
    workflow.add_edge(START, ids[0])
    for src, dst in zip(ids, ids[1:]):
        workflow.add_edge(src, dst)
    workflow.add_edge(ids[-1], END)
