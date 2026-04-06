from __future__ import annotations

"""LangGraph node implementations for Phase 1 (product).

Each `make_*` factory closes over the LLM provider and returns an async node callable.
Nodes call the same `OpenAILLMProvider.chat_completion` as the legacy chat path.

Important: models are instructed to emit JSON; we parse with Pydantic and retry once with a
repair prompt. If still invalid, we degrade gracefully (guided → plain text; PRD → fallback doc).
"""

import json
import logging

from app.graph.phase1_product.json_extract import parse_guided_output, parse_prd_document
from app.graph.phase1_product.prompts import (
    GUIDED_JSON_REPAIR,
    GUIDED_QUESTIONING_SYSTEM,
    PRD_JSON_REPAIR,
    PRD_SYNTHESIS_SYSTEM,
)
from app.graph.phase1_product.schemas import PRDDocument
from app.graph.state.phase1 import Phase1State
from app.services.llm.guardrails import sanitize_assistant_output
from app.services.llm.openai_provider import OpenAILLMProvider

logger = logging.getLogger("app.graph.phase1")


def _history_block(history: list[dict[str, str]]) -> str:
    """Flatten DB-backed turns into a single prompt-friendly transcript."""
    lines: list[str] = []
    for m in history:
        role = m.get("role", "")
        content = m.get("content", "")
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


def make_guided_questioning_node(
    llm: OpenAILLMProvider,
    *,
    max_output_chars: int,
    model: str | None = None,
):
    """Guided Questioning agent (plan §5.6): asks gaps, updates draft, may set ready_for_prd."""

    async def guided_questioning(state: Phase1State) -> dict:
        draft = state.get("requirements_draft") or ""
        transcript = _history_block(state.get("message_history") or [])
        user_block = (
            f"Current accumulated requirements draft (may be empty):\n{draft}\n\n"
            f"Conversation (chronological):\n{transcript}\n\n"
            "Respond with ONLY the JSON object described in your instructions."
        )
        api_messages: list[dict[str, str]] = [
            {"role": "system", "content": GUIDED_QUESTIONING_SYSTEM},
            {"role": "user", "content": user_block},
        ]
        raw = await llm.chat_completion(api_messages, model=model)
        parsed = parse_guided_output(raw)
        if parsed is None:
            # One repair turn: models often wrap JSON or truncate; cheaper than failing the HTTP request.
            repair_messages = api_messages + [
                {"role": "assistant", "content": raw[:8000]},
                {"role": "user", "content": GUIDED_JSON_REPAIR},
            ]
            raw2 = await llm.chat_completion(repair_messages, model=model)
            parsed = parse_guided_output(raw2)
        if parsed is None:
            logger.warning("guided_questioning_json_fallback", extra={"session_id": state["session_id"]})
            fallback = sanitize_assistant_output(
                raw,
                max_chars=max_output_chars,
            )
            return {
                "assistant_reply": fallback,
                "requirements_draft": draft,
                "open_questions": state.get("open_questions") or [],
                # Cannot trust routing if we could not parse; stay on Q&A path.
                "ready_for_prd": False,
            }
        msg = sanitize_assistant_output(parsed.assistant_message, max_chars=max_output_chars)
        draft_out = sanitize_assistant_output(
            parsed.updated_requirements_draft,
            max_chars=max_output_chars,
        )
        return {
            "assistant_reply": msg,
            "requirements_draft": draft_out,
            "open_questions": parsed.open_questions[:32],
            "ready_for_prd": bool(parsed.ready_for_prd),
        }

    return guided_questioning


def make_prd_synthesis_node(
    llm: OpenAILLMProvider,
    *,
    max_output_chars: int,
    model: str | None = None,
):
    """PRD synthesis: structured features / user stories / edge cases (plan §9.1) as JSON."""

    async def prd_synthesis(state: Phase1State) -> dict:
        # Uses draft produced by guided node this same turn (merged state).
        draft = state.get("requirements_draft") or ""
        transcript = _history_block(state.get("message_history") or [])
        user_block = (
            f"Requirements draft:\n{draft}\n\n"
            f"Conversation (chronological):\n{transcript}\n\n"
            "Produce the PRD JSON object per your instructions."
        )
        api_messages: list[dict[str, str]] = [
            {"role": "system", "content": PRD_SYNTHESIS_SYSTEM},
            {"role": "user", "content": user_block},
        ]
        raw = await llm.chat_completion(api_messages, model=model)
        doc = parse_prd_document(raw)
        if doc is None:
            repair_messages = api_messages + [
                {"role": "assistant", "content": raw[:8000]},
                {"role": "user", "content": PRD_JSON_REPAIR},
            ]
            raw2 = await llm.chat_completion(repair_messages, model=model)
            doc = parse_prd_document(raw2)
        if doc is None:
            logger.warning("prd_synthesis_json_fallback", extra={"session_id": state["session_id"]})
            body = sanitize_assistant_output(raw, max_chars=max_output_chars)
            # Still persist something versioned so the client can inspect raw model output.
            fallback = PRDDocument(
                title="PRD (unparsed)",
                summary="Model output could not be parsed as structured PRD JSON.",
                features=[],
                user_stories=[],
                edge_cases=[body[:4000]],
            )
            doc = fallback
        prd_json = json.dumps(doc.model_dump(), ensure_ascii=False, indent=2)
        summary = sanitize_assistant_output(doc.summary or doc.title, max_chars=2000)
        assistant = (
            "I've drafted a structured PRD from our discussion.\n\n"
            f"**{doc.title or 'Product requirements'}**\n\n"
            f"{summary}\n\n"
            "The full document is saved as a `prd` artifact for this session."
        )
        assistant = sanitize_assistant_output(assistant, max_chars=max_output_chars)
        return {
            "prd_json": prd_json,
            "assistant_reply": assistant,
        }

    return prd_synthesis
