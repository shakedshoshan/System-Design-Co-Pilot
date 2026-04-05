from __future__ import annotations

"""Prompt fragments shared across all Phase 2 agents."""

JSON_REPAIR = (
    "Your previous reply was not valid JSON for the required schema. "
    "Output ONLY a single JSON object with the exact keys specified in the system message. "
    "No markdown, no commentary."
)
