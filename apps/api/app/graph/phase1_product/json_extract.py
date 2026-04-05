from __future__ import annotations

"""Helpers to turn messy LLM output into strict Pydantic models.

Models frequently add markdown fences, preamble, or trailing text. We extract the first
JSON object substring before `model_validate_json` runs.
"""

import json
import re

from app.graph.phase1_product.schemas import GuidedQuestioningOutput, PRDDocument


def extract_json_object(raw: str) -> str:
    """Return a JSON object substring from model output (plain or fenced).

    Order: raw JSON → ```json ... ``` → first `{` through last `}` in the string.
    """
    text = raw.strip()
    if text.startswith("{"):
        return text
    fence = re.search(
        r"```(?:json)?\s*(\{[\s\S]*?\})\s*```",
        text,
        re.IGNORECASE,
    )
    if fence:
        return fence.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text


def parse_guided_output(raw: str) -> GuidedQuestioningOutput | None:
    """Parse guided-questioning JSON; None means caller should repair or fall back."""
    try:
        payload = extract_json_object(raw)
        return GuidedQuestioningOutput.model_validate_json(payload)
    except (json.JSONDecodeError, ValueError):
        return None


def parse_prd_document(raw: str) -> PRDDocument | None:
    """Parse PRD synthesis JSON; None triggers repair or structured fallback in the node."""
    try:
        payload = extract_json_object(raw)
        return PRDDocument.model_validate_json(payload)
    except (json.JSONDecodeError, ValueError):
        return None
