from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    """Swappable LLM backend (OpenAI today; Azure / other models later)."""

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
    ) -> str:
        """Return assistant plain-text content for a full chat payload (incl. system)."""
        ...
