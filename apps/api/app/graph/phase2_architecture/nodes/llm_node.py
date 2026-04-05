from __future__ import annotations

"""Shared helpers: build user context from state and run one structured JSON LLM turn."""

import json
import logging
from collections.abc import Callable
from typing import Any

from app.graph.phase2_architecture.prompts.shared import JSON_REPAIR
from app.graph.state.phase2 import Phase2State
from app.services.llm.guardrails import sanitize_assistant_output
from app.services.llm.openai_provider import OpenAILLMProvider

logger = logging.getLogger("app.graph.phase2")


def prd_context_block(state: Phase2State) -> str:
    """PRD plus optional user notes for this pipeline run."""
    notes = (state.get("user_notes") or "").strip()
    base = f"## PRD (source of truth)\n{state.get('prd_content') or ''}\n"
    if notes:
        return base + f"\n## User notes for this architecture run\n{notes}\n"
    return base


async def call_structured_json_node(
    llm: OpenAILLMProvider,
    *,
    system: str,
    user_body: str,
    model: str | None,
    parse_fn: Callable[[str], Any],
    fallback_factory: Callable[[str], Any],
    max_output_chars: int,
    log_key: str,
    session_id: str,
) -> str:
    """One chat completion, optional repair turn, then canonical JSON string for state."""
    api_messages: list[dict[str, str]] = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_body},
    ]
    raw = await llm.chat_completion(api_messages, model=model)
    parsed = parse_fn(raw)
    if parsed is None:
        repair = api_messages + [
            {"role": "assistant", "content": raw[:8000]},
            {"role": "user", "content": JSON_REPAIR},
        ]
        raw2 = await llm.chat_completion(repair, model=model)
        parsed = parse_fn(raw2)
    if parsed is None:
        logger.warning(log_key, extra={"session_id": session_id})
        parsed = fallback_factory(sanitize_assistant_output(raw, max_chars=max_output_chars))
    return json.dumps(parsed.model_dump(), ensure_ascii=False, indent=2)
