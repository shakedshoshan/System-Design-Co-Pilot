from __future__ import annotations

from typing import TypedDict


class Phase1State(TypedDict):
    """LangGraph state for one HTTP chat turn in the *product* phase (idea → PRD).

    The runner builds this dict from the database before `ainvoke`. Each node returns
    a *partial* update (only changed keys); LangGraph merges updates into this state.
    We do not use a checkpointer: the next user message re-hydrates from `messages` (+ latest PRD artifact).
    """

    # Correlates logs and LLM context (string form of session UUID).
    session_id: str
    # Last user turn text (redundant with message_history but handy for prompts/debug).
    user_message: str
    # Recent chat turns as OpenAI-style {role, content}; same window as REST chat history.
    message_history: list[dict[str, str]]
    # Consolidated requirements text: seeded from latest `prd` artifact if any, then updated by guided node.
    requirements_draft: str
    # Still-open questions from the guided agent (informational; merged from last node output).
    open_questions: list[str]
    # True when client sent product_action=synthesize_prd — skips "wait until ready" and runs PRD node.
    force_synthesize: bool
    # Set by guided_questioning from model JSON; drives the conditional edge toward prd_synthesis.
    ready_for_prd: bool
    # Final user-visible reply for this turn (guided questions *or* PRD summary after synthesis).
    assistant_reply: str
    # Non-empty only if prd_synthesis ran: canonical JSON string persisted to `artifacts` as type `prd`.
    prd_json: str
