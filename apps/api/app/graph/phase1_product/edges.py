from __future__ import annotations

"""Phase 1 graph *edges* (how nodes connect).

LangGraph edges are declared in `workflow.py` using `add_edge` / `add_conditional_edges`.
This module holds the branch labels shared by `routing.route_after_guided` and the
`path_map` in `workflow.py`.

Fixed edges (wired in `workflow.py`):
  START → guided_questioning
  prd_synthesis → END

Conditional edge from `guided_questioning` (router: `routing.route_after_guided`):
  prd_synthesis → prd_synthesis node
  done → END
"""

# Keys must match `routing.route_after_guided` return values and `workflow.add_conditional_edges` path_map.
CONDITIONAL_BRANCH_TO_PRD = "prd_synthesis"
CONDITIONAL_BRANCH_DONE = "done"
