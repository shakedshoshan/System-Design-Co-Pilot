from __future__ import annotations

"""Pydantic contracts for JSON the LLM must emit.

These shapes are embedded in system prompts (`prompts.py`). Keeping them in code ensures
validation and a single source of truth for field names.
"""

from pydantic import BaseModel, Field


class GuidedQuestioningOutput(BaseModel):
    """Structured result from the guided questioning call (one LLM response)."""

    # Shown to the end user in chat.
    assistant_message: str
    # Running consolidated requirements; runner seeds from latest PRD artifact when present.
    updated_requirements_draft: str
    open_questions: list[str] = Field(default_factory=list)
    # When true, the graph routes to PRD synthesis (unless only forced path matters).
    ready_for_prd: bool = False


class PRDDocument(BaseModel):
    """Canonical PRD stored as JSON text in `artifacts.content` (artifact_type=`prd`)."""

    title: str = ""
    summary: str = ""
    features: list[str] = Field(default_factory=list)
    user_stories: list[str] = Field(default_factory=list)
    edge_cases: list[str] = Field(default_factory=list)
