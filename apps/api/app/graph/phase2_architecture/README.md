# Phase 2 — architecture LangGraph package

Sequential “agents” (one LLM structured JSON turn each), wired in `build.py`.

| Folder / file | Role |
|---------------|------|
| `build.py` | Compiles the `StateGraph`: pattern → technology → scalability → tradeoffs → red team. |
| `nodes/` | One module per graph node (`pattern.py`, `technology.py`, …). `llm_node.py` holds shared `call_structured_json_node` + `prd_context_block`. |
| `prompts/` | System prompts per agent; `shared.py` has the JSON repair instruction. |
| `schemas/` | Pydantic output models per agent (must stay aligned with prompts). |
| `parsing/` | `extract.py` — turn raw model text into schema instances (uses Phase 1 `extract_json_object`). |

Public entry: `from app.graph.phase2_architecture import build_phase2_graph`.

Graph state lives in `app/graph/state/phase2.py` (`Phase2State`).

Longer walkthrough (HTTP flow, agent table, diagrams): [`../docs/Phase2_Architecture_LangGraph_Flow.md`](../docs/Phase2_Architecture_LangGraph_Flow.md).
