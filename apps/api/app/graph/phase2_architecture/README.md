# Phase 2 — architecture LangGraph package

Sequential “agents” (one LLM structured JSON turn each), wired in `workflow.py` / `edges.py`. Phase 1 (product → PRD) lives in the sibling package [`../phase1_product/`](../phase1_product/) with the same **state / nodes / edges / workflow** split (`routing.py` is Phase 1 only).

| Folder / file | Role |
|---------------|------|
| `workflow.py` | Compiles the `StateGraph`: registers nodes, then `wire_phase2_linear_edges`. |
| `edges.py` | `PHASE2_NODE_IDS` order + `wire_phase2_linear_edges` (`START` → … → `END`). |
| `nodes/` | One module per graph node (`pattern.py`, `technology.py`, …). `llm_node.py` holds shared `call_structured_json_node` + `prd_context_block`. |
| `prompts/` | System prompts per agent; `shared.py` has the JSON repair instruction. |
| `schemas/` | Pydantic output models per agent (must stay aligned with prompts). |
| `parsing/` | `extract.py` — turn raw model text into schema instances (uses Phase 1 `extract_json_object`). |

Public entry: `from app.graph.phase2_architecture import build_phase2_graph`.

Graph state lives in `app/graph/state/phase2.py` (`Phase2State`).

Longer walkthrough (HTTP flow, agent table, diagrams): [`../docs/Phase2_Architecture_LangGraph_Flow.md`](../docs/Phase2_Architecture_LangGraph_Flow.md).
